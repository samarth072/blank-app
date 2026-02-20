"""Run Pipeline page — execute the 6-stage job application pipeline."""

import streamlit as st

st.set_page_config(page_title="ApplyPilot - Run Pipeline", page_icon="🚀", layout="wide")

from config.settings import is_setup_complete, load_config, load_preferences, load_profile
from models.schemas import JobStatus
from pipeline.apply import prepare_applications
from pipeline.cover_letter import generate_cover_letters
from pipeline.discovery import discover_jobs
from pipeline.enrichment import enrich_jobs
from pipeline.scoring import score_jobs
from pipeline.tailoring import tailor_resumes
from utils.storage import add_jobs, load_jobs, save_jobs

st.title("Run Pipeline")

if not is_setup_complete():
    st.error("Please complete setup first (Profile + API Key)")
    st.stop()

profile = load_profile()
prefs = load_preferences()
config = load_config()

if not prefs or not prefs.job_titles:
    st.warning("No job titles configured. Go to Setup > Search Preferences.")
    st.stop()

st.markdown("---")

# Stage selection
st.subheader("Select Stages to Run")

stages = st.multiselect(
    "Pipeline stages",
    options=[
        "1. Discover",
        "2. Enrich",
        "3. Score",
        "4. Tailor",
        "5. Cover Letters",
        "6. Prepare Applications",
    ],
    default=[
        "1. Discover",
        "2. Enrich",
        "3. Score",
        "4. Tailor",
        "5. Cover Letters",
        "6. Prepare Applications",
    ],
)

col1, col2, col3 = st.columns(3)
with col1:
    min_score = st.slider("Minimum score threshold", 1, 10, config.min_score)
with col2:
    stream_mode = st.checkbox("Stream mode (concurrent stages)", value=config.stream_mode)
with col3:
    dry_run = st.checkbox("Dry run (preview only)", value=config.dry_run)

st.markdown("---")

# Current job stats
jobs = load_jobs()
if jobs:
    st.info(f"Current pipeline: {len(jobs)} jobs in database")

# Run button
if st.button("Run Pipeline", type="primary", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()

    def log(msg: str):
        log_container.text(msg)

    current_jobs = load_jobs()
    total_stages = len(stages)

    # Stage 1: Discover
    if "1. Discover" in stages:
        status_text.markdown("### Stage 1: Discovering Jobs...")
        progress_bar.progress(0)

        new_jobs = discover_jobs(prefs, progress_callback=log)
        if new_jobs:
            added = add_jobs(new_jobs)
            log(f"Added {len(added)} new jobs (from {len(new_jobs)} discovered)")
        else:
            log("No new jobs found. Check your search preferences.")

        current_jobs = load_jobs()
        progress_bar.progress(1 / total_stages)

    # Stage 2: Enrich
    if "2. Enrich" in stages:
        status_text.markdown("### Stage 2: Enriching Job Descriptions...")
        unenriched = [j for j in current_jobs if j.status == JobStatus.DISCOVERED]

        if unenriched:
            enriched = enrich_jobs(unenriched, progress_callback=log)
            # Update in full list
            enriched_map = {j.id: j for j in enriched}
            for i, job in enumerate(current_jobs):
                if job.id in enriched_map:
                    current_jobs[i] = enriched_map[job.id]
            save_jobs(current_jobs)
        else:
            log("No jobs to enrich (all already enriched or no jobs discovered)")

        progress_bar.progress(2 / total_stages)

    # Stage 3: Score
    if "3. Score" in stages:
        status_text.markdown("### Stage 3: Scoring Jobs...")
        unscored = [j for j in current_jobs if j.status == JobStatus.ENRICHED]

        if unscored:
            scored = score_jobs(unscored, profile, min_score=min_score, progress_callback=log)
            scored_map = {j.id: j for j in scored}
            for i, job in enumerate(current_jobs):
                if job.id in scored_map:
                    current_jobs[i] = scored_map[job.id]
            save_jobs(current_jobs)
        else:
            log("No jobs to score")

        progress_bar.progress(3 / total_stages)

    # Stage 4: Tailor
    if "4. Tailor" in stages:
        status_text.markdown("### Stage 4: Tailoring Resumes...")

        if not dry_run:
            current_jobs = tailor_resumes(current_jobs, profile, progress_callback=log)
            save_jobs(current_jobs)
        else:
            log("Dry run — skipping resume tailoring")

        progress_bar.progress(4 / total_stages)

    # Stage 5: Cover Letters
    if "5. Cover Letters" in stages:
        status_text.markdown("### Stage 5: Generating Cover Letters...")

        if not dry_run:
            current_jobs = generate_cover_letters(current_jobs, profile, progress_callback=log)
            save_jobs(current_jobs)
        else:
            log("Dry run — skipping cover letter generation")

        progress_bar.progress(5 / total_stages)

    # Stage 6: Prepare Applications
    if "6. Prepare Applications" in stages:
        status_text.markdown("### Stage 6: Preparing Applications...")
        current_jobs = prepare_applications(current_jobs, progress_callback=log)
        save_jobs(current_jobs)
        progress_bar.progress(1.0)

    status_text.markdown("### Pipeline Complete!")
    progress_bar.progress(1.0)

    # Summary
    from utils.storage import compute_stats

    stats = compute_stats()
    st.markdown("---")
    st.subheader("Pipeline Results")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Discovered", stats.total_discovered)
    c2.metric("Enriched", stats.total_enriched)
    c3.metric("Scored", stats.total_scored)
    c4.metric("Above Threshold", stats.total_above_threshold)
    c5.metric("Ready to Apply", stats.total_tailored)

    st.success("Pipeline run complete! Check the Dashboard for detailed results.")
