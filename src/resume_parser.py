import os
import re
from typing import Dict, Any

class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extracts text content from a PDF file."""
        text = ""
        try:
            import pypdf
            reader = pypdf.PdfReader(pdf_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"pypdf extraction notice: {e}")
            # Basic fallback text read if text file passed
            try:
                with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception:
                pass
        return text.strip()

    @staticmethod
    def parse_resume_summary(text: str) -> Dict[str, Any]:
        """Parses key skills and summary from resume text."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        summary = text[:1000] if text else "Experienced Candidate"
        return {
            "full_text": text,
            "summary": summary,
            "line_count": len(lines)
        }
