import pytest
from analyzer import analyze_resume, SKILLS

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