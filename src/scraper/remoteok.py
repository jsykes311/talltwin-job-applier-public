import requests
from typing import List, Dict, Any
from .base import BaseScraper

class RemoteOKScraper(BaseScraper):
    def fetch_jobs(self) -> List[Dict[str, Any]]:
        target_titles = [t.lower() for t in self.criteria.get("job_titles", [])]
        jobs = []

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            url = "https://remoteok.com/api"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return jobs

            data = resp.json()
            # RemoteOK first element is metadata legal disclaimer
            for item in data[1:] if len(data) > 1 else []:
                if not isinstance(item, dict):
                    continue

                title = item.get("position", "")
                title_lower = title.lower()

                if target_titles and not any(tt in title_lower for tt in target_titles):
                    continue

                job_url = item.get("url", "")
                if not job_url:
                    job_url = f"https://remoteok.com/remote-jobs/{item.get('id', '')}"

                description = item.get("description", "")
                company = item.get("company", "Remote Company")
                location = item.get("location", "Remote")

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": job_url,
                    "platform": "remoteok",
                    "description": description
                })
        except Exception as e:
            print(f"Error scraping RemoteOK: {e}")

        return jobs
