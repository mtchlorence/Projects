from datetime import datetime, timedelta, timezone

from analyzer import analyze_resume
from job_search import filter_and_rank_jobs

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

def test_filter_and_rank_jobs_keeps_recent_matching_jobs():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    jobs = [
        {
            "title": "Cloud Engineer",
            "company": "Example Cloud",
            "posted_date": now - timedelta(days=5),
            "skills": ["python", "aws", "terraform"],
        },
        {
            "title": "Old Python Developer",
            "company": "Archive Inc",
            "posted_date": now - timedelta(days=31),
            "skills": ["python"],
        },
        {
            "title": "Product Analyst",
            "company": "No Match LLC",
            "posted_date": now - timedelta(days=2),
            "skills": ["excel"],
        },
    ]

    result = filter_and_rank_jobs(jobs, ["python", "aws"], now=now)

    assert len(result) == 1
    assert result[0]["title"] == "Cloud Engineer"
    assert result[0]["matched_skills"] == ["aws", "python"]

def test_filter_and_rank_jobs_orders_by_skill_match():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    jobs = [
        {
            "title": "Python Engineer",
            "company": "Partial Match",
            "posted_date": now - timedelta(days=1),
            "skills": ["python"],
        },
        {
            "title": "Cloud Platform Engineer",
            "company": "Better Match",
            "posted_date": now - timedelta(days=10),
            "skills": ["python", "aws", "docker"],
        },
    ]

    result = filter_and_rank_jobs(jobs, ["python", "aws", "docker"], now=now)

    assert [job["title"] for job in result] == [
        "Cloud Platform Engineer",
        "Python Engineer",
    ]
