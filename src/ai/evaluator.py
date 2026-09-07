import os
import re
import json
from typing import Dict, Any, Tuple

class JobEvaluator:
    def __init__(self, criteria: Dict[str, Any], user_profile: Dict[str, Any]):
        self.criteria = criteria
        self.user_profile = user_profile
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def evaluate_job(self, job_title: str, job_description: str) -> Tuple[float, str]:
        """Evaluates job posting match score (0-100) and reason.
        Uses Gemini API if API key is present, otherwise uses intelligent heuristic scoring.
        """
        if self.api_key:
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                
                prompt = f"""
                Analyze this job posting against candidate criteria and profile.
                
                Candidate Profile Summary:
                {self.user_profile.get('summary', '')}
                
                Candidate Target Titles: {', '.join(self.criteria.get('job_titles', []))}
                Include Keywords: {', '.join(self.criteria.get('keywords_include', []))}
                Exclude Keywords: {', '.join(self.criteria.get('keywords_exclude', []))}
                
                Job Title: {job_title}
                Job Description:
                {job_description[:2000]}
                
                Respond strictly in JSON format with:
                {{
                  "score": <number 0 to 100>,
                  "reason": "<short 1-2 sentence explanation>"
                }}
                """
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                res_data = json.loads(response.text)
                return float(res_data.get("score", 50.0)), res_data.get("reason", "AI match evaluation complete.")
            except Exception as e:
                print(f"Gemini API evaluation fallback to heuristic: {e}")

        # Heuristic scoring fallback
        return self._heuristic_evaluate(job_title, job_description)

    def _heuristic_evaluate(self, job_title: str, job_description: str) -> Tuple[float, str]:
        score = 50.0
        reasons = []

        title_lower = job_title.lower()
        desc_lower = job_description.lower()

        # Check exclude keywords
        for exc in self.criteria.get("keywords_exclude", []):
            if exc.lower() in title_lower or exc.lower() in desc_lower:
                return 10.0, f"Contains excluded keyword '{exc}'"

        # Match title
        target_titles = [t.lower() for t in self.criteria.get("job_titles", [])]
        matched_title = any(tt in title_lower for tt in target_titles)
        if matched_title:
            score += 25.0
            reasons.append("Job title matches target criteria.")
        else:
            reasons.append("Job title is a partial match.")

        # Match include keywords
        include_keywords = [k.lower() for k in self.criteria.get("keywords_include", [])]
        found_keywords = [k for k in include_keywords if k in desc_lower or k in title_lower]
        if include_keywords:
            kw_ratio = len(found_keywords) / len(include_keywords)
            score += kw_ratio * 25.0
            reasons.append(f"Matched keywords: {', '.join(found_keywords)}")

        final_score = min(100.0, max(0.0, score))
        return final_score, " | ".join(reasons)
