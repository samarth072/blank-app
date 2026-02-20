"""Pydantic data models for the ApplyPilot pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobSource(str, Enum):
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    ZIP_RECRUITER = "zip_recruiter"
    GOOGLE = "google"
    WORKDAY = "workday"
    REMOTIVE = "remotive"
    ARBEITNOW = "arbeitnow"
    DIRECT = "direct"


class JobStatus(str, Enum):
    DISCOVERED = "discovered"
    ENRICHED = "enriched"
    SCORED = "scored"
    TAILORED = "tailored"
    COVER_LETTER = "cover_letter"
    READY = "ready"
    APPLIED = "applied"
    FAILED = "failed"
    SKIPPED = "skipped"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    company: str
    location: str = ""
    url: str = ""
    source: JobSource = JobSource.INDEED
    status: JobStatus = JobStatus.DISCOVERED
    description: str = ""
    salary: str = ""
    date_posted: str = ""
    job_type: str = ""
    score: Optional[float] = None
    score_rationale: str = ""
    tailored_resume: str = ""
    cover_letter: str = ""
    application_status: ApplicationStatus = ApplicationStatus.PENDING
    discovered_at: datetime = Field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None
    error_message: str = ""


class WorkExperience(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: str = "Present"
    description: str = ""
    highlights: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: str
    field: str = ""
    graduation_date: str = ""
    gpa: str = ""


class Profile(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    work_authorization: str = "Authorized to work"
    requires_sponsorship: bool = False
    desired_salary_min: int = 0
    desired_salary_max: int = 0
    years_of_experience: int = 0
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    resume_facts: list[str] = Field(default_factory=list)
    resume_text: str = ""


class SearchPreferences(BaseModel):
    job_titles: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_only: bool = False
    min_score: int = 7
    max_results_per_source: int = 25
    exclude_companies: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    include_job_types: list[str] = Field(
        default_factory=lambda: ["fulltime", "contract"]
    )


class PipelineConfig(BaseModel):
    gemini_api_key: str = ""
    llm_model: str = "gemini-2.0-flash"
    workers: int = 2
    min_score: int = 7
    stream_mode: bool = False
    dry_run: bool = False
    headless: bool = True


class PipelineStats(BaseModel):
    total_discovered: int = 0
    total_enriched: int = 0
    total_scored: int = 0
    total_above_threshold: int = 0
    total_tailored: int = 0
    total_cover_letters: int = 0
    total_applied: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    avg_score: float = 0.0
    last_run: Optional[datetime] = None
