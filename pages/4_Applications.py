"""Applications page — track and manage job applications."""

import streamlit as st

st.set_page_config(page_title="ApplyPilot - Applications", page_icon="🚀", layout="wide")

from models.schemas import JobStatus
from pipeline.apply import generate_apply_prompt, mark_applied, mark_failed
from utils.storage import load_jobs, reset_failed_jobs, save_jobs

st.title("Applications")

jobs = load_jobs()
if not jobs:
    st.info("No jobs in the pipeline yet. Run the pipeline first!")
    st.stop()

# ── Application Summary ──────────────────────────────────────
ready = [j for j in jobs if j.status == JobStatus.READY]
applied = [j for j in jobs if j.status == JobStatus.APPLIED]
failed = [j for j in jobs if j.status == JobStatus.FAILED]

c1, c2, c3 = st.columns(3)
c1.metric("Ready to Apply", len(ready))
c2.metric("Applied", len(applied))
c3.metric("Failed", len(failed))

st.markdown("---")

# ── Ready to Apply ────────────────────────────────────────────
st.subheader("Ready to Apply")
st.caption("Jobs with tailored resumes and cover letters, ready for submission")

if ready:
    for job in ready:
        with st.expander(f"[{job.score}/10] {job.title} — {job.company}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Title:** {job.title}")
                st.markdown(f"**Company:** {job.company}")
                st.markdown(f"**Location:** {job.location}")
                if job.salary:
                    st.markdown(f"**Salary:** {job.salary}")
                if job.url:
                    st.link_button("Open Job Posting", job.url)

            with col2:
                st.markdown(f"**Score:** {job.score}/10")
                st.markdown(f"**Source:** {job.source.value}")

            # Tailored materials
            tab1, tab2, tab3 = st.tabs(["Tailored Resume", "Cover Letter", "Apply Instructions"])

            with tab1:
                if job.tailored_resume:
                    st.markdown(job.tailored_resume)
                    st.download_button(
                        "Download Resume",
                        data=job.tailored_resume,
                        file_name=f"resume_{job.company.lower().replace(' ', '_')}_{job.id}.md",
                        mime="text/markdown",
                        key=f"dl_resume_{job.id}",
                    )
                else:
                    st.warning("No tailored resume generated")

            with tab2:
                if job.cover_letter:
                    st.markdown(job.cover_letter)
                    st.download_button(
                        "Download Cover Letter",
                        data=job.cover_letter,
                        file_name=f"cover_letter_{job.company.lower().replace(' ', '_')}_{job.id}.md",
                        mime="text/markdown",
                        key=f"dl_cover_{job.id}",
                    )
                else:
                    st.warning("No cover letter generated")

            with tab3:
                prompt = generate_apply_prompt(job)
                st.code(prompt, language="text")
                st.download_button(
                    "Download Apply Prompt",
                    data=prompt,
                    file_name=f"apply_prompt_{job.company.lower().replace(' ', '_')}_{job.id}.txt",
                    mime="text/plain",
                    key=f"dl_prompt_{job.id}",
                )

            # Action buttons
            st.markdown("---")
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                if st.button("Mark as Applied", key=f"apply_{job.id}", type="primary"):
                    mark_applied(job)
                    save_jobs(jobs)
                    st.success(f"Marked {job.title} at {job.company} as applied!")
                    st.rerun()
            with bcol2:
                if st.button("Mark as Failed", key=f"fail_{job.id}"):
                    error = st.text_input("Error reason (optional)", key=f"error_{job.id}")
                    mark_failed(job, error)
                    save_jobs(jobs)
                    st.warning(f"Marked {job.title} at {job.company} as failed")
                    st.rerun()
else:
    st.info("No applications ready. Run the full pipeline to prepare applications.")

st.markdown("---")

# ── Applied Jobs ──────────────────────────────────────────────
st.subheader("Applied")

if applied:
    for job in applied:
        with st.expander(f"[{job.score}/10] {job.title} — {job.company}"):
            st.markdown(f"**Applied at:** {job.applied_at}")
            st.markdown(f"**Location:** {job.location}")
            if job.url:
                st.link_button("View Job Posting", job.url)
else:
    st.info("No applications submitted yet.")

st.markdown("---")

# ── Failed Applications ──────────────────────────────────────
st.subheader("Failed")

if failed:
    for job in failed:
        with st.expander(f"[{job.score}/10] {job.title} — {job.company}"):
            st.markdown(f"**Error:** {job.error_message or 'No error message'}")
            if job.url:
                st.link_button("View Job Posting", job.url)

    if st.button("Reset All Failed Jobs", type="secondary"):
        count = reset_failed_jobs()
        st.success(f"Reset {count} failed jobs back to ready status")
        st.rerun()
else:
    st.info("No failed applications.")

st.markdown("---")

# ── Bulk Actions ──────────────────────────────────────────────
st.subheader("Utilities")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Mark by URL")
    mark_url = st.text_input("Job URL")
    mark_action = st.selectbox("Action", ["Mark Applied", "Mark Failed"])

    if st.button("Execute") and mark_url:
        target = next((j for j in jobs if j.url == mark_url), None)
        if target:
            if mark_action == "Mark Applied":
                mark_applied(target)
                save_jobs(jobs)
                st.success(f"Marked as applied: {target.title}")
            else:
                mark_failed(target)
                save_jobs(jobs)
                st.warning(f"Marked as failed: {target.title}")
        else:
            st.error("Job not found with that URL")

with col2:
    st.markdown("#### Export Data")
    import json
    export_data = json.dumps(
        [j.model_dump() for j in jobs],
        indent=2,
        default=str,
    )
    st.download_button(
        "Export All Jobs (JSON)",
        data=export_data,
        file_name="applypilot_jobs.json",
        mime="application/json",
    )

    # Export applied only
    if applied:
        applied_data = json.dumps(
            [j.model_dump() for j in applied],
            indent=2,
            default=str,
        )
        st.download_button(
            "Export Applied Jobs (JSON)",
            data=applied_data,
            file_name="applypilot_applied.json",
            mime="application/json",
        )
