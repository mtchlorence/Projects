from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote_plus

import requests

from analyzer import SKILLS


REMOTEOK_API_URL = "https://remoteok.com/remote-{query}-jobs.json"
DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_TIMEOUT_SECONDS = 8
DEFAULT_LIMIT = 12


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

    return {
        "title": raw_job.get("position") or "Untitled role",
        "company": raw_job.get("company") or "Unknown company",
        "location": raw_job.get("location") or "Remote",
        "url": raw_job.get("url") or raw_job.get("apply_url") or raw_job.get("source_url"),
        "posted_at": posted_at,
        "posted_date": posted_date,
        "skills": _extract_skills_from_text(description),
        "source": "Remote OK",
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
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    limit: int = DEFAULT_LIMIT,
    now: Optional[datetime] = None,
) -> List[Dict]:
    now = now or datetime.now(timezone.utc)
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

        match_score = round((len(matched_skills) / max(len(resume_skill_set), 1)) * 100, 2)
        ranked_jobs.append(
            {
                **job,
                "posted_date": posted_date,
                "posted_at": posted_date.strftime("%Y-%m-%d"),
                "matched_skills": matched_skills,
                "match_score": match_score,
            }
        )

    ranked_jobs.sort(
        key=lambda item: (
            item["match_score"],
            len(item["matched_skills"]),
            item["posted_date"],
        ),
        reverse=True,
    )
    return ranked_jobs[:limit]


def fetch_remoteok_jobs(skills: Iterable[str], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> List[Dict]:
    query_terms = list(skills)[:4] or ["python"]
    jobs = []
    headers = {
        "User-Agent": "resume-analyzer-monitoring/1.0 (+https://github.com/)",
        "Accept": "application/json",
    }

    for skill in query_terms:
        response = requests.get(
            REMOTEOK_API_URL.format(query=quote_plus(skill)),
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
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    limit: int = DEFAULT_LIMIT,
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
