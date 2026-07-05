# 🧠 Resume Skill Analyzer

[![Live Demo](https://img.shields.io/badge/Live-Demo-2563eb?style=for-the-badge&logo=render&logoColor=white)](https://projects-h5c3.onrender.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/mlorence/resume-analyzer)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

> A DevOps-powered resume analyzer that compares your resume against job descriptions, identifies skill gaps, and provides actionable recommendations.

---

## 🚀 Live Demo

**Try it now:** [https://projects-h5c3.onrender.com/](https://projects-h5c3.onrender.com/)

Upload a PDF resume or paste text, add a job description, and get instant feedback on your skill match.

---

## ✨ Features

- **📄 PDF Resume Upload** - Drag-and-drop or click to upload PDF files
- **📝 Text Input Option** - Paste resume text directly
- **🔍 Skill Matching** - Compares your skills against job requirements
- **💼 Live Job Matching** - Finds active Remote OK postings from the last 30 days that match your resume skills
- **📊 Match Score** - Visual percentage score with color-coded feedback
- **✅ Matched Skills** - See which skills you already have
- **❌ Missing Skills** - Identify skill gaps to focus on
- **💡 Recommendations** - Actionable advice based on your match score
- **📱 Responsive UI** - Works on desktop, tablet, and mobile

---

### Job Matching

When you upload a resume or paste resume text, the app extracts known skills from your resume, searches Remote OK for matching roles, filters out postings older than 30 days, and ranks the remaining jobs by skill overlap. Set `JOB_SEARCH_ENABLED=false` to disable live job matching in local or offline environments.

---

### Environment Variables and Secrets

Commit `.env.example` only. Keep real values in a local `.env` file, Render environment variables, or GitHub Actions repository secrets.

Recommended GitHub Secrets:

- `SECRET_KEY`
- `JOB_SEARCH_ENABLED`
- `JOB_SEARCH_API_URL`
- `JOB_SEARCH_LOOKBACK_DAYS`
- `JOB_SEARCH_TIMEOUT_SECONDS`
- `JOB_SEARCH_RESULT_LIMIT`

Local setup:

```bash
cp .env.example .env
```

Then fill `.env` locally. The `.gitignore` file prevents `.env` from being committed.

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| **Backend** | Python 3.10+, Flask |
| **Frontend** | HTML5, CSS3, Bootstrap 5, Font Awesome |
| **PDF Processing** | PyPDF2, pdfplumber |
| **Containerization** | Docker, Docker Compose |
| **Monitoring** | Prometheus, Grafana |
| **CI/CD** | GitHub Actions |
| **Deployment** | Render.com |

---

## 📂 Project Structure 
```
resume_analyzer_monitoring/
├── app/
│ ├── static/
│ │ └── css/
│ │ └── styles.css
│ ├── templates/
│ │ └── index.html
│ ├── analyzer.py
│ └── app.py
├── prometheus/
│ └── prometheus.yml
├── tests/
├── .dockerignore
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── CHANGELOG.md
└── README.md
```

## 🚀 Deployment
This app is currently deployed on Render.com with automatic deployments from the main branch.

Live URL: https://projects-h5c3.onrender.com/

## Alternative Deployment Options
- AWS ECS Fargate – Serverless container orchestration
- AWS EC2 – Full control, Linux/Docker environment
- Docker Hub – Container registry for any cloud platform

## 🔮 Roadmap
See [TODO.md] () for planned features and improvements, including:

- DOCX file support
- Analysis history
- Export as PDF
- User accounts
- NLP-based skill matching
- ATS compatibility checking

## 🙏 Acknowledgments
- Flask – Web framework
- Bootstrap – UI framework
- PyPDF2 – PDF parsing
- pdfplumber – Advanced PDF extraction
- Prometheus – Metrics
- Grafana – Visualization
- Render.com – Hosting
