from datetime import datetime, timedelta, timezone

from ai_agent import build_resume_guidance
from analyzer import analyze_resume
from job_search import (
    _build_search_queries,
    _extract_company_jobs_from_page,
    _is_ph_based,
    _normalize_jsearch_job,
    _passes_relevance_filter,
    _title_similarity,
    fetch_company_site_jobs,
    fetch_jsearch_jobs,
    filter_and_rank_jobs,
    filter_jobs_for_target_roles,
)

def test_analyze_resume_perfect_match():
    resume = "python sql aws docker kubernetes"
    job = "python sql aws docker kubernetes"
    result = analyze_resume(resume, job)
    assert result["score"] == 100.0
    assert len(result["matched_skills"]) == 5
    assert len(result["missing_skills"]) == 0

def test_analyze_resume_partial_match():
    resume = "python sql"
    job = "python sql aws docker"
    result = analyze_resume(resume, job)
    assert result["score"] == 50.0
    assert "aws" in result["missing_skills"]
    assert "docker" in result["missing_skills"]

def test_analyze_resume_empty_input():
    result = analyze_resume("", "")
    assert result["score"] == 0.0
    assert result["matched_skills"] == []
    assert result["missing_skills"] == []

def test_analyze_resume_detects_cloud_terms():
    result = analyze_resume("Cloud engineering and DevOps monitoring experience")

    assert "cloud" in result["resume_skills"]
    assert "cloud engineering" in result["resume_skills"]
    assert "devops" in result["resume_skills"]

def test_analyze_resume_detects_non_technical_categories_and_experience():
    result = analyze_resume(
        "Licensed veterinarian with 4 years of experience in animal care, diagnosis, and clinical documentation."
    )

    assert "veterinarian" in result["resume_skills"]
    assert "animal care" in result["resume_skills"]
    assert result["experience_level"]["level"] == "mid"

def test_build_resume_guidance_fallback_answers_resume_questions(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    guidance = build_resume_guidance(
        "AWS Python Docker SQL resume with cloud monitoring projects",
        ["aws", "python", "docker", "sql", "cloudwatch"],
        {},
    )

    assert guidance["resume_review"]
    assert guidance["strengths"]
    assert guidance["improvements"]
    assert guidance["recommended_roles"]
    assert any("Cloud" in role["title"] for role in guidance["recommended_roles"])

def test_filter_and_rank_jobs_ignores_old_jobs_when_date_filter_enabled(monkeypatch):
    monkeypatch.setenv("JOB_SEARCH_DATE_FILTER_ENABLED", "true")
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    jobs = [
        {
            "title": "Cloud Engineer",
            "company": "Example Cloud",
            "location": "Manila, Philippines",
            "posted_date": now - timedelta(days=5),
            "skills": ["python", "aws", "terraform"],
            "is_ph_based": True,
        },
        {
            "title": "Old Python Developer",
            "company": "Archive Inc",
            "location": "Makati, Philippines",
            "posted_date": now - timedelta(days=31),
            "skills": ["python"],
            "is_ph_based": True,
        },
        {
            "title": "Product Analyst",
            "company": "No Match LLC",
            "location": "Manila, Philippines",
            "posted_date": now - timedelta(days=2),
            "skills": ["excel"],
            "is_ph_based": True,
        },
    ]

    result = filter_and_rank_jobs(jobs, ["python", "aws"], now=now)

    assert len(result) == 1
    assert result[0]["title"] == "Cloud Engineer"
    assert result[0]["matched_skills"] == ["aws", "python"]

def test_filter_and_rank_jobs_keeps_old_jobs_when_date_filter_disabled(monkeypatch):
    monkeypatch.setenv("JOB_SEARCH_DATE_FILTER_ENABLED", "false")
    monkeypatch.setenv("JOB_SEARCH_MIN_MATCHED_SKILLS", "2")
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    jobs = [
        {
            "title": "Old Python Developer",
            "company": "Archive Inc",
            "location": "Makati, Philippines",
            "posted_date": now - timedelta(days=90),
            "skills": ["python", "aws"],
            "is_ph_based": True,
        },
    ]

    result = filter_and_rank_jobs(jobs, ["python", "aws"], now=now)

    assert len(result) == 1
    assert result[0]["title"] == "Old Python Developer"

def test_filter_and_rank_jobs_orders_ph_jobs_by_skill_match():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    jobs = [
        {
            "title": "Python Engineer",
            "company": "Partial Match",
            "location": "Cebu, Philippines",
            "posted_date": now - timedelta(days=1),
            "skills": ["python", "aws"],
            "is_ph_based": True,
        },
        {
            "title": "Cloud Platform Engineer",
            "company": "Better Match",
            "location": "Manila, Philippines",
            "posted_date": now - timedelta(days=10),
            "skills": ["python", "aws", "docker"],
            "is_ph_based": True,
        },
    ]

    result = filter_and_rank_jobs(jobs, ["python", "aws", "docker"], now=now)

    assert [job["title"] for job in result] == [
        "Cloud Platform Engineer",
        "Python Engineer",
    ]

def test_filter_and_rank_jobs_excludes_non_ph_jobs():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    jobs = [
        {
            "title": "Remote Python Engineer",
            "company": "Global Remote",
            "location": "Remote",
            "posted_date": now - timedelta(days=1),
            "skills": ["python", "aws"],
            "is_ph_based": False,
        },
        {
            "title": "Cloud Engineer",
            "company": "Manila Cloud",
            "location": "Manila, Philippines",
            "posted_date": now - timedelta(days=2),
            "skills": ["python", "aws"],
            "is_ph_based": True,
        },
    ]

    result = filter_and_rank_jobs(jobs, ["python", "aws"], now=now)

    assert len(result) == 1
    assert result[0]["company"] == "Manila Cloud"
    assert result[0]["is_ph_based"] is True


def test_filter_and_rank_jobs_falls_back_to_relevant_non_ph_jobs():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    jobs = [
        {
            "title": "Cloud Engineer",
            "company": "Example Corp",
            "location": "Remote",
            "posted_date": now - timedelta(days=1),
            "skills": ["python", "aws"],
            "is_ph_based": False,
        }
    ]

    result = filter_and_rank_jobs(jobs, ["python", "aws"], now=now)

    assert len(result) == 1
    assert result[0]["title"] == "Cloud Engineer"

def test_is_ph_based_uses_location_only_terms():
    assert _is_ph_based("Manila, Philippines") is True
    assert _is_ph_based("Taguig, PH") is True
    assert _is_ph_based("Makati City") is True
    assert _is_ph_based("Remote") is False
    assert _is_ph_based("Phoenix, Arizona") is False

def test_build_search_queries_includes_ai_and_ph_queries():
    profile = {
        "search_queries": ["cloud engineer philippines"],
        "target_titles": ["DevOps Engineer"],
    }

    queries = _build_search_queries(["python", "aws"], profile)

    assert "cloud engineer philippines" in queries
    assert "devops engineer philippines" in queries
    assert "python philippines" in queries
    assert "manila" in queries

def test_build_search_queries_follow_non_technical_resume_category():
    queries = _build_search_queries(["veterinarian", "animal care", "clinical"], {})

    assert "veterinarian philippines" in queries
    assert "veterinary associate philippines" in queries
    assert "cloud engineer philippines" not in queries

def test_filter_jobs_for_target_roles_matches_recommended_roles():
    jobs = [
        {"title": "Cloud Engineer", "company": "Example", "location": "Manila", "match_reason": ""},
        {"title": "Data Analyst", "company": "Example", "location": "Manila", "match_reason": ""},
    ]

    filtered_jobs = filter_jobs_for_target_roles(
        jobs,
        {"recommended_roles": [{"title": "Cloud Engineer", "why": "Good fit"}]},
        {},
    )

    assert [job["title"] for job in filtered_jobs] == ["Cloud Engineer"]

def test_title_similarity_supports_related_job_titles():
    assert _title_similarity("Architectural Designer", "Architect / Architectural Designer") >= 0.42
    assert _title_similarity("Veterinary Associate", "Veterinarian / Veterinary Associate") >= 0.42

def test_filter_jobs_for_target_roles_uses_similarity_and_experience():
    jobs = [
        {"title": "Architectural Designer", "company": "Studio", "location": "Makati", "matched_skills": ["revit"]},
        {"title": "Senior Architect", "company": "Studio", "location": "Makati", "matched_skills": ["revit"]},
        {"title": "Cloud Engineer", "company": "Cloud", "location": "Manila", "matched_skills": ["aws"]},
    ]

    filtered_jobs = filter_jobs_for_target_roles(
        jobs,
        {
            "experience_level": "junior",
            "recommended_roles": [{"title": "Architect / Architectural Designer", "why": "Design fit"}],
        },
        {},
    )

    assert [job["title"] for job in filtered_jobs] == ["Architectural Designer"]
    assert filtered_jobs[0]["target_role"] == "Architect / Architectural Designer"

def test_normalize_jsearch_job_maps_ph_location_and_skills():
    job = _normalize_jsearch_job(
        {
            "job_title": "AWS Cloud Engineer",
            "employer_name": "Example Corp",
            "job_city": "Taguig",
            "job_country": "PH",
            "job_apply_link": "https://example.com/apply",
            "job_posted_at_datetime_utc": "2026-07-01T00:00:00.000Z",
            "job_description": "Python AWS Docker Terraform",
        }
    )

    assert job["source"] == "JSearch"
    assert job["is_ph_based"] is True
    assert "aws" in job["skills"]
    assert "python" in job["skills"]

def test_fetch_jsearch_jobs_skips_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("JSEARCH_API_KEY", raising=False)

    assert fetch_jsearch_jobs(["python"]) == []

def test_extract_company_site_jobposting_json_ld():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@type": "JobPosting",
          "title": "Analyst II - Cloud Engineering",
          "datePosted": "2026-07-01",
          "hiringOrganization": {"name": "DXC Technology"},
          "jobLocation": {
            "address": {
              "addressLocality": "Taguig City",
              "addressCountry": "Philippines"
            }
          },
          "description": "Support cloud engineering tasks with Python, AWS, and Docker."
        }
        </script>
      </head>
    </html>
    """

    jobs = _extract_company_jobs_from_page(html, "https://careers.dxc.com/job/123")

    assert len(jobs) == 1
    assert jobs[0]["company"] == "DXC Technology"
    assert jobs[0]["is_ph_based"] is True
    assert "aws" in jobs[0]["skills"]

def test_fetch_company_site_jobs_skips_when_no_urls(monkeypatch):
    monkeypatch.delenv("CAREER_SITE_URLS", raising=False)

    assert fetch_company_site_jobs(["cloud engineer"]) == []

def test_relevance_filter_rejects_single_or_generic_matches(monkeypatch):
    monkeypatch.setenv("JOB_SEARCH_MIN_MATCHED_SKILLS", "2")
    monkeypatch.setenv("JOB_SEARCH_MIN_SPECIFIC_SKILLS", "1")

    assert _passes_relevance_filter(["api", "cloud"]) is False
    assert _passes_relevance_filter(["python"]) is False
    assert _passes_relevance_filter(["python", "aws"]) is True
    assert _passes_relevance_filter(["cloud", "cloud engineering"]) is True

def test_filter_and_rank_jobs_excludes_weak_resume_matches(monkeypatch):
    monkeypatch.setenv("JOB_SEARCH_DATE_FILTER_ENABLED", "false")
    monkeypatch.setenv("JOB_SEARCH_MIN_MATCHED_SKILLS", "2")
    monkeypatch.setenv("JOB_SEARCH_MIN_SPECIFIC_SKILLS", "1")
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    jobs = [
        {
            "title": "Generic Support Analyst",
            "company": "Weak Match Inc",
            "location": "Manila, Philippines",
            "posted_date": now,
            "skills": ["api", "cloud"],
            "is_ph_based": True,
        },
        {
            "title": "AWS Cloud Engineer",
            "company": "Strong Match Inc",
            "location": "Taguig, Philippines",
            "posted_date": now,
            "skills": ["aws", "python", "cloud"],
            "is_ph_based": True,
        },
    ]

    result = filter_and_rank_jobs(jobs, ["api", "cloud", "aws", "python"], now=now)

    assert len(result) == 1
    assert result[0]["company"] == "Strong Match Inc"
