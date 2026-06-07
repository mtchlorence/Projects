from flask import Flask, render_template, request
from analyzer import analyze_resume
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)
ANALYSIS_TOTAL = Counter(
    "resume_analysis_total",
    "Total number of resume analyses performed"
)

ANALYSIS_SUCCESS = Counter(
    "resume_analysis_success_total",
    "Total number of successful resume analyses"
)

ANALYSIS_FAILED = Counter(
    "resume_analysis_failed_total",
    "Total number of failed resume analyses"
)

ANALYSIS_DURATION = Histogram(
    "resume_analysis_duration_seconds",
    "Time spent processing resume analysis"
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    start_time = time.time()
    ANALYSIS_TOTAL.inc()

    try:
        resume = request.form.get("resume", "")
        job_description = request.form.get("job_description", "")

        results = analyze_resume(
            resume,
            job_description
        )

        ANALYSIS_SUCCESS.inc()

        return render_template(
            "index.html",
            results=results,
            resume=resume,
            job_description=job_description
        )

    except Exception:
        ANALYSIS_FAILED.inc()
        raise

    finally:
        ANALYSIS_DURATION.observe(time.time() - start_time)

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)