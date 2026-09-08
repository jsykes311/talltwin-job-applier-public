import os
import sys
import json
import streamlit as st

# Add src module to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db import Database
from src.cli import run_discover, run_evaluate, load_json
from src.resume_parser import ResumeParser

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CRITERIA_PATH = os.path.join(BASE_DIR, "config", "criteria.json")
PROFILE_PATH = os.path.join(BASE_DIR, "config", "user_profile.json")
PROFILES_DIR = os.path.join(BASE_DIR, "config", "profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)

st.set_page_config(
    page_title="Tall Twin Job Finder",
    page_icon="⚡",
    layout="wide"
)

db = Database()
criteria = load_json(CRITERIA_PATH)
profile = load_json(PROFILE_PATH)

if "light_mode" not in st.session_state:
    st.session_state.light_mode = False
with st.sidebar:
    st.markdown("<div class='brand-mark'>TALL TWIN<span>JOB FINDER</span></div>", unsafe_allow_html=True)
    st.toggle("Light mode", key="light_mode", help="Switch between the midnight command center and the clear light workflow.")

def apply_theme(light_mode: bool):
    if light_mode:
        c = {"bg":"#f7f9fc","surface":"#ffffff","surface2":"#f0f5ff","ink":"#14213d","muted":"#64748b","line":"#dbe4f0","accent":"#1769ff","accent2":"#0f4fc8"}
    else:
        c = {"bg":"#050b1d","surface":"#0b1631","surface2":"#101f42","ink":"#f7f9ff","muted":"#aebbd4","line":"#233761","accent":"#2b7cff","accent2":"#1262e8"}
    st.markdown(f"""<style>
    :root{{--tt-bg:{c['bg']};--tt-surface:{c['surface']};--tt-surface2:{c['surface2']};--tt-ink:{c['ink']};--tt-muted:{c['muted']};--tt-line:{c['line']};--tt-accent:{c['accent']};--tt-accent2:{c['accent2']};}}
    .stApp,[data-testid="stAppViewContainer"]>.main{{background:var(--tt-bg);color:var(--tt-ink)}} [data-testid="stHeader"],[data-testid="stToolbar"]{{background:transparent}} [data-testid="stSidebar"]{{background:var(--tt-surface);border-right:1px solid var(--tt-line)}} [data-testid="stSidebar"] *{{color:var(--tt-ink)}}
    .brand-mark{{margin:.65rem .3rem 1.8rem;font-weight:800;letter-spacing:.14em;font-size:1.15rem;color:var(--tt-ink)}}.brand-mark:before{{content:'◆';color:var(--tt-accent);margin-right:.5rem;font-size:1.4rem}}.brand-mark span{{display:block;margin:.25rem 0 0 1.85rem;letter-spacing:.11em;color:var(--tt-muted);font-size:.58rem;font-weight:700}}
    .block-container{{max-width:1440px;padding-top:3.4rem;padding-bottom:3rem}}h1,h2,h3,p,label,[data-testid="stMetricLabel"],[data-testid="stMetricValue"]{{color:var(--tt-ink)!important}}h1{{font-size:clamp(2.5rem,4.4vw,4.25rem)!important;line-height:1.04!important;letter-spacing:-.055em!important;max-width:850px;margin-bottom:.7rem!important}}h2,h3{{letter-spacing:-.025em!important}}.stCaption,[data-testid="stCaptionContainer"]{{color:var(--tt-muted)!important;font-size:1rem!important}}
    [data-testid="stVerticalBlockBorderWrapper"]{{background:var(--tt-surface)!important;border:1px solid var(--tt-line)!important;border-radius:18px!important;box-shadow:none!important}}[data-testid="stMetric"]{{padding:.8rem 0;border-bottom:1px solid var(--tt-line)}}[data-testid="stMetric"]:last-child{{border-bottom:0}}[data-testid="stMetricValue"]{{font-size:2.15rem!important;letter-spacing:-.055em}}[data-testid="stMetricLabel"]{{color:var(--tt-muted)!important;font-size:.82rem!important;text-transform:uppercase;letter-spacing:.08em}}
    .stButton>button{{border-radius:10px!important;border:1px solid var(--tt-line)!important;background:transparent!important;color:var(--tt-ink)!important;font-weight:650!important;min-height:2.85rem;transition:all .16s ease}}.stButton>button:hover{{border-color:var(--tt-accent)!important;color:var(--tt-accent)!important;transform:translateY(-1px)}}.stButton>button[kind="primary"]{{background:var(--tt-accent)!important;border-color:var(--tt-accent)!important;color:white!important;box-shadow:0 10px 28px rgba(23,105,255,.22)}}.stButton>button[kind="primary"]:hover{{background:var(--tt-accent2)!important;color:white!important}}
    [data-baseweb="input"]>div,[data-baseweb="select"]>div{{background:var(--tt-surface2)!important;border-color:var(--tt-line)!important;color:var(--tt-ink)!important;border-radius:10px!important}}input,textarea{{color:var(--tt-ink)!important}}[data-baseweb="tab-list"]{{gap:1.5rem;border-bottom:1px solid var(--tt-line)}}button[data-baseweb="tab"]{{color:var(--tt-muted)!important;font-weight:700;padding:.7rem .1rem!important}}button[data-baseweb="tab"][aria-selected="true"]{{color:var(--tt-accent)!important;border-bottom-color:var(--tt-accent)!important}}[data-testid="stAlert"]{{background:var(--tt-surface2)!important;border:1px solid var(--tt-line)!important;color:var(--tt-ink)!important;border-radius:12px!important}}[data-testid="stDataFrame"]{{border:1px solid var(--tt-line);border-radius:14px;overflow:hidden}}hr{{border-color:var(--tt-line)!important}}@media(max-width:768px){{.block-container{{padding:1.5rem 1rem 2rem}}h1{{font-size:2.45rem!important}}}}
    </style>""", unsafe_allow_html=True)
apply_theme(st.session_state.light_mode)

# Hero Header
st.markdown("<div class='eyebrow'>WELCOME TO TALL TWIN</div>", unsafe_allow_html=True)
st.title("Find roles worth your time.")
st.caption("Tell Tall Twin what you want, review every match, and only count a submission when the employer confirms it.")

with st.container(border=True):
    step_1, step_2, step_3 = st.columns(3)
    step_1.markdown("### 1. Discover\nTell us what you want.")
    step_2.markdown("### 2. Match\nWe surface the best fits.")
    step_3.markdown("### 3. Confirm\nYou stay in control.")

st.warning(
    "**Demo-mode privacy notice:** this public preview does not yet create private user accounts. "
    "Do not upload a real resume or sensitive contact details here."
)

# Search first. Selection and official-form review happen below.
with st.container(border=True):
    st.subheader("1. Search for verified roles")
    c1, c2 = st.columns([3, 1])
    
    with c1:
        st.markdown("We search and score first. Then you choose **all** or only the roles you want to prepare for review.")
        min_match = st.slider("Minimum match score", min_value=50, max_value=100, value=70)
    with c2:
        run_btn = st.button("Search jobs", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Finding and scoring verified roles..."):
            run_discover(db, criteria)
            run_evaluate(db, criteria, profile)
        st.success("Results are ready below. Pick the roles you want to prepare.")
        st.rerun()

st.divider()

# Sidebar Metrics
st.sidebar.header("Your progress")
stats = db.get_stats()
st.sidebar.metric("Total Discovered", stats.get("TOTAL", 0))
st.sidebar.metric("Ready to review", stats.get("MATCHED", 0) + stats.get("REVIEW_READY", 0))
st.sidebar.metric("Confirmed submissions", stats.get("APPLIED", 0))
st.sidebar.metric("Needs confirmation", stats.get("SUBMISSION_UNCONFIRMED", 0))
st.sidebar.metric("Not a match", stats.get("REJECTED", 0))
st.sidebar.metric("Technical failures", stats.get("FAILED", 0))

st.sidebar.divider()
st.sidebar.header("Next steps")
if st.sidebar.button("1. Find jobs", use_container_width=True):
    with st.spinner("Scraping ATS boards & APIs..."):
        run_discover(db, criteria)
    st.sidebar.success("Discovery completed!")
    st.rerun()

if st.sidebar.button("2. Score my matches", use_container_width=True):
    with st.spinner("Evaluating match scores..."):
        run_evaluate(db, criteria, profile)
    st.sidebar.success("Evaluation completed!")
    st.rerun()

st.sidebar.markdown("### 3. Review applications")
st.sidebar.caption("Open the official form only after you review the role. No slow browser run here.")
st.sidebar.markdown("[Open my review queue](#review-queue)")

# One-page command center: profile, queue, and activity stay visible in one
# continuous workflow instead of hiding review work behind a tab.
st.markdown("<div id='review-queue'></div>", unsafe_allow_html=True)
tab_jobs = st.container()
tab_activity = st.container()
tab_setup = st.container()

with tab_jobs:
    st.subheader("2. Choose roles to prepare")
    st.caption("Select individual roles, or queue every current match. This prepares a review queue—it does not submit applications.")
    matching_jobs = [j for j in db.get_jobs(status="MATCHED", min_score=min_match)]
    selected_job_ids = []
    if matching_jobs:
        for job in matching_jobs:
            selected = st.checkbox(f"{job['title']} · {job['company']} · {job['match_score']:.0f}% match", key=f"choose_job_{job['id']}")
            if selected:
                selected_job_ids.append(job["id"])
        choose_one, choose_all = st.columns(2)
        with choose_one:
            prepare_selected = st.button(f"Prepare selected ({len(selected_job_ids)})", type="primary", use_container_width=True)
        with choose_all:
            prepare_all = st.button(f"Prepare all matches ({len(matching_jobs)})", use_container_width=True)
        chosen_ids = [j["id"] for j in matching_jobs] if prepare_all else selected_job_ids
        if prepare_selected or prepare_all:
            if not chosen_ids:
                st.warning("Choose at least one role first.")
            else:
                for job_id in chosen_ids:
                    db.update_job_status(job_id, "REVIEW_READY")
                    db.log_step(job_id, "REVIEW_QUEUE", "Queued for your review before any submission.")
                st.success(f"{len(chosen_ids)} role(s) moved to your review queue.")
                st.rerun()
    else:
        st.info("Search jobs above to see matching roles here.")

    st.divider()
    st.subheader("3. Review prepared applications")
    st.caption("Open the official form only after you review the role. No slow browser run here.")
    review_jobs = [j for j in db.get_jobs() if j["status"] in ("MATCHED", "REVIEW_READY", "SUBMISSION_UNCONFIRMED")]
    if review_jobs:
        for job in review_jobs[:10]:
            with st.container(border=True):
                queue_main, queue_action = st.columns([5, 1])
                with queue_main:
                    st.markdown(f"**{job['title']}** · {job['company']}  ")
                    st.caption(f"{job['status'].replace('_', ' ').title()} · {job['match_score']:.0f}% match · {job['match_reason'] or 'Review the job details before applying.'}")
                with queue_action:
                    st.link_button("Open role", job["url"], use_container_width=True)
    else:
        st.info("No roles are waiting for your review yet. Find and score jobs above, then they will appear here.")

    st.markdown("#### Browse all roles")
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status Filter", ["ALL", "DISCOVERED", "MATCHED", "REVIEW_READY", "SUBMISSION_UNCONFIRMED", "APPLIED", "REJECTED", "FAILED"])
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

with tab_activity:
    st.subheader("Your application activity")
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

with tab_setup:
    st.subheader("Tell us what you are looking for")
    st.markdown("Complete this once, then move to **Find jobs**. Use sample details in this public preview.")

    with st.form("onboarding_form"):
        st.markdown("#### About you")
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

        st.markdown("#### What kind of job do you want?")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            titles_input = st.text_input("Target Job Titles (comma separated)", value=", ".join(criteria.get("job_titles", [])))
            salary_input = st.number_input("Minimum Salary ($ USD)", value=int(criteria.get("min_salary", 100000)))
            remote_only = st.checkbox("Remote Jobs Only", value=criteria.get("remote_only", True))
        with col_c2:
            locations_input = st.text_input("Target Locations (comma separated)", value=", ".join(criteria.get("locations", [])))
            keywords_inc = st.text_input("Keywords to Include (comma separated)", value=", ".join(criteria.get("keywords_include", [])))
            keywords_exc = st.text_input("Keywords to Exclude (comma separated)", value=", ".join(criteria.get("keywords_exclude", [])))

        st.markdown("#### Resume")
        uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

        submit_setup = st.form_submit_button("Save and find jobs", type="primary", use_container_width=True)

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

            st.success("Saved. Next, open **Find jobs** and click **Find jobs** in the sidebar.")
            st.rerun()
