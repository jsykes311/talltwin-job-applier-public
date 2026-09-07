import os
import time
from typing import Dict, Any
from playwright.sync_api import sync_playwright
from .base_applier import BaseApplier

class GreenhouseApplier(BaseApplier):
    def apply(self, job: Dict[str, Any]) -> bool:
        job_id = job["id"]
        job_url = job["url"]
        self.db.update_job_status(job_id, "APPLYING")
        self.db.log_step(job_id, "START", f"Navigating to Greenhouse application: {job_url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()

            try:
                page.goto(job_url, wait_until="networkidle", timeout=30000)
                
                # Check for direct apply form or 'Apply Now' button
                apply_button = page.query_selector("a[href*='#app'], a[href*='apply'], #apply_button")
                if apply_button:
                    try:
                        apply_button.click()
                        page.wait_for_timeout(1000)
                    except Exception:
                        pass

                # Fill Standard Personal Fields
                self._fill_field(page, "first_name", self.user_profile.get("first_name", ""))
                self._fill_field(page, "last_name", self.user_profile.get("last_name", ""))
                self._fill_field(page, "email", self.user_profile.get("email", ""))
                self._fill_field(page, "phone", self.user_profile.get("phone", ""))
                
                # Social Links
                self._fill_field(page, "linkedin", self.user_profile.get("linkedin_url", ""))
                self._fill_field(page, "github", self.user_profile.get("github_url", ""))
                self._fill_field(page, "website", self.user_profile.get("portfolio_url", ""))

                # Attach Resume
                resume_path = self.user_profile.get("resume_path", "data/sample_resume.txt")
                abs_resume_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), resume_path))
                if not os.path.exists(abs_resume_path):
                    # Fallback to sample text file if pdf not supplied
                    abs_resume_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample_resume.txt"))

                file_input = page.query_selector("input[type='file']")
                if file_input:
                    file_input.set_input_files(abs_resume_path)
                    self.db.log_step(job_id, "RESUME_ATTACHED", f"Attached resume from {abs_resume_path}")

                # Custom Text Areas / Questions
                textareas = page.query_selector_all("textarea")
                for area in textareas:
                    try:
                        label_elem = page.query_selector(f"label[for='{area.get_attribute('id')}']")
                        label_text = label_elem.inner_text() if label_elem else "custom question"
                        answer = self.answer_gen.generate_answer(label_text, job["title"], job["company"], job.get("description", ""))
                        if answer:
                            area.fill(answer)
                            self.db.log_step(job_id, "QUESTION_ANSWERED", f"Question: '{label_text}' -> Answered")
                        else:
                            self.db.log_step(job_id, "MANUAL_REVIEW_REQUIRED", f"Question: '{label_text}' needs your answer.", log_level="WARNING")
                    except Exception as e:
                        pass

                # Take screenshot prior to submission decision
                screenshot_path = self.capture_screenshot(page, job_id, "form_filled")
                self.db.log_step(job_id, "FORM_FILLED", "Form fields populated successfully", screenshot_path=screenshot_path)

                if self.mode == "dry_run":
                    self.db.log_step(job_id, "DRY_RUN", "[Dry-Run Mode] Skipped clicking final Submit button.")
                    self.db.update_job_status(job_id, "MATCHED") # reset or keep matched
                    browser.close()
                    return True

                elif self.mode == "review":
                    self.db.log_step(job_id, "REVIEW_READY", "[Review Mode] Form prepared; submission requires your confirmation.")
                    self.db.update_job_status(job_id, "REVIEW_READY")
                    browser.close()
                    return True

                elif self.mode == "autonomous":
                    submit_btn = page.query_selector("#submit_app, input[type='submit'], button[type='submit']")
                    if submit_btn:
                        submit_btn.click()
                        page.wait_for_timeout(3000)
                        final_shot = self.capture_screenshot(page, job_id, "submission_result")
                        if self.submission_confirmed(page):
                            self.db.log_step(job_id, "SUBMITTED", "Application receipt confirmation detected.", screenshot_path=final_shot)
                            self.db.update_job_status(job_id, "APPLIED")
                        else:
                            self.db.log_step(job_id, "SUBMISSION_UNCONFIRMED", "Submit was clicked, but no receipt confirmation was detected.", log_level="WARNING", screenshot_path=final_shot)
                            self.db.update_job_status(job_id, "SUBMISSION_UNCONFIRMED")
                        browser.close()
                        return True
                    else:
                        self.db.log_step(job_id, "ERROR", "Submit button not found", log_level="ERROR")
                        self.db.update_job_status(job_id, "FAILED")
                        browser.close()
                        return False

            except Exception as e:
                err_msg = f"Failed Greenhouse application: {str(e)}"
                self.db.log_step(job_id, "ERROR", err_msg, log_level="ERROR")
                self.db.update_job_status(job_id, "FAILED")
                browser.close()
                return False

    def _fill_field(self, page, field_keyword: str, val: str):
        if not val:
            return
        selectors = [
            f"input[name*='{field_keyword}']",
            f"input[id*='{field_keyword}']",
            f"input[autocomplete*='{field_keyword}']"
        ]
        for sel in selectors:
            elem = page.query_selector(sel)
            if elem:
                try:
                    elem.fill(val)
                    break
                except Exception:
                    pass
