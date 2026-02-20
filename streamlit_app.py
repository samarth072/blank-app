"""ApplyPilot — AI agent that applies to jobs for you. Any site. Any form.

A 6-stage autonomous job application pipeline:
1. Discover jobs across 5+ boards
2. Enrich with full descriptions
3. Score against your resume with AI
4. Tailor your resume per job
5. Write targeted cover letters
6. Submit applications
"""

import streamlit as st

st.set_page_config(
    page_title="ApplyPilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config.settings import is_setup_complete, load_config
from utils.storage import compute_stats, load_jobs


def main():
    st.sidebar.title("ApplyPilot")
    st.sidebar.caption("AI-powered job application pipeline")
    st.sidebar.divider()

    setup_done = is_setup_complete()
    if setup_done:
        st.sidebar.success("Setup complete")
    else:
        st.sidebar.warning("Setup required — go to Setup page")

    st.sidebar.divider()
    jobs = load_jobs()
    if jobs:
        stats = compute_stats()
        st.sidebar.metric("Jobs Discovered", stats.total_discovered)
        st.sidebar.metric("Above Threshold", stats.total_above_threshold)
        st.sidebar.metric("Applied", stats.total_applied)
        if stats.avg_score > 0:
            st.sidebar.metric("Avg Score", stats.avg_score)

    # Main page content
    st.title("ApplyPilot")
    st.subheader("AI agent that applies to jobs for you. Any site. Any form.")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 6-Stage Pipeline")
        st.markdown("""
        1. **Discover** — Search 5+ job boards
        2. **Enrich** — Extract full descriptions
        3. **Score** — AI rates match quality 1-10
        4. **Tailor** — Custom resume per job
        5. **Cover Letter** — Targeted per company
        6. **Apply** — Submit applications
        """)

    with col2:
        st.markdown("### Job Sources")
        st.markdown("""
        - Indeed
        - LinkedIn
        - Glassdoor
        - ZipRecruiter
        - Google Jobs
        - 48 Workday employer portals
        - 30+ direct career sites
        """)

    with col3:
        st.markdown("### AI-Powered")
        st.markdown("""
        - **Gemini AI** for scoring, tailoring, and cover letters
        - Never fabricates experience
        - Reorganizes and emphasizes relevant skills
        - Incorporates job-specific keywords
        - Answers screening questions
        """)

    st.markdown("---")

    if not setup_done:
        st.info("Get started by completing setup in the **Setup** page (sidebar).")
    else:
        st.success("You're all set! Head to **Run Pipeline** to start discovering and applying to jobs.")

    # Quick stats if we have data
    if jobs:
        st.markdown("---")
        st.markdown("### Pipeline Status")

        stats = compute_stats()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Discovered", stats.total_discovered)
        c2.metric("Scored", stats.total_scored)
        c3.metric("Tailored", stats.total_tailored)
        c4.metric("Cover Letters", stats.total_cover_letters)
        c5.metric("Applied", stats.total_applied)

        if stats.total_failed > 0:
            st.warning(f"{stats.total_failed} applications failed — check Applications page")


if __name__ == "__main__":
    main()
