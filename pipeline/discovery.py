"""Stage 1: Job Discovery — search multiple job boards and aggregate results."""

from __future__ import annotations

from models.schemas import Job, JobSource, SearchPreferences


def discover_jobs(preferences: SearchPreferences, progress_callback=None) -> list[Job]:
    """Discover jobs from multiple sources based on search preferences.

    Uses python-jobspy to query Indeed, LinkedIn, Glassdoor, ZipRecruiter, and Google Jobs.
    Deduplicates results by URL.
    """
    all_jobs: list[Job] = []
    seen_urls: set[str] = set()

    source_map = {
        "indeed": JobSource.INDEED,
        "linkedin": JobSource.LINKEDIN,
        "glassdoor": JobSource.GLASSDOOR,
        "zip_recruiter": JobSource.ZIP_RECRUITER,
        "google": JobSource.GOOGLE,
    }

    for title_query in preferences.job_titles:
        for location in preferences.locations or [""]:
            if progress_callback:
                progress_callback(f"Searching: '{title_query}' in {location or 'all locations'}...")

            try:
                jobs = _search_jobspy(
                    query=title_query,
                    location=location,
                    remote=preferences.remote_only,
                    max_results=preferences.max_results_per_source,
                    job_types=preferences.include_job_types,
                )

                for raw_job in jobs:
                    url = raw_job.get("job_url", "")
                    if url and url in seen_urls:
                        continue
                    if url:
                        seen_urls.add(url)

                    company = raw_job.get("company_name", raw_job.get("company", "Unknown"))
                    if company in preferences.exclude_companies:
                        continue

                    job_title = raw_job.get("title", "").lower()
                    if any(kw.lower() in job_title for kw in preferences.exclude_keywords):
                        continue

                    source_str = raw_job.get("site", "indeed")
                    source = source_map.get(source_str, JobSource.INDEED)

                    job = Job(
                        title=raw_job.get("title", "Unknown Title"),
                        company=company,
                        location=raw_job.get("location", location),
                        url=url,
                        source=source,
                        description=raw_job.get("description", ""),
                        salary=_format_salary(raw_job),
                        date_posted=str(raw_job.get("date_posted", "")),
                        job_type=raw_job.get("job_type", ""),
                    )
                    all_jobs.append(job)

            except Exception as e:
                if progress_callback:
                    progress_callback(f"Warning: Search error for '{title_query}': {e}")

    if progress_callback:
        progress_callback(f"Discovery complete: {len(all_jobs)} jobs found")

    return all_jobs


def _search_jobspy(
    query: str,
    location: str,
    remote: bool,
    max_results: int,
    job_types: list[str],
) -> list[dict]:
    """Search using python-jobspy library."""
    from jobspy import scrape_jobs

    # Try sites individually so one failure doesn't kill the whole search
    all_sites = ["indeed", "linkedin", "google", "zip_recruiter", "glassdoor"]
    all_results = []

    base_kwargs = {
        "search_term": query,
        "results_wanted": max_results,
        "hours_old": 168,  # 7 days for more results
        "country_indeed": "USA",
    }

    if location:
        base_kwargs["location"] = location

    if remote:
        base_kwargs["is_remote"] = True

    if job_types:
        type_map = {
            "fulltime": "fulltime",
            "parttime": "parttime",
            "contract": "contract",
            "internship": "internship",
        }
        mapped = [type_map[t] for t in job_types if t in type_map]
        if mapped:
            base_kwargs["job_type"] = mapped[0]

    # Try all sites together first
    try:
        df = scrape_jobs(site_name=all_sites, **base_kwargs)
        if not df.empty:
            return df.to_dict("records")
    except Exception:
        pass

    # If that fails, try each site individually
    for site in all_sites:
        try:
            df = scrape_jobs(site_name=[site], **base_kwargs)
            if not df.empty:
                all_results.extend(df.to_dict("records"))
        except Exception:
            continue

    return all_results



def _format_salary(raw_job: dict) -> str:
    """Format salary information from raw job data."""
    min_sal = raw_job.get("min_amount") or raw_job.get("salary_min")
    max_sal = raw_job.get("max_amount") or raw_job.get("salary_max")
    interval = raw_job.get("interval") or raw_job.get("salary_interval", "yearly")

    if min_sal and max_sal:
        return f"${int(min_sal):,} - ${int(max_sal):,} / {interval}"
    elif min_sal:
        return f"${int(min_sal):,}+ / {interval}"
    elif max_sal:
        return f"Up to ${int(max_sal):,} / {interval}"
    return ""
