import os
import time

from dotenv import load_dotenv
from flask import Flask, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from ai_agent import build_resume_guidance
from analyzer import analyze_resume
from job_search import filter_jobs_for_target_roles, find_matching_jobs


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ANALYSIS_TOTAL = Counter("resume_analysis_total", "Total number of resume analyses performed")
ANALYSIS_SUCCESS = Counter("resume_analysis_success_total", "Total number of successful resume analyses")
ANALYSIS_FAILED = Counter("resume_analysis_failed_total", "Total number of failed resume analyses")
ANALYSIS_DURATION = Histogram("resume_analysis_duration_seconds", "Time spent processing resume analysis")
JOB_MATCH_TOTAL = Counter("resume_job_match_total", "Total number of resume-based job searches performed")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"pdf"}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    start_time = time.time()
    ANALYSIS_TOTAL.inc()

    try:
        resume_text = request.form.get("resume", "").strip()
        resume_file = request.files.get("resume_file")

        if resume_file and resume_file.filename and allowed_file(resume_file.filename):
            results = analyze_resume(
                resume_source="",
                job_description="",
                is_file=True,
                file_bytes=resume_file.read(),
            )
        elif resume_text:
            results = analyze_resume(
                resume_source=resume_text,
                job_description="",
                is_file=False,
            )
        else:
            return render_template(
                "index.html",
                error="Please upload a PDF resume or paste your resume text.",
            )

        JOB_MATCH_TOTAL.inc()
        job_matches = find_matching_jobs(
            results.get("resume_skills", []),
            resume_text=results.get("resume_text", ""),
        )
        resume_guidance = build_resume_guidance(
            results.get("resume_text", ""),
            results.get("resume_skills", []),
            {
                **job_matches.get("candidate_profile", {}),
                "experience_level": results.get("experience_level", {}).get("level", ""),
            },
        )
        display_jobs = filter_jobs_for_target_roles(
            job_matches.get("jobs", []),
            resume_guidance,
            {
                **job_matches.get("candidate_profile", {}),
                "experience_level": results.get("experience_level", {}).get("level", ""),
            },
        )
        ANALYSIS_SUCCESS.inc()

        return render_template(
            "index.html",
            results=results,
            resume_guidance=resume_guidance,
            job_matches=display_jobs,
            job_search_error=job_matches.get("error"),
            analyzed=True,
        )

    except Exception as e:
        ANALYSIS_FAILED.inc()
        app.logger.error(f"Analysis failed: {str(e)}")
        return render_template("index.html", error=f"Error analyzing resume: {str(e)}")

    finally:
        ANALYSIS_DURATION.observe(time.time() - start_time)


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
