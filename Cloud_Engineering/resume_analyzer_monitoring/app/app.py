from flask import Flask, render_template, request, jsonify
from analyzer import analyze_resume, extract_text_from_pdf
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import os

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp'  # Temporary storage

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename: str) -> bool:
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Prometheus Metrics
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
        job_description = request.form.get("job_description", "")
        resume_text = request.form.get("resume", "")
        
        # Check if file was uploaded
        resume_file = request.files.get("resume_file")
        
        if resume_file and resume_file.filename != '' and allowed_file(resume_file.filename):
            # Process PDF file
            file_bytes = resume_file.read()
            results = analyze_resume(
                resume_source="",
                job_description=job_description,
                is_file=True,
                file_bytes=file_bytes
            )
            # Store filename for display
            resume_filename = resume_file.filename
        else:
            # Use text input (or empty)
            if not resume_text and not job_description:
                results = {
                    "score": 0,
                    "matched_skills": [],
                    "missing_skills": [],
                    "job_skills": [],
                    "resume_skills": []
                }
                resume_filename = None
            else:
                results = analyze_resume(
                    resume_source=resume_text,
                    job_description=job_description,
                    is_file=False
                )
                resume_filename = None

        ANALYSIS_SUCCESS.inc()

        return render_template(
            "index.html",
            results=results,
            resume=resume_text,
            job_description=job_description,
            resume_filename=resume_filename
        )

    except Exception as e:
        ANALYSIS_FAILED.inc()
        # Log error and return with error message
        app.logger.error(f"Analysis failed: {str(e)}")
        return render_template(
            "index.html",
            error=f"Error analyzing resume: {str(e)}",
            resume=request.form.get("resume", ""),
            job_description=request.form.get("job_description", "")
        )

    finally:
        ANALYSIS_DURATION.observe(time.time() - start_time)

@app.route("/api/analyze", methods=["POST"])
def analyze_api():
    """REST API endpoint for programmatic access"""
    try:
        job_description = request.form.get("job_description", "")
        resume_file = request.files.get("resume_file")
        
        if not resume_file:
            return jsonify({"error": "No file uploaded"}), 400
        
        if not allowed_file(resume_file.filename):
            return jsonify({"error": "Only PDF files are supported"}), 400
        
        file_bytes = resume_file.read()
        
        # Extract text and analyze
        resume_text = extract_text_from_pdf(file_bytes)
        results = analyze_resume(
            resume_source=resume_text,
            job_description=job_description,
            is_file=False
        )
        
        return jsonify({
            "success": True,
            "results": results,
            "resume_text_preview": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)