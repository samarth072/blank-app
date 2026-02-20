"""Stage 3: AI Scoring — score every job against the candidate profile."""

from __future__ import annotations

from models.schemas import Job, JobStatus, Profile
from utils.ai import score_job
from utils.resume_parser import build_profile_summary


def score_jobs(
    jobs: list[Job],
    profile: Profile,
    min_score: int = 7,
    progress_callback=None,
) -> list[Job]:
    """Score each job against the candidate profile using AI.

    Scoring guide:
    - 9-10: Strong match
    - 7-8: Good match
    - 5-6: Moderate match
    - 1-4: Weak match (skipped)
    """
    profile_summary = build_profile_summary(profile)
    scored = []
    total = len(jobs)

    for i, job in enumerate(jobs):
        if progress_callback:
            progress_callback(f"Scoring {i + 1}/{total}: {job.title} at {job.company}")

        if not job.description:
            job.score = 0
            job.score_rationale = "No description available for scoring"
            job.status = JobStatus.SKIPPED
            scored.append(job)
            continue

        try:
            job_score, rationale = score_job(job.description, profile_summary)
            job.score = job_score
            job.score_rationale = rationale

            if job_score >= min_score:
                job.status = JobStatus.SCORED
            else:
                job.status = JobStatus.SKIPPED

        except Exception as e:
            job.score = 0
            job.score_rationale = f"Scoring error: {e}"
            job.status = JobStatus.SKIPPED

        scored.append(job)

    above = sum(1 for j in scored if (j.score or 0) >= min_score)
    if progress_callback:
        progress_callback(
            f"Scoring complete: {above}/{total} jobs above threshold ({min_score}+)"
        )

    return scored
