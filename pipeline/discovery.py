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
        "remotive": JobSource.REMOTIVE,
        "arbeitnow": JobSource.ARBEITNOW,
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
                    progress_callback=progress_callback,
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
    progress_callback=None,
) -> list[dict]:
    """Search using python-jobspy library."""
    try:
        from jobspy import scrape_jobs
    except ImportError:
        if progress_callback:
            progress_callback("  python-jobspy not installed, trying API fallback...")
        return _search_api_fallback(query, location, remote, max_results, progress_callback)

    # Detect country from location
    country = _detect_country(location)

    all_sites = ["indeed", "linkedin", "google", "zip_recruiter", "glassdoor"]
    all_results = []

    base_kwargs = {
        "search_term": query,
        "results_wanted": max_results,
        "hours_old": 168,
        "country_indeed": country,
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
        if progress_callback:
            progress_callback("  All sites returned 0 results, trying individually...")
    except Exception as e:
        if progress_callback:
            progress_callback(f"  Combined search failed: {e}")

    # If that fails, try each site individually
    for site in all_sites:
        try:
            df = scrape_jobs(site_name=[site], **base_kwargs)
            if not df.empty:
                all_results.extend(df.to_dict("records"))
                if progress_callback:
                    progress_callback(f"  {site}: found {len(df)} jobs")
            else:
                if progress_callback:
                    progress_callback(f"  {site}: 0 results")
        except Exception as e:
            if progress_callback:
                progress_callback(f"  {site} error: {e}")
            continue

    # If scraping failed entirely, try API fallback
    if not all_results:
        if progress_callback:
            progress_callback("  Scraping returned 0 results, trying API fallback...")
        all_results = _search_api_fallback(query, location, remote, max_results, progress_callback)

    return all_results


def _detect_country(location: str) -> str:
    """Detect country from location string for Indeed's country_indeed param."""
    if not location:
        return "USA"
    loc = location.lower().strip()
    country_map = {
        "india": "India",
        "usa": "USA",
        "united states": "USA",
        "uk": "UK",
        "united kingdom": "UK",
        "canada": "Canada",
        "australia": "Australia",
        "germany": "Germany",
        "france": "France",
        "remote": "USA",
    }
    for key, value in country_map.items():
        if key in loc:
            return value
    return "USA"


def _search_api_fallback(
    query: str,
    location: str,
    remote: bool,
    max_results: int,
    progress_callback=None,
) -> list[dict]:
    """Fallback: use free job APIs when scraping is blocked."""
    import requests

    results = []

    # 1. Remotive API (free, no key, remote jobs)
    if remote or (location and "remote" in location.lower()):
        try:
            resp = requests.get(
                "https://remotive.com/api/remote-jobs",
                params={"search": query, "limit": max_results},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                for job in data.get("jobs", [])[:max_results]:
                    results.append({
                        "title": job.get("title", ""),
                        "company_name": job.get("company_name", ""),
                        "location": job.get("candidate_required_location", "Remote"),
                        "job_url": job.get("url", ""),
                        "description": job.get("description", ""),
                        "date_posted": job.get("publication_date", ""),
                        "job_type": job.get("job_type", ""),
                        "salary": job.get("salary", ""),
                        "site": "remotive",
                    })
                if progress_callback:
                    progress_callback(f"  Remotive API: found {len(results)} remote jobs")
        except Exception as e:
            if progress_callback:
                progress_callback(f"  Remotive API error: {e}")

    # 2. Arbeitnow API (free, no key, general + remote jobs)
    try:
        params = {"search": query, "page": 1}
        if remote or (location and "remote" in location.lower()):
            params["remote"] = "true"
        resp = requests.get(
            "https://www.arbeitnow.com/api/job-board-api",
            params=params,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            count = 0
            for job in data.get("data", [])[:max_results]:
                loc_str = job.get("location", "")
                # Filter by location if specified and not remote
                if location and "remote" not in location.lower():
                    if location.lower() not in loc_str.lower():
                        continue
                results.append({
                    "title": job.get("title", ""),
                    "company_name": job.get("company_name", ""),
                    "location": loc_str,
                    "job_url": job.get("url", ""),
                    "description": job.get("description", ""),
                    "date_posted": job.get("created_at", ""),
                    "job_type": ",".join(job.get("tags", [])),
                    "site": "arbeitnow",
                })
                count += 1
            if progress_callback:
                progress_callback(f"  Arbeitnow API: found {count} jobs")
    except Exception as e:
        if progress_callback:
            progress_callback(f"  Arbeitnow API error: {e}")

    return results



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
