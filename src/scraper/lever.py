import requests
from typing import List, Dict, Any
from .base import BaseScraper

DEFAULT_LEVER_COMPANIES = [
    "palantir", "netflix", "spotify", "scaleapi", "replit", 
    "vercel", "linear", "notion", "brex", "ramp"
]

class LeverScraper(BaseScraper):
    def __init__(self, criteria: Dict[str, Any], companies: List[str] = None):
        super().__init__(criteria)
        self.companies = companies or DEFAULT_LEVER_COMPANIES

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        target_titles = [t.lower() for t in self.criteria.get("job_titles", [])]
        remote_only = self.criteria.get("remote_only", False)
        jobs = []

        for company in self.companies:
            try:
                url = f"https://api.lever.co/v0/postings/{company}?mode=json"
                resp = requests.get(url, timeout=10)
                if resp.status_code != 200:
                    continue

                postings = resp.json()
                for item in postings:
                    title = item.get("text", "")
                    title_lower = title.lower()

                    if target_titles and not any(tt in title_lower for tt in target_titles):
                        continue

                    categories = item.get("categories", {})
                    location = categories.get("location", "Unknown")
                    workplace_type = categories.get("workplaceType", "")

                    if remote_only and ("remote" not in location.lower() and "remote" not in workplace_type.lower() and "remote" not in title_lower):
                        continue

                    job_url = item.get("hostedUrl", "")
                    description = item.get("descriptionPlain", "")

                    jobs.append({
                        "title": title,
                        "company": company.capitalize(),
                        "location": location,
                        "url": job_url,
                        "platform": "lever",
                        "description": description
                    })
            except Exception as e:
                print(f"Error scraping Lever company {company}: {e}")
                continue

        return jobs
