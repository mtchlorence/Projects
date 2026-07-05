# Resume PH Job Matcher

[![Live Demo](https://img.shields.io/badge/Live-Demo-2563eb?style=for-the-badge&logo=render&logoColor=white)](https://projects-h5c3.onrender.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/mlorence/resume-analyzer)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

A Flask portfolio app that accepts a resume, extracts skills, and discovers Philippines-based jobs that match the candidate profile.

## Features

- PDF resume upload with drag-and-drop support
- Resume text paste fallback
- PDF text extraction with `pdfplumber`
- Skill extraction from a configurable skill list
- Philippines-only job filtering
- Optional AI-assisted search-query generation and job match explanations
- Configurable job providers:
  - Public company career sites from `CAREER_SITE_URLS`
  - JSearch / RapidAPI
  - Remote OK
  - Remotive
- Prometheus metrics endpoint at `/metrics`
- Docker and Docker Compose support

## App Flow

1. User uploads a PDF resume or pastes resume text.
2. Flask extracts resume text and known skills.
3. The optional AI layer builds better Philippines-focused job search queries.
4. Job providers fetch candidate jobs.
5. The app removes non-Philippines jobs.
6. Date filtering is optional and currently off by default.
7. Jobs are ranked by matched skills and recency.
8. The results page shows extracted skills, job cards, and optional AI match reasons.

Uploaded files are not persisted. They are read during the request only.

## Job Discovery

The app does not scrape LinkedIn, JobStreet, or Indeed directly. Instead, it uses safer provider adapters:

- `company_sites`: crawls only configured public company career URLs, follows same-domain career/job links, and respects `robots.txt` by default.
- `jsearch`: uses JSearch/RapidAPI when `JSEARCH_API_KEY` is configured.
- `remoteok` and `remotive`: fallback public remote-job providers.

Example company career-site setup:

```env
JOB_SEARCH_PROVIDERS=company_sites,jsearch,remoteok,remotive
CAREER_SITE_URLS=https://careers.dxc.com/search-jobs/Philippines;https://www.accenture.com/ph-en/careers/jobsearch
CAREER_SITE_MAX_PAGES=16
CAREER_SITES_RESPECT_ROBOTS=true
```

To test one job page directly:

```env
CAREER_SITE_URLS=https://careers.dxc.com/job/23409628/analyst-ii-cloud-engineering-taguig-city-ph/
```

## AI Layer

The app works without OpenAI credentials. If `OPENAI_API_KEY` is missing, it falls back to deterministic skill-based matching.

When `OPENAI_API_KEY` is configured, `app/ai_agent.py` can:

- summarize the candidate profile
- generate better Philippines-focused search queries
- enrich jobs with short "why this matches" explanations

## Environment Variables

Use a local `.env` file for runtime configuration. Keep `.env` out of git because it may contain API keys and secrets.

Important variables:

```env
SECRET_KEY=
OPENAI_API_KEY=
AI_JOB_AGENT_ENABLED=true
OPENAI_MODEL=gpt-4.1-mini

JOB_SEARCH_ENABLED=true
JOB_SEARCH_COUNTRY=philippines
JOB_SEARCH_PROVIDERS=company_sites,jsearch,remoteok,remotive

CAREER_SITE_URLS=
CAREER_SITE_MAX_PAGES=16
CAREER_SITES_RESPECT_ROBOTS=true

JSEARCH_API_KEY=
JSEARCH_API_URL=https://jsearch.p.rapidapi.com/search
JSEARCH_API_HOST=jsearch.p.rapidapi.com

REMOTEOK_JOB_API_URL=https://remoteok.com/remote-{query}-jobs.json
REMOTIVE_JOB_API_URL=https://remotive.com/api/remote-jobs?search={query}

JOB_SEARCH_LOOKBACK_DAYS=30
JOB_SEARCH_DATE_FILTER_ENABLED=false
JOB_SEARCH_MIN_MATCHED_SKILLS=2
JOB_SEARCH_MIN_SPECIFIC_SKILLS=1
JOB_SEARCH_TIMEOUT_SECONDS=8
JOB_SEARCH_RESULT_LIMIT=12
```

The `.gitignore` file prevents `.env` from being committed.

## Running Locally

With Docker:

```bash
docker compose up --build app
```

Then open:

```text
http://127.0.0.1:5000
```

Metrics:

```text
http://127.0.0.1:5000/metrics
```

## Testing

If Python and dependencies are installed locally:

```bash
python -m pytest
```

Inside Docker:

```bash
docker compose exec app python -m pytest
```

If `pytest` is not installed in the image, rebuild after dependency updates:

```bash
docker compose up --build app
```

## Tech Stack

| Category | Technologies |
|----------|--------------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, Bootstrap 5, Font Awesome |
| PDF Processing | PyPDF2, pdfplumber |
| Job Discovery | requests, BeautifulSoup, provider adapters |
| Optional AI | OpenAI Python SDK |
| Monitoring | Prometheus, Grafana |
| Containerization | Docker, Docker Compose |

## Project Structure

```text
resume_analyzer_monitoring/
├── app/
│   ├── static/
│   │   └── styles.css
│   ├── templates/
│   │   └── index.html
│   ├── ai_agent.py
│   ├── analyzer.py
│   ├── app.py
│   └── job_search.py
├── prometheus/
│   └── prometheus.yml
├── tests/
│   ├── conftest.py
│   └── test_analyzer.py
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Deployment Notes

- Store `SECRET_KEY`, `OPENAI_API_KEY`, and provider API keys in deployment environment variables or GitHub Secrets.
- Keep `CAREER_SITES_RESPECT_ROBOTS=true` unless you have explicit permission to crawl a site differently.
- Keep `JOB_SEARCH_DATE_FILTER_ENABLED=false` while tuning career-site coverage; enable it later if you want strict recency.
