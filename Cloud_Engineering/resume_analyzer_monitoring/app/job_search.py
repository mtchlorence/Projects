from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote_plus

import requests

from analyzer import SKILLS


PH_SEARCH_TERMS = ["philippines", "philippine", "manila", "ph"]
PH_LOCATION_KEYWORDS = {
    "philippines",
    "philippine",
    "manila",
    "makati",
    "taguig",
    "quezon city",
    "cebu",
    "davao",
    "ph",
}


def _get_env_int(name: str, fallback: int) -> int:
    try:
        return int(os.getenv(name, fallback))
    except (TypeError, ValueError):
        return fallback


def _get_job_search_api_url() -> str:
    api_url = os.getenv("JOB_SEARCH_API_URL")
    if not api_url:
        raise ValueError("JOB_SEARCH_API_URL is not configured")
    return api_url


def _get_lookback_days() -> int:
    return _get_env_int("JOB_SEARCH_LOOKBACK_DAYS", 30)


def _get_timeout_seconds() -> int:
    return _get_env_int("JOB_SEARCH_TIMEOUT_SECONDS", 8)


def _get_result_limit() -> int:
    return _get_env_int("JOB_SEARCH_RESULT_LIMIT", 12)


def _is_ph_friendly(*values: str) -> bool:
    text = " ".join(value for value in values if value).lower()
    return any(keyword in text for keyword in PH_LOCATION_KEYWORDS)


def _parse_posted_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed = datetime.strptime(value[:10], "%Y-%m-%d")
        except ValueError:
            return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _extract_skills_from_text(text: str) -> List[str]:
    lowered = text.lower()
    return sorted({skill for skill in SKILLS if skill in lowered})


def _normalize_remoteok_job(raw_job: Dict) -> Dict:
    tags = raw_job.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]

    description = " ".join(
        str(raw_job.get(field, ""))
        for field in ("position", "company", "description")
    )
    description = f"{description} {' '.join(str(tag) for tag in tags)}"

    posted_at = raw_job.get("date") or raw_job.get("created_at")
    posted_date = _parse_posted_date(posted_at)

    location = raw_job.get("location") or "Remote"
    is_ph_friendly = _is_ph_friendly(
        raw_job.get("position", ""),
        raw_job.get("company", ""),
        location,
        description,
    )

    return {
        "title": raw_job.get("position") or "Untitled role",
        "company": raw_job.get("company") or "Unknown company",
        "location": location,
        "url": raw_job.get("url") or raw_job.get("apply_url") or raw_job.get("source_url"),
        "posted_at": posted_at,
        "posted_date": posted_date,
        "skills": _extract_skills_from_text(description),
        "source": "Remote OK",
        "is_ph_friendly": is_ph_friendly,
        "region_label": "PH / Remote" if is_ph_friendly else "Remote",
    }


def _dedupe_jobs(jobs: Iterable[Dict]) -> List[Dict]:
    seen = set()
    unique_jobs = []

    for job in jobs:
        key = (
            str(job.get("title", "")).lower(),
            str(job.get("company", "")).lower(),
            str(job.get("url", "")).lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_jobs.append(job)

    return unique_jobs


def filter_and_rank_jobs(
    jobs: Iterable[Dict],
    resume_skills: Iterable[str],
    lookback_days: Optional[int] = None,
    limit: Optional[int] = None,
    now: Optional[datetime] = None,
) -> List[Dict]:
    now = now or datetime.now(timezone.utc)
    lookback_days = lookback_days if lookback_days is not None else _get_lookback_days()
    limit = limit if limit is not None else _get_result_limit()
    cutoff = now - timedelta(days=lookback_days)
    resume_skill_set = {skill.lower() for skill in resume_skills}
    ranked_jobs = []

    for job in jobs:
        posted_date = job.get("posted_date")
        if isinstance(posted_date, str):
            posted_date = _parse_posted_date(posted_date)

        if not posted_date or posted_date < cutoff:
            continue

        job_skills = {skill.lower() for skill in job.get("skills", [])}
        matched_skills = sorted(resume_skill_set.intersection(job_skills))
        if not matched_skills:
            continue

        ranked_jobs.append(
            {
                **job,
                "posted_date": posted_date,
                "posted_at": posted_date.strftime("%Y-%m-%d"),
                "matched_skills": matched_skills,
            }
        )

    ranked_jobs.sort(
        key=lambda item: (
            item.get("is_ph_friendly", False),
            len(item["matched_skills"]),
            item["posted_date"],
        ),
        reverse=True,
    )
    return ranked_jobs[:limit]


def fetch_remoteok_jobs(skills: Iterable[str], timeout: Optional[int] = None) -> List[Dict]:
    query_terms = list(dict.fromkeys([*list(skills)[:4], *PH_SEARCH_TERMS])) or ["python"]
    timeout = timeout if timeout is not None else _get_timeout_seconds()
    api_url = _get_job_search_api_url()
    jobs = []
    headers = {
        "User-Agent": "resume-analyzer-monitoring/1.0 (+https://github.com/)",
        "Accept": "application/json",
    }

    for skill in query_terms:
        response = requests.get(
            api_url.format(query=quote_plus(skill)),
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, list):
            continue

        for raw_job in payload:
            if isinstance(raw_job, dict) and raw_job.get("position"):
                jobs.append(_normalize_remoteok_job(raw_job))

    return _dedupe_jobs(jobs)


def find_matching_jobs(
    resume_skills: Iterable[str],
    lookback_days: Optional[int] = None,
    limit: Optional[int] = None,
) -> Dict:
    if os.getenv("JOB_SEARCH_ENABLED", "true").lower() in {"0", "false", "no"}:
        return {
            "jobs": [],
            "error": "Job search is disabled. Set JOB_SEARCH_ENABLED=true to enable live job matching.",
        }

    resume_skills = list(resume_skills)
    if not resume_skills:
        return {"jobs": [], "error": None}

    try:
        jobs = fetch_remoteok_jobs(resume_skills)
        return {
            "jobs": filter_and_rank_jobs(
                jobs,
                resume_skills,
                lookback_days=lookback_days,
                limit=limit,
            ),
            "error": None,
        }
    except Exception as exc:
        return {
            "jobs": [],
            "error": f"Live job search is unavailable right now: {exc}",
        }
