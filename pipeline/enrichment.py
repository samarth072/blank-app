"""Stage 2: Job Enrichment — visit job URLs and extract full descriptions."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

from models.schemas import Job, JobStatus
from utils.ai import extract_job_description


def enrich_jobs(jobs: list[Job], progress_callback=None) -> list[Job]:
    """Enrich jobs by fetching and extracting full descriptions.

    Uses a 3-tier extraction cascade:
    1. JSON-LD structured data
    2. CSS selector patterns for common job sites
    3. AI-powered extraction for unknown layouts
    """
    enriched = []
    total = len(jobs)

    for i, job in enumerate(jobs):
        if progress_callback:
            progress_callback(f"Enriching {i + 1}/{total}: {job.title} at {job.company}")

        if job.description and len(job.description) > 200:
            job.status = JobStatus.ENRICHED
            enriched.append(job)
            continue

        if not job.url:
            enriched.append(job)
            continue

        try:
            description = _fetch_and_extract(job.url)
            if description and len(description) > 100:
                job.description = description
                job.status = JobStatus.ENRICHED
            elif job.description:
                job.status = JobStatus.ENRICHED
        except Exception as e:
            if progress_callback:
                progress_callback(f"  Warning: Could not enrich {job.url}: {e}")

        enriched.append(job)

    if progress_callback:
        enriched_count = sum(1 for j in enriched if j.status == JobStatus.ENRICHED)
        progress_callback(f"Enrichment complete: {enriched_count}/{total} jobs enriched")

    return enriched


def _fetch_and_extract(url: str) -> str:
    """Fetch a URL and extract the job description using a 3-tier cascade."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    html = response.text

    # Tier 1: Try JSON-LD structured data
    description = _extract_jsonld(html)
    if description and len(description) > 100:
        return description

    # Tier 2: Try CSS selector patterns for known job sites
    description = _extract_css_selectors(html)
    if description and len(description) > 100:
        return description

    # Tier 3: AI-powered extraction
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = markdownify(str(soup.body)) if soup.body else soup.get_text()
    if len(text) > 200:
        return extract_job_description(text)

    return ""


def _extract_jsonld(html: str) -> str:
    """Extract job description from JSON-LD structured data."""
    import json

    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0]
            if isinstance(data, dict):
                if data.get("@type") == "JobPosting":
                    parts = []
                    if data.get("title"):
                        parts.append(f"# {data['title']}")
                    if data.get("hiringOrganization", {}).get("name"):
                        parts.append(f"**Company:** {data['hiringOrganization']['name']}")
                    if data.get("jobLocation"):
                        loc = data["jobLocation"]
                        if isinstance(loc, dict):
                            address = loc.get("address", {})
                            parts.append(f"**Location:** {address.get('addressLocality', '')} {address.get('addressRegion', '')}")
                    if data.get("description"):
                        desc = data["description"]
                        if "<" in desc:
                            desc = markdownify(desc)
                        parts.append(f"\n{desc}")
                    if parts:
                        return "\n".join(parts)
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    return ""


def _extract_css_selectors(html: str) -> str:
    """Try common CSS selectors for job description content."""
    soup = BeautifulSoup(html, "html.parser")

    selectors = [
        ".job-description",
        ".jobsearch-jobDescriptionText",
        "#job-details",
        ".description__text",
        "[data-testid='job-description']",
        ".job-details",
        ".posting-requirements",
        ".job-posting-content",
        "article.job",
        ".jobs-description__content",
    ]

    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = markdownify(str(element))
            if len(text) > 100:
                return text

    return ""
