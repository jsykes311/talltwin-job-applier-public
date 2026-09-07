import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..db import Database
from ..ai.answer_generator import AnswerGenerator

class BaseApplier(ABC):
    def __init__(self, user_profile: Dict[str, Any], db: Database, mode: str = "dry_run", headless: bool = True):
        """
        mode options:
        - 'dry_run': Auto-fills form fields, uploads resume, takes screenshot, but DOES NOT submit.
        - 'review': Auto-fills form fields, pauses for human review in browser.
        - 'autonomous': Auto-fills form fields and clicks submit.
        """
        self.user_profile = user_profile
        self.db = db
        self.mode = mode
        self.headless = headless if mode != "review" else False
        self.answer_gen = AnswerGenerator(user_profile)
        self.screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    @abstractmethod
    def apply(self, job: Dict[str, Any]) -> bool:
        """Executes the auto-fill and submission workflow for a given job.
        Returns True if successful, False otherwise.
        """
        pass

    def capture_screenshot(self, page, job_id: int, step_name: str) -> str:
        filename = f"job_{job_id}_{step_name}_{int(time.time())}.png"
        path = os.path.join(self.screenshot_dir, filename)
        try:
            page.screenshot(path=path, full_page=True)
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
        return path

    def submission_confirmed(self, page) -> bool:
        """Return True only when the application site visibly confirms receipt."""
        try:
            page_text = page.locator("body").inner_text(timeout=5000).lower()
        except Exception:
            return False
        confirmations = (
            "application submitted", "application received", "thanks for applying",
            "thank you for applying", "thank you for your application",
            "we received your application",
        )
        return any(message in page_text for message in confirmations)
