import os
import json
from typing import Dict, Any

class AnswerGenerator:
    def __init__(self, user_profile: Dict[str, Any]):
        self.user_profile = user_profile
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def generate_answer(self, question: str, job_title: str, company: str, job_description: str = "") -> str:
        """Generates candidate response to application questions.
        Uses Gemini API if key is available, or user template/heuristics fallback.
        """
        q_lower = question.lower()

        # Check direct template mappings
        templates = self.user_profile.get("answers_templates", {})
        if ("why" in q_lower and ("us" in q_lower or "company" in q_lower or "role" in q_lower)) and templates.get("why_us"):
            return templates["why_us"]
        if "years" in q_lower and "experience" in q_lower and templates.get("years_experience"):
            return templates["years_experience"]
        if "salary" in q_lower or "compensation" in q_lower:
            return self.user_profile.get("desired_salary", "$120,000")

        # Try Gemini API if key exists
        if self.api_key:
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)

                prompt = f"""
                You are assisting {self.user_profile.get('first_name', 'Candidate')} {self.user_profile.get('last_name', '')} in filling out a job application.
                
                Candidate Summary:
                {self.user_profile.get('summary', '')}
                
                Company Name: {company}
                Job Title: {job_title}
                Application Question: "{question}"
                
                Provide a concise, professional answer (1-3 sentences) directly answering the question as the applicant.
                """
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                print(f"Gemini API answer generation fallback: {e}")

        # Basic fallback answers based on question intent
        if "sponsorship" in q_lower or "visa" in q_lower:
            return self.user_profile.get("requires_sponsorship", "No")
        if "authorized" in q_lower or "work in" in q_lower:
            return self.user_profile.get("work_authorization", "Yes")
        if "notice" in q_lower or "start date" in q_lower or "availability" in q_lower:
            return templates.get("notice_period", "2 weeks")
        if "relocat" in q_lower:
            return templates.get("relocation", "Open to discuss")
        if any(topic in q_lower for topic in ("gender", "race", "ethnicity", "disability", "veteran", "criminal", "conviction", "ssn", "social security")):
            return ""

        # Generic summary fallback
        return ""
