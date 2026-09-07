import os
import time
from typing import Dict, Any
from playwright.sync_api import sync_playwright
from .base_applier import BaseApplier

class LeverApplier(BaseApplier):
    def apply(self, job: Dict[str, Any]) -> bool:
        job_id = job["id"]
        job_url = job["url"]
        
        # Ensure url points to /apply endpoint
        if not job_url.endswith("/apply"):
            apply_url = job_url.rstrip("/") + "/apply"
        else:
            apply_url = job_url

        self.db.update_job_status(job_id, "APPLYING")
        self.db.log_step(job_id, "START", f"Navigating to Lever application: {apply_url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()

            try:
                page.goto(apply_url, wait_until="networkidle", timeout=30000)

                # Fill Standard Personal Fields
                full_name = f"{self.user_profile.get('first_name', '')} {self.user_profile.get('last_name', '')}".strip()
                self._fill_field(page, "input[name='name']", full_name)
                self._fill_field(page, "input[name='email']", self.user_profile.get("email", ""))
                self._fill_field(page, "input[name='phone']", self.user_profile.get("phone", ""))
                self._fill_field(page, "input[name='org']", "Independent Developer")

                # Social Links
                self._fill_field(page, "input[name*='LinkedIn']", self.user_profile.get("linkedin_url", ""))
                self._fill_field(page, "input[name*='GitHub']", self.user_profile.get("github_url", ""))
                self._fill_field(page, "input[name*='Portfolio']", self.user_profile.get("portfolio_url", ""))

                # Attach Resume
                resume_path = self.user_profile.get("resume_path", "data/sample_resume.txt")
                abs_resume_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), resume_path))
                if not os.path.exists(abs_resume_path):
                    abs_resume_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample_resume.txt"))

                file_input = page.query_selector("input[type='file'][name='resume']")
                if file_input:
                    file_input.set_input_files(abs_resume_path)
                    self.db.log_step(job_id, "RESUME_ATTACHED", f"Attached resume from {abs_resume_path}")

                # Additional Custom Questions
                textareas = page.query_selector_all("textarea")
                for area in textareas:
                    try:
                        placeholder = area.get_attribute("placeholder") or "custom question"
                        answer = self.answer_gen.generate_answer(placeholder, job["title"], job["company"], job.get("description", ""))
                        area.fill(answer)
                        self.db.log_step(job_id, "QUESTION_ANSWERED", f"Question: '{placeholder}' -> Answered")
                    except Exception:
                        pass

                # Capture screenshot
                screenshot_path = self.capture_screenshot(page, job_id, "form_filled")
                self.db.log_step(job_id, "FORM_FILLED", "Form fields populated successfully", screenshot_path=screenshot_path)

                if self.mode == "dry_run":
                    self.db.log_step(job_id, "DRY_RUN", "[Dry-Run Mode] Skipped clicking final Submit button.")
                    self.db.update_job_status(job_id, "MATCHED")
                    browser.close()
                    return True

                elif self.mode == "review":
                    self.db.log_step(job_id, "REVIEW", "[Review Mode] Pausing for user manual review & submit in browser.")
                    page.pause()
                    self.db.update_job_status(job_id, "APPLIED")
                    browser.close()
                    return True

                elif self.mode == "autonomous":
                    submit_btn = page.query_selector("#btn-submit, button[type='submit']")
                    if submit_btn:
                        submit_btn.click()
                        page.wait_for_timeout(3000)
                        final_shot = self.capture_screenshot(page, job_id, "submitted")
                        self.db.log_step(job_id, "SUBMITTED", "Application submitted automatically", screenshot_path=final_shot)
                        self.db.update_job_status(job_id, "APPLIED")
                        browser.close()
                        return True
                    else:
                        self.db.log_step(job_id, "ERROR", "Submit button not found", log_level="ERROR")
                        self.db.update_job_status(job_id, "FAILED")
                        browser.close()
                        return False

            except Exception as e:
                err_msg = f"Failed Lever application: {str(e)}"
                self.db.log_step(job_id, "ERROR", err_msg, log_level="ERROR")
                self.db.update_job_status(job_id, "FAILED")
                browser.close()
                return False

    def _fill_field(self, page, selector: str, val: str):
        if not val:
            return
        elem = page.query_selector(selector)
        if elem:
            try:
                elem.fill(val)
            except Exception:
                pass
