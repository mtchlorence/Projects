import io
import PyPDF2
import pdfplumber
from typing import Optional, Dict, List, Tuple

SKILLS = [
    "python", "sql", "aws", "cloud", "cloud engineering",
    "devops", "lambda", "s3", "docker", "serverless",
    "kubernetes", "terraform", "linux", "git", "jenkins",
    "cloudwatch", "monitoring", "prometheus", "grafana", "power bi",
    "athena", "glue", "etl", "api", "ci/cd", "ansible",
    "jenkins", "azure", "gcp", "react", "angular",
    "node.js", "typescript", "javascript", "java", "c++",
    "postgresql", "mysql", "mongodb", "redis"
]

# ----- PDF Extraction Functions -----

def extract_text_from_pdf_pypdf2(file_bytes: bytes) -> str:
    """Extract text from PDF using PyPDF2 (faster, less accurate)"""
    try:
        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"PyPDF2 extraction failed: {str(e)}")

def extract_text_from_pdf_pdfplumber(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber (slower, more accurate)"""
    try:
        pdf_file = io.BytesIO(file_bytes)
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"pdfplumber extraction failed: {str(e)}")

def extract_text_from_pdf(file_bytes: bytes, method: str = "pdfplumber") -> str:
    """
    Extract text from PDF file bytes.
    
    Args:
        file_bytes: PDF file as bytes
        method: "pdfplumber" (default, more accurate) or "pypdf2" (faster)
    
    Returns:
        Extracted text as string
    """
    if method == "pypdf2":
        return extract_text_from_pdf_pypdf2(file_bytes)
    else:
        return extract_text_from_pdf_pdfplumber(file_bytes)

# ----- Analysis Functions -----

def analyze_resume_text(resume_text: str, job_description: str = "") -> Dict:
    """
    Analyze resume text against job description.
    
    Args:
        resume_text: Resume text content
        job_description: Job description text
    
    Returns:
        Dict with score, matched_skills, missing_skills
    """
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
        "missing_skills": sorted(missing_skills),
        "job_skills": sorted(job_skills),
        "resume_skills": sorted(resume_skills),
        "resume_text": resume_text,
    }

def analyze_resume(
    resume_source: str, 
    job_description: str = "",
    is_file: bool = False,
    file_bytes: Optional[bytes] = None
) -> Dict:
    """
    Main analysis function - handles both text and file input.
    
    Args:
        resume_source: Either text content or file path
        job_description: Job description text
        is_file: Whether resume_source is a file path
        file_bytes: File bytes (alternative to file path)
    
    Returns:
        Analysis results dict
    """
    if is_file:
        # Extract text from file
        if file_bytes is not None:
            resume_text = extract_text_from_pdf(file_bytes)
        else:
            raise ValueError("File bytes required when is_file=True")
    else:
        # Use text directly
        resume_text = resume_source
    
    return analyze_resume_text(resume_text, job_description)
