from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseScraper(ABC):
    def __init__(self, criteria: Dict[str, Any]):
        self.criteria = criteria

    @abstractmethod
    def fetch_jobs(self) -> List[Dict[str, Any]]:
        """Fetches job postings according to criteria.
        Returns a list of dicts with: title, company, location, url, platform, description.
        """
        pass
