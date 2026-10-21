"""Live Job Ingestion & Web Scraper Service
Adapted from ai-job-search/tools/fetch_page.py and freehire/harvest/ for Minor Project 1.

Fetches live job postings from Greenhouse, Lever, Ashby, and corporate career pages,
pipes them through PostingGuard to neutralize prompt injections and hidden CSS,
and extracts structured requirements for FAISS vector indexing.
"""

import re
import html
import logging
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.core.posting_guard import PostingGuard
from backend.app.database.models import Job, Company, JobSource
from backend.app.services.vector_store import vector_store

logger = logging.getLogger("JobScraper")

SKILL_LEXICON = [
    "Python", "FastAPI", "React", "TypeScript", "JavaScript", "PyTorch", "TensorFlow",
    "FAISS", "Redis", "Docker", "Kubernetes", "SQL", "PostgreSQL", "MongoDB",
    "Go", "Java", "C++", "C", "Rust", "AWS", "GCP", "Linux", "Git", "REST APIs",
    "GraphQL", "CUDA", "Microservices", "Next.js", "Pandas", "Scikit-Learn"
]

class JobScraperService:
    @staticmethod
    async def fetch_and_clean_posting(url: str) -> Dict[str, Any]:
        """Fetches raw web posting and strips adversarial payloads using PostingGuard."""
        import httpx

        # Validate host provenance
        host_info = PostingGuard.verify_source_host(url)

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                raw_html = resp.text
        except Exception as e:
            logger.error(f"Failed to fetch job URL '{url}': {e}")
            raise ValueError(f"Could not reach job URL: {str(e)}")

        # 1. Strip script, style, and noscript blocks
        clean_html = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw_html, flags=re.I | re.S)

        # 2. Extract plain text from HTML
        plain_text = re.sub(r"<[^>]+>", " ", clean_html)
        plain_text = html.unescape(plain_text)
        plain_text = re.sub(r"\s+", " ", plain_text).strip()

        # 3. Pipe through Adversarial PostingGuard
        guard_audit = PostingGuard.clean_text(plain_text)
        cleaned_text = guard_audit["cleaned_text"]

        # 4. Extract Structured Job Attributes
        title = JobScraperService._extract_title(clean_html, cleaned_text, url)
        company = JobScraperService._extract_company(clean_html, url)
        skills = JobScraperService._extract_skills(cleaned_text)
        exp_level = "Internship" if any(w in cleaned_text.lower() for w in ["intern", "fresher", "entry"]) else "Associate"

        return {
            "url": url,
            "host_verification": host_info,
            "security_verdict": guard_audit["verdict"],
            "security_findings": guard_audit["findings"],
            "title": title,
            "company": company,
            "required_skills": skills,
            "experience_level": exp_level,
            "description_snippet": cleaned_text[:500] + "...",
            "raw_text_length": len(cleaned_text)
        }

    @staticmethod
    def _extract_title(raw_html: str, text: str, url: str) -> str:
        # Check <title> tag
        m = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.I)
        if m:
            t = m.group(1).split("-")[0].split("|")[0].split("at")[0].strip()
            if 3 < len(t) < 70:
                return t
        
        # Check <h1>
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", raw_html, re.I)
        if h1:
            clean_h1 = re.sub(r"<[^>]+>", "", h1.group(1)).strip()
            if 3 < len(clean_h1) < 70:
                return clean_h1

        return "Software Engineer"

    @staticmethod
    def _extract_company(raw_html: str, url: str) -> str:
        domain = urlparse(url).hostname or ""
        parts = domain.split(".")
        if len(parts) >= 2:
            base = parts[-2].title()
            if base in ["Greenhouse", "Lever", "Ashbyhq", "Workday"]:
                # Subdomain usually holds company name
                return parts[0].title()
            return base
        return "Tech Employer"

    @staticmethod
    def _extract_skills(text: str) -> List[str]:
        found = []
        lower_t = text.lower()
        for s in SKILL_LEXICON:
            if re.search(rf"\b{re.escape(s.lower())}\b", lower_t):
                found.append(s)
        return found[:8] if found else ["Python", "REST APIs", "Git"]

    @classmethod
    def save_and_index_scraped_job(cls, db: Session, parsed_job: Dict[str, Any]) -> Job:
        """Persists the sanitized job into SQLAlchemy models and indexes into FAISS."""
        # Find or create company
        comp = db.query(Company).filter_by(name=parsed_job["company"]).first()
        if not comp:
            comp = Company(
                name=parsed_job["company"],
                domain=urlparse(parsed_job["url"]).hostname or "tech.com",
                industry="Software & AI"
            )
            db.add(comp)
            db.commit()

        # Find or create job
        job = db.query(Job).filter_by(job_url=parsed_job["url"]).first()
        if not job:
            job = Job(
                company_id=comp.company_id,
                title=parsed_job["title"],
                description=parsed_job["description_snippet"],
                experience_level=parsed_job["experience_level"],
                location="Bangalore / Hybrid",
                required_skills=parsed_job["required_skills"],
                job_url=parsed_job["url"],
                is_active=True
            )
            db.add(job)
            db.commit()

        # Index in FAISS
        job_text = f"{job.title} {comp.name} {job.description} {' '.join(job.required_skills or [])}"
        vector_store.add_job(job.job_id, job_text)

        return job

job_scraper = JobScraperService()
