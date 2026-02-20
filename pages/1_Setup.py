"""Setup page — configure profile, preferences, and API keys."""

import streamlit as st

st.set_page_config(page_title="ApplyPilot - Setup", page_icon="🚀", layout="wide")

from config.settings import (
    load_config,
    load_preferences,
    load_profile,
    save_config,
    save_preferences,
    save_profile,
)
from models.schemas import (
    Education,
    PipelineConfig,
    Profile,
    SearchPreferences,
    WorkExperience,
)
from utils.resume_parser import extract_text_from_pdf

st.title("Setup")
st.caption("One-time configuration: profile, preferences, and API keys")

tab1, tab2, tab3 = st.tabs(["Profile", "Search Preferences", "API Keys & Config"])

# ── Profile Tab ──────────────────────────────────────────────
with tab1:
    st.subheader("Your Profile")
    st.caption("This powers scoring, tailoring, and auto-fill")

    profile = load_profile() or Profile()

    # Resume upload
    st.markdown("#### Resume Upload")
    uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    if uploaded:
        pdf_bytes = uploaded.read()
        resume_text = extract_text_from_pdf(pdf_bytes)
        if resume_text and not resume_text.startswith("Error"):
            profile.resume_text = resume_text
            st.success(f"Resume parsed: {len(resume_text)} characters extracted")
            with st.expander("Preview extracted text"):
                st.text(resume_text[:2000])
        else:
            st.error(resume_text)

    st.markdown("#### Contact Information")
    col1, col2 = st.columns(2)
    with col1:
        profile.full_name = st.text_input("Full Name", value=profile.full_name)
        profile.email = st.text_input("Email", value=profile.email)
        profile.phone = st.text_input("Phone", value=profile.phone)
        profile.location = st.text_input("Location", value=profile.location)
    with col2:
        profile.linkedin_url = st.text_input("LinkedIn URL", value=profile.linkedin_url)
        profile.github_url = st.text_input("GitHub URL", value=profile.github_url)
        profile.portfolio_url = st.text_input("Portfolio URL", value=profile.portfolio_url)

    st.markdown("#### Work Authorization")
    col1, col2 = st.columns(2)
    with col1:
        profile.work_authorization = st.selectbox(
            "Work Authorization",
            ["Authorized to work", "US Citizen", "Green Card", "H1B", "OPT/CPT", "Other"],
            index=["Authorized to work", "US Citizen", "Green Card", "H1B", "OPT/CPT", "Other"].index(
                profile.work_authorization
            )
            if profile.work_authorization
            in ["Authorized to work", "US Citizen", "Green Card", "H1B", "OPT/CPT", "Other"]
            else 0,
        )
    with col2:
        profile.requires_sponsorship = st.checkbox(
            "Requires visa sponsorship", value=profile.requires_sponsorship
        )

    st.markdown("#### Professional Summary")
    profile.summary = st.text_area(
        "Summary",
        value=profile.summary,
        height=100,
        placeholder="Brief professional summary highlighting your key strengths...",
    )

    profile.years_of_experience = st.number_input(
        "Years of Experience", min_value=0, max_value=50, value=profile.years_of_experience
    )

    st.markdown("#### Skills")
    skills_text = st.text_area(
        "Skills (one per line)",
        value="\n".join(profile.skills),
        height=100,
        placeholder="Python\nMachine Learning\nAWS\n...",
    )
    profile.skills = [s.strip() for s in skills_text.split("\n") if s.strip()]

    st.markdown("#### Compensation Preferences")
    col1, col2 = st.columns(2)
    with col1:
        profile.desired_salary_min = st.number_input(
            "Minimum Salary ($)", min_value=0, value=profile.desired_salary_min, step=5000
        )
    with col2:
        profile.desired_salary_max = st.number_input(
            "Maximum Salary ($)", min_value=0, value=profile.desired_salary_max, step=5000
        )

    # Work Experience
    st.markdown("#### Work Experience")
    num_experiences = st.number_input(
        "Number of positions", min_value=0, max_value=20,
        value=max(len(profile.work_experience), 1),
    )

    experiences = []
    for i in range(int(num_experiences)):
        with st.expander(f"Position {i + 1}", expanded=i < len(profile.work_experience)):
            existing = profile.work_experience[i] if i < len(profile.work_experience) else WorkExperience(company="", title="", start_date="")
            col1, col2 = st.columns(2)
            with col1:
                company = st.text_input(f"Company #{i+1}", value=existing.company, key=f"exp_company_{i}")
                title = st.text_input(f"Title #{i+1}", value=existing.title, key=f"exp_title_{i}")
            with col2:
                start = st.text_input(f"Start Date #{i+1}", value=existing.start_date, key=f"exp_start_{i}")
                end = st.text_input(f"End Date #{i+1}", value=existing.end_date, key=f"exp_end_{i}")
            desc = st.text_area(f"Description #{i+1}", value=existing.description, key=f"exp_desc_{i}", height=80)
            highlights_text = st.text_area(
                f"Key Highlights #{i+1} (one per line)",
                value="\n".join(existing.highlights),
                key=f"exp_highlights_{i}",
                height=60,
            )
            highlights = [h.strip() for h in highlights_text.split("\n") if h.strip()]

            if company and title:
                experiences.append(
                    WorkExperience(
                        company=company, title=title, start_date=start,
                        end_date=end, description=desc, highlights=highlights,
                    )
                )
    profile.work_experience = experiences

    # Education
    st.markdown("#### Education")
    num_edu = st.number_input(
        "Number of degrees", min_value=0, max_value=10,
        value=max(len(profile.education), 1),
    )

    educations = []
    for i in range(int(num_edu)):
        with st.expander(f"Degree {i + 1}", expanded=i < len(profile.education)):
            existing = profile.education[i] if i < len(profile.education) else Education(institution="", degree="")
            col1, col2 = st.columns(2)
            with col1:
                inst = st.text_input(f"Institution #{i+1}", value=existing.institution, key=f"edu_inst_{i}")
                degree = st.text_input(f"Degree #{i+1}", value=existing.degree, key=f"edu_degree_{i}")
            with col2:
                field = st.text_input(f"Field #{i+1}", value=existing.field, key=f"edu_field_{i}")
                grad_date = st.text_input(f"Graduation Date #{i+1}", value=existing.graduation_date, key=f"edu_grad_{i}")

            if inst and degree:
                educations.append(
                    Education(institution=inst, degree=degree, field=field, graduation_date=grad_date)
                )
    profile.education = educations

    # Resume Facts
    st.markdown("#### Resume Facts")
    st.caption("Key facts that must be preserved exactly during tailoring (companies, projects, metrics)")
    facts_text = st.text_area(
        "Resume Facts (one per line)",
        value="\n".join(profile.resume_facts),
        height=100,
        placeholder="Led team of 8 engineers at Acme Corp\nIncreased revenue by 40%\n...",
    )
    profile.resume_facts = [f.strip() for f in facts_text.split("\n") if f.strip()]

    if st.button("Save Profile", type="primary"):
        save_profile(profile)
        st.success("Profile saved!")

# ── Search Preferences Tab ────────────────────────────────────
with tab2:
    st.subheader("Search Preferences")
    st.caption("Configure what jobs to search for")

    prefs = load_preferences() or SearchPreferences()

    st.markdown("#### Job Titles to Search")
    titles_text = st.text_area(
        "Job titles (one per line)",
        value="\n".join(prefs.job_titles),
        height=100,
        placeholder="Software Engineer\nSenior Developer\nFull Stack Engineer\n...",
    )
    prefs.job_titles = [t.strip() for t in titles_text.split("\n") if t.strip()]

    st.markdown("#### Locations")
    locations_text = st.text_area(
        "Locations (one per line, leave empty for all)",
        value="\n".join(prefs.locations),
        height=80,
        placeholder="San Francisco, CA\nNew York, NY\nRemote\n...",
    )
    prefs.locations = [l.strip() for l in locations_text.split("\n") if l.strip()]

    col1, col2 = st.columns(2)
    with col1:
        prefs.remote_only = st.checkbox("Remote jobs only", value=prefs.remote_only)
        prefs.min_score = st.slider("Minimum match score", 1, 10, prefs.min_score)
    with col2:
        prefs.max_results_per_source = st.number_input(
            "Max results per search", min_value=5, max_value=100,
            value=prefs.max_results_per_source,
        )

    st.markdown("#### Job Types")
    all_types = ["fulltime", "parttime", "contract", "internship"]
    prefs.include_job_types = st.multiselect(
        "Include job types",
        options=all_types,
        default=prefs.include_job_types or ["fulltime", "contract"],
    )

    st.markdown("#### Excluded Companies")
    exclude_text = st.text_area(
        "Companies to exclude (one per line)",
        value="\n".join(prefs.exclude_companies),
        height=60,
    )
    prefs.exclude_companies = [c.strip() for c in exclude_text.split("\n") if c.strip()]

    st.markdown("#### Excluded Keywords")
    st.caption("Jobs with these keywords in the title will be skipped (case-insensitive)")
    exclude_kw_text = st.text_area(
        "Keywords to exclude (one per line)",
        value="\n".join(prefs.exclude_keywords),
        height=60,
        placeholder="accounting\naccountant\nbookkeeping\ntax\naudit\n...",
    )
    prefs.exclude_keywords = [k.strip() for k in exclude_kw_text.split("\n") if k.strip()]

    if st.button("Save Preferences", type="primary"):
        save_preferences(prefs)
        st.success("Preferences saved!")

# ── API Keys Tab ──────────────────────────────────────────────
with tab3:
    st.subheader("API Keys & Configuration")

    config = load_config()

    config.gemini_api_key = st.text_input(
        "Gemini API Key",
        value=config.gemini_api_key,
        type="password",
        help="Free API key from https://aistudio.google.com/apikey",
    )

    config.llm_model = st.selectbox(
        "LLM Model",
        ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-pro"],
        index=["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-pro"].index(config.llm_model)
        if config.llm_model in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-pro"]
        else 0,
    )

    st.markdown("#### Pipeline Settings")
    col1, col2 = st.columns(2)
    with col1:
        config.workers = st.number_input("Workers (parallel tasks)", min_value=1, max_value=8, value=config.workers)
        config.min_score = st.slider("Default minimum score", 1, 10, config.min_score, key="config_min_score")
    with col2:
        config.dry_run = st.checkbox("Dry run mode (no actual submissions)", value=config.dry_run)
        config.headless = st.checkbox("Headless browser mode", value=config.headless)

    if st.button("Save Configuration", type="primary"):
        save_config(config)
        st.success("Configuration saved!")
