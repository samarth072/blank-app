"""Stage 4: Resume Tailoring — generate a custom resume per job."""

from __future__ import annotations

from models.schemas import Job, JobStatus, Profile
from utils.ai import tailor_resume


def tailor_resumes(
    jobs: list[Job],
    profile: Profile,
    progress_callback=None,
) -> list[Job]:
    """Generate tailored resumes for scored jobs.

    Only processes jobs that passed the scoring threshold.
    Reorganizes and emphasizes relevant experience without fabricating.
    """
    eligible = [j for j in jobs if j.status == JobStatus.SCORED]
    total = len(eligible)

    if progress_callback:
        progress_callback(f"Tailoring resumes for {total} jobs...")

    for i, job in enumerate(eligible):
        if progress_callback:
            progress_callback(f"Tailoring {i + 1}/{total}: {job.title} at {job.company}")

        try:
            tailored = tailor_resume(
                resume_text=profile.resume_text,
                job_description=job.description,
                resume_facts=profile.resume_facts,
            )
            job.tailored_resume = tailored
            job.status = JobStatus.TAILORED

        except Exception as e:
            if progress_callback:
                progress_callback(f"  Warning: Tailoring failed for {job.title}: {e}")

    tailored_count = sum(1 for j in jobs if j.status == JobStatus.TAILORED)
    if progress_callback:
        progress_callback(f"Tailoring complete: {tailored_count} resumes generated")

    return jobs
