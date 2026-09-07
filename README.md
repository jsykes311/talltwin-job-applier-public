# 🌐 Public Universal Autonomous Job Applier (`auto-job-applier-public`)

A multi-user, multi-candidate autonomous job application web app designed for public deployment and sharing.

---

## 🌟 Key Features of the Public Version

1. **Multi-User Profile Setup:** Any external user can onboard by entering their contact details, target roles, salary expectations, and uploading their resume PDF.
2. **Dynamic Resume Ingestion:** Automated PDF text parser (`ResumeParser`) extracts candidate skills and summary instantly.
3. **One-Touch Auto-Apply Engine:** Single-click execution of discovery, AI evaluation, and Playwright form submissions.
4. **Isolated Candidate Profiles:** Supports switching between different candidate profiles and databases.

---

## 🛠️ How to Deploy & Share

### Local Run:
```bash
cd /Users/jeremysykes/.gemini/antigravity/scratch/auto-job-applier-public
./venv/bin/streamlit run web/app.py
```

### Public Web Hosting Options:
- **Streamlit Community Cloud:** Free 1-click cloud hosting directly from GitHub repository.
- **Docker Container:** Package into a standard Docker container for deployment on AWS, Render, or Railway.

---

## 📁 Project Structure

```
/Users/jeremysykes/.gemini/antigravity/scratch/auto-job-applier-public/
├── config/
│   ├── criteria.json           # Job search filters
│   └── user_profile.json       # Current active user profile
├── data/
│   ├── resume.pdf              # Uploaded user resume
│   └── applications.db         # Database tracking jobs & logs
├── src/
│   ├── db.py                   # SQLite database manager
│   ├── resume_parser.py        # PDF resume text extraction
│   ├── scraper/                # Greenhouse, Lever, RemoteOK scrapers
│   ├── ai/                     # Gemini AI match evaluator & prompt answerer
│   └── automator/              # Playwright browser form submission engine
├── web/
│   └── app.py                  # Multi-user Streamlit web application
├── one_touch.py                # One-touch CLI runner
├── requirements.txt            # System dependencies
└── README.md                   # Public documentation
```
