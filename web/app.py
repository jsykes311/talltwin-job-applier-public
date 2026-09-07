import os
import sys
import json
import streamlit as st

# Add src module to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db import Database
from src.cli import run_discover, run_evaluate, run_apply, load_json
from src.resume_parser import ResumeParser
from one_touch import execute_one_touch

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CRITERIA_PATH = os.path.join(BASE_DIR, "config", "criteria.json")
PROFILE_PATH = os.path.join(BASE_DIR, "config", "user_profile.json")
PROFILES_DIR = os.path.join(BASE_DIR, "config", "profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)

st.set_page_config(
    page_title="Universal One-Touch Job Applier",
    page_icon="⚡",
    layout="wide"
)

db = Database()
criteria = load_json(CRITERIA_PATH)
profile = load_json(PROFILE_PATH)

# Hero Header
st.title("⚡ Universal One-Touch Job Applier")
st.caption("Customized job application engine for any candidate, job title, salary, or resume.")

# Top One-Touch Action Banner
with st.container(border=True):
    st.subheader("⚡ One-Touch Action Center")
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        st.markdown(f"**Candidate:** `{profile.get('first_name', 'User')} {profile.get('last_name', '')}` (`{profile.get('email', 'No email')}`)")
        one_touch_mode = st.radio(
            "Execution Safety Mode",
            ["dry_run", "review", "autonomous"],
            captions=["Fills forms & takes screenshots (No submit)", "Opens browser & pauses for review", "Fills forms & SUBMITS automatically"],
            horizontal=True
        )
    with c2:
        max_apps = st.number_input("Max Apps per Run", min_value=1, max_value=20, value=5)
    with c3:
        min_match = st.number_input("Min Match Score %", min_value=0, max_value=100, value=70)

    run_btn = st.button("⚡ RUN ONE-TOUCH AUTO-APPLY", type="primary", use_container_width=True)

    if run_btn:
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_progress(msg: str, val: float):
            status_text.info(msg)
            progress_bar.progress(val)

        summary = execute_one_touch(
            mode=one_touch_mode,
            limit=max_apps,
            min_score=min_match,
            progress_callback=update_progress
        )

        st.balloons()
        st.success(f"🎉 One-Touch Run Complete! Processed {summary['applied']} job applications in [{one_touch_mode.upper()}] mode.")
        
        if summary["jobs_applied"]:
            with st.expander("📋 View Applied Jobs Summary", expanded=True):
                for j in summary["jobs_applied"]:
                    st.write(f"• **{j['title']}** @ **{j['company']}** (Match Score: `{j['score']:.1f}%`) — [Application Link]({j['url']})")

        st.rerun()

st.divider()

# Sidebar Metrics
st.sidebar.header("📊 System Stats")
stats = db.get_stats()
st.sidebar.metric("Total Discovered", stats.get("TOTAL", 0))
st.sidebar.metric("Matched Jobs", stats.get("MATCHED", 0))
st.sidebar.metric("Applied Count", stats.get("APPLIED", 0))
st.sidebar.metric("Failed / Rejected", stats.get("FAILED", 0) + stats.get("REJECTED", 0))

st.sidebar.divider()
st.sidebar.header("🔧 Step Controls")
if st.sidebar.button("1. Discover Jobs", use_container_width=True):
    with st.spinner("Scraping ATS boards & APIs..."):
        run_discover(db, criteria)
    st.sidebar.success("Discovery completed!")
    st.rerun()

if st.sidebar.button("2. Evaluate & Score", use_container_width=True):
    with st.spinner("Evaluating match scores..."):
        run_evaluate(db, criteria, profile)
    st.sidebar.success("Evaluation completed!")
    st.rerun()

if st.sidebar.button("3. Run Auto-Applier", use_container_width=True):
    with st.spinner("Running Applier..."):
        run_apply(db, profile, mode=one_touch_mode, limit=max_apps)
    st.sidebar.success("Applier run finished!")
    st.rerun()

# Main Navigation Tabs
tab1, tab2, tab3 = st.tabs(["📋 Job Feed & Matches", "📷 Application Logs & Proof", "👤 User Profile & Resume Setup"])

with tab1:
    st.subheader("Discovered & Matched Jobs")
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status Filter", ["ALL", "DISCOVERED", "MATCHED", "APPLIED", "REJECTED", "FAILED"])
    with col2:
        min_score_filter = st.slider("Filter by Min Match Score", 0, 100, 50)

    selected_status = None if status_filter == "ALL" else status_filter
    jobs = db.get_jobs(status=selected_status, min_score=min_score_filter)

    if not jobs:
        st.info("No jobs found matching the selected filters.")
    else:
        st.dataframe(
            [{
                "ID": j["id"],
                "Title": j["title"],
                "Company": j["company"],
                "Platform": j["platform"],
                "Match Score": f"{j['match_score']:.1f}%",
                "Status": j["status"],
                "Reason": j["match_reason"],
                "URL": j["url"]
            } for j in jobs],
            column_config={
                "URL": st.column_config.LinkColumn("Application Link")
            },
            use_container_width=True
        )

with tab2:
    st.subheader("Application Logs & Proof Screenshots")
    all_jobs = db.get_jobs()
    if not all_jobs:
        st.info("No application history available.")
    else:
        job_options = {f"#{j['id']} - {j['title']} @ {j['company']} ({j['status']})": j['id'] for j in all_jobs}
        selected_job_str = st.selectbox("Select Application Entry", list(job_options.keys()))
        selected_job_id = job_options[selected_job_str]
        
        job_detail = db.get_job_by_id(selected_job_id)
        logs = db.get_logs(selected_job_id)
        
        st.write(f"**Target URL:** [{job_detail['url']}]({job_detail['url']})")
        st.write(f"**Current Status:** `{job_detail['status']}`")
        
        st.markdown("### Step Logs & Screenshots")
        for log in logs:
            st.text(f"[{log['timestamp']}] [{log['step']}] [{log['log_level']}]: {log['message']}")
            if log.get("screenshot_path") and os.path.exists(log["screenshot_path"]):
                st.image(log["screenshot_path"], caption=f"Screenshot Proof: {log['step']}", use_container_width=True)

with tab3:
    st.subheader("👤 Candidate Onboarding & Universal Setup")
    st.markdown("Fill in your candidate details, job criteria, and upload your resume. Any user can set up their profile here!")

    with st.form("onboarding_form"):
        st.markdown("#### 1. Candidate Contact Information")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fn = st.text_input("First Name", value=profile.get("first_name", ""))
            ln = st.text_input("Last Name", value=profile.get("last_name", ""))
            email = st.text_input("Email Address", value=profile.get("email", ""))
            phone = st.text_input("Phone Number", value=profile.get("phone", ""))
        with col_p2:
            loc = st.text_input("Location (City, State/Country)", value=profile.get("location", ""))
            linkedin = st.text_input("LinkedIn Profile URL", value=profile.get("linkedin_url", ""))
            github = st.text_input("GitHub Profile URL", value=profile.get("github_url", ""))
            portfolio = st.text_input("Portfolio / Website URL", value=profile.get("portfolio_url", ""))

        st.markdown("#### 2. Job Search Criteria")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            titles_input = st.text_input("Target Job Titles (comma separated)", value=", ".join(criteria.get("job_titles", [])))
            salary_input = st.number_input("Minimum Salary ($ USD)", value=int(criteria.get("min_salary", 100000)))
            remote_only = st.checkbox("Remote Jobs Only", value=criteria.get("remote_only", True))
        with col_c2:
            locations_input = st.text_input("Target Locations (comma separated)", value=", ".join(criteria.get("locations", [])))
            keywords_inc = st.text_input("Keywords to Include (comma separated)", value=", ".join(criteria.get("keywords_include", [])))
            keywords_exc = st.text_input("Keywords to Exclude (comma separated)", value=", ".join(criteria.get("keywords_exclude", [])))

        st.markdown("#### 3. Resume Upload")
        uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

        submit_setup = st.form_submit_button("💾 Save Profile & Update Criteria", type="primary", use_container_width=True)

        if submit_setup:
            # Handle uploaded resume file
            resume_path = profile.get("resume_path", "data/resume.pdf")
            if uploaded_file is not None:
                save_dir = os.path.join(BASE_DIR, "data")
                os.makedirs(save_dir, exist_ok=True)
                ext = uploaded_file.name.split(".")[-1]
                saved_resume_filename = f"resume.{ext}"
                full_save_path = os.path.join(save_dir, saved_resume_filename)
                
                with open(full_save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                resume_path = f"data/{saved_resume_filename}"
                
                # Extract summary text from uploaded PDF
                if ext == "pdf":
                    extracted_text = ResumeParser.extract_text_from_pdf(full_save_path)
                    parsed_res = ResumeParser.parse_resume_summary(extracted_text)
                    profile["summary"] = parsed_res["summary"]
                    st.info(f"📄 Resume text successfully extracted! ({parsed_res['line_count']} lines)")

            # Save Profile JSON
            updated_profile = {
                **profile,
                "first_name": fn,
                "last_name": ln,
                "email": email,
                "phone": phone,
                "location": loc,
                "linkedin_url": linkedin,
                "github_url": github,
                "portfolio_url": portfolio,
                "resume_path": resume_path
            }

            # Save Criteria JSON
            updated_criteria = {
                **criteria,
                "job_titles": [t.strip() for t in titles_input.split(",") if t.strip()],
                "locations": [l.strip() for l in locations_input.split(",") if l.strip()],
                "remote_only": remote_only,
                "min_salary": salary_input,
                "keywords_include": [k.strip() for k in keywords_inc.split(",") if k.strip()],
                "keywords_exclude": [k.strip() for k in keywords_exc.split(",") if k.strip()]
            }

            with open(PROFILE_PATH, "w") as f:
                json.dump(updated_profile, f, indent=2)
            with open(CRITERIA_PATH, "w") as f:
                json.dump(updated_criteria, f, indent=2)

            st.success("✅ Profile, Criteria, and Resume successfully saved and updated!")
            st.rerun()

    st.divider()
    with st.expander("🔧 Raw JSON Configuration Editors"):
        raw_c1, raw_c2 = st.columns(2)
        with raw_c1:
            st.json(criteria)
        with raw_c2:
            st.json(profile)
