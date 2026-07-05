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


def _fallback_recommended_roles(resume_skills: Iterable[str]) -> List[Dict]:
    skills = {skill.lower() for skill in resume_skills}
    roles = []

    if skills.intersection({"aws", "cloud", "cloud engineering", "lambda", "s3", "cloudwatch"}):
        roles.append(
            {
                "title": "Cloud Engineer",
                "why": "Your cloud, AWS, monitoring, and infrastructure skills point toward cloud operations and engineering roles.",
            }
        )

    if skills.intersection({"devops", "docker", "kubernetes", "terraform", "ci/cd", "jenkins"}):
        roles.append(
            {
                "title": "DevOps Engineer",
                "why": "Your container, automation, and delivery-tooling skills fit DevOps support and platform work.",
            }
        )

    if skills.intersection({"glue", "athena", "etl", "sql", "postgresql", "mysql", "power bi"}):
        roles.append(
            {
                "title": "Data Engineer / BI Engineer",
                "why": "Your SQL, ETL, AWS analytics, and reporting skills fit data pipeline and analytics engineering roles.",
            }
        )

    if skills.intersection({"python", "api", "docker", "postgresql", "mysql"}):
        roles.append(
            {
                "title": "Python Backend Engineer",
                "why": "Your Python, API, database, and deployment skills can support backend application roles.",
            }
        )

    if not roles:
        roles.append(
            {
                "title": "Technical Support Analyst",
                "why": "Your resume has transferable technical skills, but the target role should be refined with more specific tools.",
            }
        )

    return roles[:4]


def _fallback_resume_guidance(resume_skills: Iterable[str]) -> Dict:
    skills = sorted({skill.lower() for skill in resume_skills})
    strongest = skills[:8]

    return {
        "resume_review": (
            "This resume shows a technical profile with useful cloud, data, and operations skills. "
            "It will be stronger if each project clearly states business impact, tools used, and measurable outcomes."
        ),
        "strengths": [
            f"Clear technical skill coverage: {', '.join(strongest)}." if strongest else "Technical foundation is visible.",
            "Good fit for roles that value hands-on tools and operational problem solving.",
            "The skill mix can support cloud, DevOps, data, or backend paths depending on project emphasis.",
        ],
        "improvements": [
            "Add measurable outcomes such as cost saved, runtime reduced, uptime improved, or data processed.",
            "Group projects by role target so recruiters can immediately see your cloud/data/backend direction.",
            "Add short context for each project: problem, tools, implementation, and result.",
        ],
        "recommended_roles": _fallback_recommended_roles(skills),
        "job_search_focus": "Prioritize Philippines-based roles where the description mentions at least two of your stronger tools.",
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

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
        )
        profile = _safe_json_loads(_extract_response_text(response), DEFAULT_PROFILE.copy())
    except Exception:
        profile = DEFAULT_PROFILE.copy()

    return {
        "summary": str(profile.get("summary", "")),
        "target_titles": [str(item) for item in profile.get("target_titles", [])][:8],
        "search_queries": [str(item) for item in profile.get("search_queries", [])][:10],
        "must_have_skills": [str(item).lower() for item in profile.get("must_have_skills", [])][:16],
    }


def build_resume_guidance(
    resume_text: str,
    resume_skills: Iterable[str],
    candidate_profile: Dict,
) -> Dict:
    resume_skills = list(resume_skills)
    client = _get_client()
    if client is None:
        return _fallback_resume_guidance(resume_skills)

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    prompt = f"""
You are a concise technical career advisor for a Philippines-based job search.

Answer these three user questions from the resume:
1. What do you think of this resume?
2. What jobs should this person target?
3. What should they apply to based on the resume?

Return JSON only:
{{
  "resume_review": "direct, useful paragraph",
  "strengths": ["strength", "..."],
  "improvements": ["improvement", "..."],
  "recommended_roles": [
    {{"title": "role title", "why": "short reason"}}
  ],
  "job_search_focus": "one sentence strategy"
}}

Rules:
- Do not flatter vaguely.
- Do not invent employers, credentials, degrees, or years of experience.
- Recommended roles must be realistic for the extracted skills.
- Keep strengths and improvements to 3 bullets each.
- Keep role reasons under 20 words each.

Candidate profile:
{json.dumps(candidate_profile, ensure_ascii=True)}

Extracted skills:
{json.dumps(sorted(set(resume_skills)), ensure_ascii=True)}

Resume text:
{resume_text[:6000]}
""".strip()

    fallback = _fallback_resume_guidance(resume_skills)
    try:
        response = client.responses.create(
            model=model,
            input=prompt,
        )
        guidance = _safe_json_loads(_extract_response_text(response), fallback)
    except Exception:
        guidance = fallback

    recommended_roles = []
    for role in guidance.get("recommended_roles", []):
        if isinstance(role, dict):
            title = str(role.get("title", "")).strip()
            why = str(role.get("why", "")).strip()
            if title:
                recommended_roles.append({"title": title, "why": why})

    return {
        "resume_review": str(guidance.get("resume_review") or fallback["resume_review"]),
        "strengths": [str(item) for item in guidance.get("strengths", [])][:3] or fallback["strengths"],
        "improvements": [str(item) for item in guidance.get("improvements", [])][:3] or fallback["improvements"],
        "recommended_roles": recommended_roles[:4] or fallback["recommended_roles"],
        "job_search_focus": str(guidance.get("job_search_focus") or fallback["job_search_focus"]),
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

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
        )
        payload = _safe_json_loads(_extract_response_text(response), {"ranked_jobs": []})
    except Exception:
        return jobs

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
