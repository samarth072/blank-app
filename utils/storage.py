"""Data persistence utilities for jobs and pipeline state."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from models.schemas import Job, JobStatus, PipelineStats

DATA_DIR = Path(__file__).parent.parent / "data"
JOBS_PATH = DATA_DIR / "jobs.json"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_jobs(jobs: list[Job]) -> None:
    ensure_data_dir()
    data = [job.model_dump() for job in jobs]
    with open(JOBS_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_jobs() -> list[Job]:
    if not JOBS_PATH.exists():
        return []
    with open(JOBS_PATH) as f:
        data = json.load(f)
    return [Job(**item) for item in data]


def add_jobs(new_jobs: list[Job]) -> list[Job]:
    """Add jobs, deduplicating by URL."""
    existing = load_jobs()
    existing_urls = {j.url for j in existing if j.url}
    added = []
    for job in new_jobs:
        if job.url and job.url not in existing_urls:
            existing.append(job)
            existing_urls.add(job.url)
            added.append(job)
        elif not job.url:
            existing.append(job)
            added.append(job)
    save_jobs(existing)
    return added


def update_job(job_id: str, **kwargs) -> Job | None:
    jobs = load_jobs()
    for i, job in enumerate(jobs):
        if job.id == job_id:
            for key, value in kwargs.items():
                setattr(jobs[i], key, value)
            save_jobs(jobs)
            return jobs[i]
    return None


def get_jobs_by_status(status: JobStatus) -> list[Job]:
    return [j for j in load_jobs() if j.status == status]


def mark_job_applied(job_id: str) -> None:
    update_job(
        job_id,
        status=JobStatus.APPLIED,
        applied_at=datetime.now(),
    )


def mark_job_failed(job_id: str, error: str = "") -> None:
    update_job(
        job_id,
        status=JobStatus.FAILED,
        error_message=error,
    )


def reset_failed_jobs() -> int:
    jobs = load_jobs()
    count = 0
    for job in jobs:
        if job.status == JobStatus.FAILED:
            job.status = JobStatus.READY
            job.error_message = ""
            count += 1
    save_jobs(jobs)
    return count


def compute_stats() -> PipelineStats:
    jobs = load_jobs()
    scored_jobs = [j for j in jobs if j.score is not None]
    above_threshold = [j for j in scored_jobs if (j.score or 0) >= 7]
    avg = sum(j.score for j in scored_jobs if j.score) / len(scored_jobs) if scored_jobs else 0.0

    return PipelineStats(
        total_discovered=len(jobs),
        total_enriched=len([j for j in jobs if j.status.value in (
            "enriched", "scored", "tailored", "cover_letter", "ready", "applied"
        )]),
        total_scored=len(scored_jobs),
        total_above_threshold=len(above_threshold),
        total_tailored=len([j for j in jobs if j.tailored_resume]),
        total_cover_letters=len([j for j in jobs if j.cover_letter]),
        total_applied=len([j for j in jobs if j.status == JobStatus.APPLIED]),
        total_failed=len([j for j in jobs if j.status == JobStatus.FAILED]),
        total_skipped=len([j for j in jobs if j.status == JobStatus.SKIPPED]),
        avg_score=round(avg, 1),
        last_run=datetime.now(),
    )
