SKILLS = [
    "python",
    "sql",
    "aws",
    "lambda",
    "s3",
    "docker",
    "kubernetes",
    "terraform",
    "linux",
    "git",
    "jenkins",
    "cloudwatch",
    "prometheus",
    "grafana",
    "power bi",
    "athena",
    "glue",
    "api",
    "ci/cd"
]

def analyze_resume(resume_text, job_description):
    resume_text = resume_text.lower()
    job_description = job_description.lower()

    resume_skills = [
        skill for skill in SKILLS
        if skill in resume_text
    ]

    job_skills = [
        skill for skill in SKILLS
        if skill in job_description
    ]

    matched_skills = list(
        set(resume_skills).intersection(job_skills)
    )

    missing_skills = list(
        set(job_skills) - set(resume_skills)
    )

    score = 0

    if len(job_skills) > 0:
        score = round(
            (len(matched_skills) / len(job_skills)) * 100,
            2
        )

    return {
        "score": score,
        "matched_skills": sorted(matched_skills),
        "missing_skills": sorted(missing_skills)
    }