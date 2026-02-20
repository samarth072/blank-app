"""Stage 5: Cover Letter Generation — write targeted cover letters."""

from __future__ import annotations

from models.schemas import Job, JobStatus, Profile
from utils.ai import generate_cover_letter
from utils.resume_parser import build_profile_summary


def generate_cover_letters(
    jobs: list[Job],
    profile: Profile,
    progress_callback=None,
) -> list[Job]:
    """Generate targeted cover letters for tailored jobs.

    Each cover letter references the specific company, role, and
    maps the candidate's experience to the job requirements.
    """
    eligible = [j for j in jobs if j.status == JobStatus.TAILORED]
    total = len(eligible)
    profile_summary = build_profile_summary(profile)

    if progress_callback:
        progress_callback(f"Generating cover letters for {total} jobs...")

    for i, job in enumerate(eligible):
        if progress_callback:
            progress_callback(f"Writing cover letter {i + 1}/{total}: {job.title} at {job.company}")

        try:
            letter = generate_cover_letter(
                profile_summary=profile_summary,
                job_title=job.title,
                company=job.company,
                job_description=job.description,
            )
            job.cover_letter = letter
            job.status = JobStatus.COVER_LETTER

        except Exception as e:
            if progress_callback:
                progress_callback(f"  Warning: Cover letter failed for {job.title}: {e}")

    letters_count = sum(1 for j in jobs if j.status == JobStatus.COVER_LETTER)
    if progress_callback:
        progress_callback(f"Cover letters complete: {letters_count} generated")

    return jobs
