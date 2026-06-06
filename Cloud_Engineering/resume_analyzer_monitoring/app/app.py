from flask import Flask, render_template, request
from analyzer import analyze_resume

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():

    resume = request.form.get("resume")
    job_description = request.form.get("job_description")

    results = analyze_resume(
        resume,
        job_description
    )

    return render_template(
        "index.html",
        results=results,
        resume=resume,
        job_description=job_description
    )

@app.route("/health")
def health():
    return {
        "status": "healthy"
    }

if __name__ == "__main__":
    app.run(debug=True)