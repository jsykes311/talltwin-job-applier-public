import requests
from typing import List, Dict, Any
from .base import BaseScraper

DEFAULT_GREENHOUSE_BOARDS = [
    "cloudflare", "datadog", "discord", "figma", "github", 
    "gitlab", "hashicorp", "stripe", "airtable", "roblox"
]

class GreenhouseScraper(BaseScraper):
    def __init__(self, criteria: Dict[str, Any], boards: List[str] = None):
        super().__init__(criteria)
        self.boards = boards or DEFAULT_GREENHOUSE_BOARDS

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        target_titles = [t.lower() for t in self.criteria.get("job_titles", [])]
        remote_only = self.criteria.get("remote_only", False)
        jobs = []

        for board in self.boards:
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
                resp = requests.get(url, timeout=10)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                for job_item in data.get("jobs", []):
                    title = job_item.get("title", "")
                    title_lower = title.lower()

                    # Match job titles if criteria specified
                    if target_titles and not any(tt in title_lower for tt in target_titles):
                        continue

                    location_name = job_item.get("location", {}).get("name", "Unknown")
                    if remote_only and "remote" not in location_name.lower() and "remote" not in title_lower:
                        continue

                    job_url = job_item.get("absolute_url", "")
                    content = job_item.get("content", "")
                    
                    jobs.append({
                        "title": title,
                        "company": board.capitalize(),
                        "location": location_name,
                        "url": job_url,
                        "platform": "greenhouse",
                        "description": content
                    })
            except Exception as e:
                print(f"Error scraping Greenhouse board {board}: {e}")
                continue

        return jobs
