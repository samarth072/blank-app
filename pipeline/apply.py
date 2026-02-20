"""Stage 6: Auto-Apply — autonomous browser-driven job application submission.

This stage generates application instructions and manages application state.
In a full deployment with Claude Code CLI and Playwright, this would
autonomously navigate forms, fill fields, upload documents, and submit.

In the Streamlit web version, it provides:
- Application preparation (generates instruction files)
- One-click links to apply manually
- Status tracking for all applications
"""

from __future__ import annotations

from datetime import datetime

from models.schemas import ApplicationStatus, Job, JobStatus


def prepare_applications(jobs: list[Job], progress_callback=None) -> list[Job]:
    """Prepare jobs for application submission.

    Marks jobs with cover letters as ready to apply.
    """
    eligible = [j for j in jobs if j.status == JobStatus.COVER_LETTER]
    total = len(eligible)

    if progress_callback:
        progress_callback(f"Preparing {total} applications...")

    for job in eligible:
        job.status = JobStatus.READY
        job.application_status = ApplicationStatus.PENDING

    if progress_callback:
        progress_callback(f"{total} applications ready")

    return jobs


def generate_apply_prompt(job: Job) -> str:
    """Generate an instruction prompt for applying to a specific job.

    This can be used with Claude Code CLI for autonomous application,
    or as a guide for manual application.
    """
    prompt = f"""Apply to this job:

JOB DETAILS:
- Title: {job.title}
- Company: {job.company}
- URL: {job.url}
- Location: {job.location}

INSTRUCTIONS:
1. Navigate to {job.url}
2. Look for an "Apply" or "Submit Application" button
3. Fill in personal information from the profile
4. Upload the tailored resume (provided below)
5. Paste the cover letter if there's a field for it
6. Answer any screening questions based on the profile
7. Review all fields before submitting
8. Submit the application

TAILORED RESUME:
{job.tailored_resume}

COVER LETTER:
{job.cover_letter}
"""
    return prompt


def mark_applied(job: Job) -> Job:
    """Mark a job as successfully applied."""
    job.status = JobStatus.APPLIED
    job.application_status = ApplicationStatus.SUBMITTED
    job.applied_at = datetime.now()
    return job


def mark_failed(job: Job, error: str = "") -> Job:
    """Mark a job application as failed."""
    job.status = JobStatus.FAILED
    job.application_status = ApplicationStatus.FAILED
    job.error_message = error
    return job
