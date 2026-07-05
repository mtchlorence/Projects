from __future__ import annotations

import json
import os
from typing import Dict, Iterable, List


DEFAULT_PROFILE = {
    "summary": "",
    "target_titles": [],
    "search_queries": [],
    "must_have_skills": [],
}


def _is_enabled() -> bool:
    return os.getenv("AI_JOB_AGENT_ENABLED", "true").lower() not in {"0", "false", "no"}


def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not _is_enabled():
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    return OpenAI(api_key=api_key)


def _extract_response_text(response) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return text

    output = getattr(response, "output", None) or []
    chunks = []
    for item in output:
        for content in getattr(item, "content", []) or []:
            content_text = getattr(content, "text", None)
            if content_text:
                chunks.append(content_text)
    return "\n".join(chunks)


def _safe_json_loads(value: str, fallback):
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def build_candidate_profile(resume_text: str, resume_skills: Iterable[str]) -> Dict:
    client = _get_client()
    if client is None:
        return DEFAULT_PROFILE.copy()

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    skills = sorted(set(resume_skills))
    prompt = f"""
You are a recruiting research agent. Create job-search metadata from this resume.

Return JSON only with this schema:
{{
  "summary": "one sentence candidate summary",
  "target_titles": ["role title", "..."],
  "search_queries": ["query", "..."],
  "must_have_skills": ["skill", "..."]
}}

Rules:
- Create 6 to 10 search queries.
- Include Philippines location intent in every query.
- Focus on jobs located in the Philippines, not remote-only jobs.
- Prefer concise query strings for job-board APIs.
- Do not invent credentials, employers, degrees, or years of experience.

Known extracted skills: {", ".join(skills)}

Resume text:
{resume_text[:6000]}
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
    )
    profile = _safe_json_loads(_extract_response_text(response), DEFAULT_PROFILE.copy())

    return {
        "summary": str(profile.get("summary", "")),
        "target_titles": [str(item) for item in profile.get("target_titles", [])][:8],
        "search_queries": [str(item) for item in profile.get("search_queries", [])][:10],
        "must_have_skills": [str(item).lower() for item in profile.get("must_have_skills", [])][:16],
    }


def enrich_and_rank_jobs(
    resume_text: str,
    resume_skills: Iterable[str],
    jobs: List[Dict],
    candidate_profile: Dict,
) -> List[Dict]:
    client = _get_client()
    if client is None or not jobs:
        return jobs

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    compact_jobs = [
        {
            "index": index,
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "posted_at": job.get("posted_at"),
            "matched_skills": job.get("matched_skills", []),
            "is_ph_based": job.get("is_ph_based", False),
        }
        for index, job in enumerate(jobs[:30])
    ]

    prompt = f"""
You are a job-matching agent. Rank these jobs for the candidate.

Return JSON only:
{{
  "ranked_jobs": [
    {{
      "index": 0,
      "reason": "short reason this is a fit"
    }}
  ]
}}

Rules:
- Only include jobs located in the Philippines.
- Prefer active roles matching cloud, DevOps, data, Python, SQL, AWS, or resume-specific skills.
- Do not include jobs that appear unrelated.
- Keep each reason under 22 words.

Candidate profile:
{json.dumps(candidate_profile, ensure_ascii=True)}

Known extracted skills:
{json.dumps(sorted(set(resume_skills)), ensure_ascii=True)}

Resume excerpt:
{resume_text[:3500]}

Jobs:
{json.dumps(compact_jobs, ensure_ascii=True)}
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
    )
    payload = _safe_json_loads(_extract_response_text(response), {"ranked_jobs": []})

    ranked = []
    seen = set()
    for item in payload.get("ranked_jobs", []):
        try:
            index = int(item.get("index"))
        except (TypeError, ValueError):
            continue
        if index in seen or index < 0 or index >= len(jobs):
            continue
        seen.add(index)
        job = {**jobs[index]}
        job["match_reason"] = str(item.get("reason", "")).strip()
        ranked.append(job)

    for index, job in enumerate(jobs):
        if index not in seen:
            ranked.append(job)

    return ranked
