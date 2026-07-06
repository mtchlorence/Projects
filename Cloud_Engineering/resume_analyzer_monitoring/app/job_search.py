from __future__ import annotations

import json
import os
import re
import urllib.robotparser
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote_plus, urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ai_agent import build_candidate_profile, enrich_and_rank_jobs
from analyzer import SKILLS


DEFAULT_REMOTEOK_API_URL = "https://remoteok.com/remote-{query}-jobs.json"
DEFAULT_REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs?search={query}"
DEFAULT_JSEARCH_API_URL = "https://jsearch.p.rapidapi.com/search"
DEFAULT_USER_AGENT = "resume-analyzer-monitoring/1.0"
PH_SEARCH_TERMS = ["philippines", "philippine", "manila"]
JOB_LINK_KEYWORDS = {
    "job",
    "jobs",
    "career",
    "careers",
    "opening",
    "openings",
    "philippines",
    "manila",
    "taguig",
    "makati",
    "cebu",
    "davao",
}
PH_LOCATION_KEYWORDS = {
    "philippines",
    "philippine",
    "manila",
    "makati",
    "taguig",
    "quezon city",
    "cebu",
    "davao",
}
GENERIC_MATCH_SKILLS = {
    "api",
    "cloud",
    "etl",
    "git",
    "linux",
    "monitoring",
    "sql",
}
TITLE_STOP_WORDS = {
    "and",
    "associate",
    "for",
    "i",
    "ii",
    "iii",
    "iv",
    "junior",
    "level",
    "mid",
    "of",
    "senior",
    "the",
}
EXPERIENCE_TITLE_TERMS = {
    "entry": {"entry", "entry-level", "junior", "trainee", "intern", "associate"},
    "junior": {"entry", "entry-level", "junior", "trainee", "associate"},
    "mid": {"associate", "mid", "mid-level", "specialist", "officer"},
    "senior": {"senior", "lead", "principal", "manager", "supervisor", "head"},
}


def _get_env_int(name: str, fallback: int) -> int:
    try:
        return int(os.getenv(name, fallback))
    except (TypeError, ValueError):
        return fallback


def _get_lookback_days() -> int:
    return _get_env_int("JOB_SEARCH_LOOKBACK_DAYS", 30)


def _get_timeout_seconds() -> int:
    return _get_env_int("JOB_SEARCH_TIMEOUT_SECONDS", 8)


def _get_result_limit() -> int:
    return _get_env_int("JOB_SEARCH_RESULT_LIMIT", 12)


def _get_min_matched_skills() -> int:
    return _get_env_int("JOB_SEARCH_MIN_MATCHED_SKILLS", 2)


def _get_min_specific_skills() -> int:
    return _get_env_int("JOB_SEARCH_MIN_SPECIFIC_SKILLS", 1)


def _date_filter_enabled() -> bool:
    return os.getenv("JOB_SEARCH_DATE_FILTER_ENABLED", "false").lower() not in {"0", "false", "no"}


def _get_career_site_max_pages() -> int:
    return _get_env_int("CAREER_SITE_MAX_PAGES", 16)


def _get_provider_names() -> List[str]:
    providers = os.getenv("JOB_SEARCH_PROVIDERS", "company_sites,jsearch,remoteok,remotive")
    return [provider.strip().lower() for provider in providers.split(",") if provider.strip()]


def _get_career_site_urls() -> List[str]:
    raw_urls = os.getenv("CAREER_SITE_URLS", "")
    return [
        url.strip()
        for url in re.split(r"[\n,;]+", raw_urls)
        if url.strip().startswith(("http://", "https://"))
    ]


def _is_ph_based(location: str) -> bool:
    text = location.lower()
    tokens = {token for token in re.split(r"[^a-z]+", text) if token}
    return "ph" in tokens or any(
        re.search(rf"\b{re.escape(keyword)}\b", text)
        for keyword in PH_LOCATION_KEYWORDS
    )


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


def _active_listing_date() -> datetime:
    return datetime.now(timezone.utc)


def _extract_skills_from_text(text: str) -> List[str]:
    lowered = text.lower()
    return sorted({skill for skill in SKILLS if skill in lowered})


def _passes_relevance_filter(matched_skills: Iterable[str]) -> bool:
    matched = {skill.lower() for skill in matched_skills}
    specific_matches = matched - GENERIC_MATCH_SKILLS
    return (
        len(matched) >= _get_min_matched_skills()
        and len(specific_matches) >= _get_min_specific_skills()
    )


def _title_tokens(title: str) -> set:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", title.lower())
        if token not in TITLE_STOP_WORDS and len(token) >= 2
    }


def _title_similarity(job_title: str, target_title: str) -> float:
    job_title = job_title.lower().strip()
    target_title = target_title.lower().strip()
    if not job_title or not target_title:
        return 0.0

    sequence_score = SequenceMatcher(None, job_title, target_title).ratio()
    job_tokens = _title_tokens(job_title)
    target_tokens = _title_tokens(target_title)
    if not job_tokens or not target_tokens:
        return sequence_score

    token_overlap = len(job_tokens.intersection(target_tokens)) / len(target_tokens)
    return max(sequence_score, token_overlap)


def _experience_matches_title(job_title: str, experience_level: str) -> bool:
    if not experience_level:
        return True

    level = str(experience_level).lower()
    terms = EXPERIENCE_TITLE_TERMS.get(level)
    if not terms:
        return True

    title = job_title.lower()
    senior_terms = EXPERIENCE_TITLE_TERMS["senior"]
    junior_terms = EXPERIENCE_TITLE_TERMS["entry"].union(EXPERIENCE_TITLE_TERMS["junior"])

    if level in {"entry", "junior"}:
        return not any(term in title for term in senior_terms)

    if level == "senior":
        return any(term in title for term in terms) or not any(term in title for term in junior_terms)

    return not any(term in title for term in {"intern", "trainee"})


def _normalize_remoteok_job(raw_job: Dict) -> Optional[Dict]:
    tags = raw_job.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]

    if not raw_job.get("position"):
        return None

    description = " ".join(
        str(raw_job.get(field, ""))
        for field in ("position", "company", "description")
    )
    description = f"{description} {' '.join(str(tag) for tag in tags)}"

    location = raw_job.get("location") or "Remote"
    posted_at = raw_job.get("date") or raw_job.get("created_at")

    return {
        "title": raw_job.get("position") or "Untitled role",
        "company": raw_job.get("company") or "Unknown company",
        "location": location,
        "url": raw_job.get("url") or raw_job.get("apply_url") or raw_job.get("source_url"),
        "posted_at": posted_at,
        "posted_date": _parse_posted_date(posted_at),
        "skills": _extract_skills_from_text(description),
        "source": "Remote OK",
        "is_ph_based": _is_ph_based(location),
    }


def _normalize_remotive_job(raw_job: Dict) -> Optional[Dict]:
    if not raw_job.get("title"):
        return None

    description = " ".join(
        str(raw_job.get(field, ""))
        for field in ("title", "company_name", "description", "candidate_required_location")
    )
    location = raw_job.get("candidate_required_location") or "Remote"
    posted_at = raw_job.get("publication_date")

    return {
        "title": raw_job.get("title") or "Untitled role",
        "company": raw_job.get("company_name") or "Unknown company",
        "location": location,
        "url": raw_job.get("url"),
        "posted_at": posted_at,
        "posted_date": _parse_posted_date(posted_at),
        "skills": _extract_skills_from_text(description),
        "source": "Remotive",
        "is_ph_based": _is_ph_based(location),
    }


def _normalize_jsearch_job(raw_job: Dict) -> Optional[Dict]:
    if not raw_job.get("job_title"):
        return None

    city = raw_job.get("job_city") or ""
    state = raw_job.get("job_state") or ""
    country = raw_job.get("job_country") or ""
    location = ", ".join(part for part in (city, state, country) if part) or "Unknown"
    description = " ".join(
        str(raw_job.get(field, ""))
        for field in ("job_title", "employer_name", "job_description", "job_required_skills")
    )
    posted_at = raw_job.get("job_posted_at_datetime_utc")

    return {
        "title": raw_job.get("job_title") or "Untitled role",
        "company": raw_job.get("employer_name") or "Unknown company",
        "location": location,
        "url": raw_job.get("job_apply_link") or raw_job.get("job_google_link"),
        "posted_at": posted_at,
        "posted_date": _parse_posted_date(posted_at),
        "skills": _extract_skills_from_text(description),
        "source": "JSearch",
        "is_ph_based": _is_ph_based(location),
    }


def _json_ld_items(payload) -> List[Dict]:
    if isinstance(payload, list):
        items = []
        for item in payload:
            items.extend(_json_ld_items(item))
        return items

    if not isinstance(payload, dict):
        return []

    items = []
    if "@graph" in payload:
        items.extend(_json_ld_items(payload["@graph"]))
    items.append(payload)
    return items


def _jobposting_type_matches(value) -> bool:
    if isinstance(value, list):
        return any(_jobposting_type_matches(item) for item in value)
    return str(value).lower() == "jobposting"


def _text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


def _location_from_jobposting(jobposting: Dict) -> str:
    locations = jobposting.get("jobLocation") or jobposting.get("applicantLocationRequirements") or []
    if isinstance(locations, dict):
        locations = [locations]

    parts = []
    for location in locations if isinstance(locations, list) else []:
        address = location.get("address", location) if isinstance(location, dict) else location
        if isinstance(address, dict):
            parts.extend(
                str(address.get(field, ""))
                for field in ("addressLocality", "addressRegion", "addressCountry")
                if address.get(field)
            )
        elif address:
            parts.append(str(address))

    return ", ".join(parts) or str(jobposting.get("jobLocation", "") or "Unknown")


def _normalize_company_site_job(
    title: str,
    company: str,
    location: str,
    description: str,
    url: str,
    posted_at: Optional[str] = None,
) -> Optional[Dict]:
    if not title:
        return None

    posted_date = _parse_posted_date(posted_at) if posted_at else _active_listing_date()
    posted_label = posted_at or "Active listing"

    return {
        "title": title.strip(),
        "company": company.strip() or urlparse(url).netloc,
        "location": location.strip() or "Unknown",
        "url": url,
        "posted_at": posted_label,
        "posted_date": posted_date,
        "skills": _extract_skills_from_text(f"{title} {description}"),
        "source": "Company career site",
        "is_ph_based": _is_ph_based(location),
    }


def _extract_company_jobs_from_page(html: str, url: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for script in soup.find_all("script", type=lambda value: value and "ld+json" in value.lower()):
        try:
            payload = json.loads(script.string or "")
        except ValueError:
            continue

        for item in _json_ld_items(payload):
            if not _jobposting_type_matches(item.get("@type")):
                continue

            company = item.get("hiringOrganization", {})
            if isinstance(company, dict):
                company = company.get("name", "")

            job = _normalize_company_site_job(
                title=str(item.get("title", "")),
                company=str(company or ""),
                location=_location_from_jobposting(item),
                description=_text_from_html(str(item.get("description", ""))),
                url=str(item.get("url") or url),
                posted_at=item.get("datePosted"),
            )
            if job:
                jobs.append(job)

    if jobs:
        return jobs

    page_text = _text_from_html(html)
    if not _is_ph_based(page_text):
        return []

    title = soup.find(["h1", "title"])
    title_text = title.get_text(" ", strip=True) if title else ""
    if not title_text or not any(keyword in page_text.lower() for keyword in ("job", "qualification", "responsibilit")):
        return []

    company = urlparse(url).netloc.replace("careers.", "").replace("www.", "")
    return [
        _normalize_company_site_job(
            title=title_text,
            company=company,
            location=page_text[:1200],
            description=page_text,
            url=url,
        )
    ]


def _can_fetch_url(url: str, timeout: Optional[int] = None) -> bool:
    if os.getenv("CAREER_SITES_RESPECT_ROBOTS", "true").lower() in {"0", "false", "no"}:
        return True

    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        response = requests.get(
            robots_url,
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=timeout or _get_timeout_seconds(),
        )
        if response.status_code >= 400:
            return True
        parser.parse(response.text.splitlines())
    except requests.RequestException:
        return True
    return parser.can_fetch(DEFAULT_USER_AGENT, url)


def _should_follow_career_link(url: str, seed_netloc: str, text: str, queries: Iterable[str]) -> bool:
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc != seed_netloc:
        return False

    haystack = f"{url} {text}".lower()
    query_terms = {
        term
        for query in queries
        for term in re.split(r"[^a-z0-9+#.]+", query.lower())
        if len(term) >= 3
    }
    return bool(JOB_LINK_KEYWORDS.intersection(set(re.split(r"[^a-z]+", haystack))) or query_terms.intersection(set(haystack.split())))


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


def _build_search_queries(resume_skills: Iterable[str], candidate_profile: Dict) -> List[str]:
    skills = list(resume_skills)
    skill_set = {skill.lower() for skill in skills}
    ai_queries = candidate_profile.get("search_queries", [])
    target_titles = candidate_profile.get("target_titles", [])
    career_queries = []

    if skill_set.intersection({"architecture", "architect", "autocad", "revit", "sketchup", "bim", "drafting"}):
        career_queries.extend(
            [
                "architect philippines",
                "architectural designer philippines",
                "revit designer philippines",
                "bim specialist philippines",
            ]
        )

    if skill_set.intersection({"veterinarian", "veterinary", "animal care", "animal health", "clinical", "diagnosis"}):
        career_queries.extend(
            [
                "veterinarian philippines",
                "veterinary associate philippines",
                "animal care philippines",
                "veterinary clinic philippines",
            ]
        )

    if skill_set.intersection({"aws", "cloud", "cloud engineering", "devops", "python", "sql", "docker"}):
        career_queries.extend(
            [
                "cloud engineer philippines",
                "devops engineer philippines",
                "python aws philippines",
            ]
        )

    if skill_set.intersection({"project management", "customer service", "communication", "leadership", "documentation"}):
        career_queries.extend(
            [
                "project coordinator philippines",
                "operations associate philippines",
                "customer success philippines",
            ]
        )

    fallback_queries = [
        *skills[:5],
        *[f"{skill} philippines" for skill in skills[:4]],
        *target_titles[:4],
        *career_queries,
    ]
    return list(dict.fromkeys([*ai_queries, *fallback_queries, *PH_SEARCH_TERMS]))[:14]


def fetch_remoteok_jobs(
    queries: Iterable[str],
    timeout: Optional[int] = None,
) -> List[Dict]:
    timeout = timeout if timeout is not None else _get_timeout_seconds()
    api_url = os.getenv("REMOTEOK_JOB_API_URL", DEFAULT_REMOTEOK_API_URL)
    headers = {
        "User-Agent": "resume-analyzer-monitoring/1.0",
        "Accept": "application/json",
    }
    jobs = []

    for query in queries:
        response = requests.get(
            api_url.format(query=quote_plus(query)),
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            continue

        for raw_job in payload:
            if isinstance(raw_job, dict):
                job = _normalize_remoteok_job(raw_job)
                if job:
                    jobs.append(job)

    return jobs


def fetch_remotive_jobs(
    queries: Iterable[str],
    timeout: Optional[int] = None,
) -> List[Dict]:
    timeout = timeout if timeout is not None else _get_timeout_seconds()
    api_url = os.getenv("REMOTIVE_JOB_API_URL", DEFAULT_REMOTIVE_API_URL)
    headers = {
        "User-Agent": "resume-analyzer-monitoring/1.0",
        "Accept": "application/json",
    }
    jobs = []

    for query in queries:
        response = requests.get(
            api_url.format(query=quote_plus(query)),
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        raw_jobs = payload.get("jobs", []) if isinstance(payload, dict) else []

        for raw_job in raw_jobs:
            if isinstance(raw_job, dict):
                job = _normalize_remotive_job(raw_job)
                if job:
                    jobs.append(job)

    return jobs


def fetch_jsearch_jobs(
    queries: Iterable[str],
    timeout: Optional[int] = None,
) -> List[Dict]:
    api_key = os.getenv("JSEARCH_API_KEY")
    if not api_key:
        return []

    timeout = timeout if timeout is not None else _get_timeout_seconds()
    api_url = os.getenv("JSEARCH_API_URL", DEFAULT_JSEARCH_API_URL)
    host = os.getenv("JSEARCH_API_HOST", "jsearch.p.rapidapi.com")
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": host,
        "Accept": "application/json",
    }
    jobs = []

    for query in queries:
        response = requests.get(
            api_url,
            headers=headers,
            params={
                "query": f"{query} Philippines",
                "page": "1",
                "num_pages": "1",
                "date_posted": "month",
                "country": "ph",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        raw_jobs = payload.get("data", []) if isinstance(payload, dict) else []

        for raw_job in raw_jobs:
            if isinstance(raw_job, dict):
                job = _normalize_jsearch_job(raw_job)
                if job:
                    jobs.append(job)

    return jobs


def fetch_company_site_jobs(
    queries: Iterable[str],
    timeout: Optional[int] = None,
) -> List[Dict]:
    seed_urls = _get_career_site_urls()
    if not seed_urls:
        return []

    timeout = timeout if timeout is not None else _get_timeout_seconds()
    max_pages = _get_career_site_max_pages()
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }
    jobs = []

    for seed_url in seed_urls:
        seed_netloc = urlparse(seed_url).netloc
        queue = [seed_url]
        seen = set()

        while queue and len(seen) < max_pages:
            url = queue.pop(0)
            url = urldefrag(url)[0]
            if url in seen or not _can_fetch_url(url, timeout=timeout):
                continue
            seen.add(url)

            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
            except requests.RequestException:
                continue

            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                continue

            html = response.text
            jobs.extend(_extract_company_jobs_from_page(html, url))

            soup = BeautifulSoup(html, "html.parser")
            for anchor in soup.find_all("a", href=True):
                next_url = urldefrag(urljoin(url, anchor["href"]))[0]
                link_text = anchor.get_text(" ", strip=True)
                if next_url not in seen and _should_follow_career_link(next_url, seed_netloc, link_text, queries):
                    queue.append(next_url)

    return _dedupe_jobs(jobs)


def fetch_jobs(queries: Iterable[str]) -> List[Dict]:
    provider_names = _get_provider_names()
    jobs = []

    if "company_sites" in provider_names:
        jobs.extend(fetch_company_site_jobs(queries))

    if "jsearch" in provider_names:
        jobs.extend(fetch_jsearch_jobs(queries))

    if "remoteok" in provider_names:
        jobs.extend(fetch_remoteok_jobs(queries))

    if "remotive" in provider_names:
        jobs.extend(fetch_remotive_jobs(queries))

    return _dedupe_jobs(jobs)


def filter_jobs_for_target_roles(
    jobs: Iterable[Dict],
    resume_guidance: Optional[Dict] = None,
    candidate_profile: Optional[Dict] = None,
) -> List[Dict]:
    jobs = list(jobs)
    if not jobs:
        return []

    role_titles = []
    if isinstance(resume_guidance, dict):
        for role in resume_guidance.get("recommended_roles", []) or []:
            if isinstance(role, dict):
                title = str(role.get("title", "")).strip()
                if title:
                    role_titles.append(title)

    if isinstance(candidate_profile, dict):
        for title in candidate_profile.get("target_titles", []) or []:
            title = str(title).strip()
            if title:
                role_titles.append(title)

    if not role_titles:
        return jobs

    experience_level = ""
    if isinstance(resume_guidance, dict):
        experience_level = str(resume_guidance.get("experience_level", "") or "")
    if not experience_level and isinstance(candidate_profile, dict):
        experience_level = str(candidate_profile.get("experience_level", "") or "")

    filtered_jobs = []
    for job in jobs:
        job_title = str(job.get("title", ""))
        target_role, similarity = max(
            ((role_title, _title_similarity(job_title, role_title)) for role_title in role_titles),
            key=lambda item: item[1],
        )

        if similarity >= 0.42 and _experience_matches_title(job_title, experience_level):
            annotated_job = {
                **job,
                "target_role": target_role,
                "title_similarity": round(similarity, 3),
            }
            if not annotated_job.get("match_reason"):
                annotated_job["match_reason"] = f"Matches the target role: {target_role}."
            filtered_jobs.append(annotated_job)

    filtered_jobs.sort(
        key=lambda item: (
            item.get("title_similarity", 0),
            len(item.get("matched_skills", [])),
            item.get("posted_date") or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )

    if filtered_jobs:
        return filtered_jobs

    annotated_jobs = []
    for job in jobs:
        job_title = str(job.get("title", ""))
        target_role, similarity = max(
            ((role_title, _title_similarity(job_title, role_title)) for role_title in role_titles),
            key=lambda item: item[1],
        )
        annotated_jobs.append(
            {
                **job,
                "target_role": target_role,
                "title_similarity": round(similarity, 3),
            }
        )

    return annotated_jobs


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
    ph_jobs = []

    for job in jobs:
        posted_date = job.get("posted_date")
        if isinstance(posted_date, str):
            posted_date = _parse_posted_date(posted_date)

        if _date_filter_enabled() and (not posted_date or posted_date < cutoff):
            continue

        job_skills = {skill.lower() for skill in job.get("skills", [])}
        matched_skills = sorted(resume_skill_set.intersection(job_skills))
        if not _passes_relevance_filter(matched_skills):
            continue

        normalized_job = {
            **job,
            "posted_date": posted_date,
            "posted_at": posted_date.strftime("%Y-%m-%d") if posted_date else None,
            "matched_skills": matched_skills,
            "region_label": "Philippines" if job.get("is_ph_based", False) else "Remote/Other",
        }

        if job.get("is_ph_based", False):
            ph_jobs.append(normalized_job)
        else:
            ranked_jobs.append(normalized_job)

    ph_jobs.sort(
        key=lambda item: (
            len(item["matched_skills"]),
            item["posted_date"],
        ),
        reverse=True,
    )
    ranked_jobs.sort(
        key=lambda item: (
            len(item["matched_skills"]),
            item["posted_date"],
        ),
        reverse=True,
    )

    if ph_jobs:
        return ph_jobs[:limit]
    return ranked_jobs[:limit]


def find_matching_jobs(
    resume_skills: Iterable[str],
    resume_text: str = "",
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
        candidate_profile = build_candidate_profile(resume_text, resume_skills)
        queries = _build_search_queries(resume_skills, candidate_profile)
        jobs = fetch_jobs(queries)
        ranked_jobs = filter_and_rank_jobs(
            jobs,
            resume_skills,
            lookback_days=lookback_days,
            limit=limit,
        )
        enriched_jobs = enrich_and_rank_jobs(
            resume_text,
            resume_skills,
            ranked_jobs,
            candidate_profile,
        )
        return {
            "jobs": enriched_jobs[: limit or _get_result_limit()],
            "error": None,
            "candidate_profile": candidate_profile,
        }
    except Exception as exc:
        return {
            "jobs": [],
            "error": f"Live job search is unavailable right now: {exc}",
        }
