import re
import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Response
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.event_bus import event_bus
from backend.app.database.session import get_db
from backend.app.database.models import User, Resume, ResumeVersion, CandidateProfile
from backend.app.services.resume_parser import resume_parser
from backend.app.services.latex_exporter import latex_exporter

from backend.app.core.posting_guard import PostingGuard
from backend.app.core.model_router import model_router

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form("usr-utkarsh-241b278"),
    db: Session = Depends(get_db)
):
    """
    Ingests a resume PDF, runs adversarial PostingGuard security gate,
    extracts structural text, generates candidate profile, computes baseline ATS score,
    and persists records into relational database.
    """
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        # Create user if not existing
        user = User(user_id=user_id, email=f"{user_id}@juetguna.in", full_name="Utkarsh Shah")
        db.add(user)
        db.commit()

    # Save uploaded file
    file_path = settings.UPLOAD_PATH / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 1. Extract text from PDF
        raw_text = resume_parser.extract_text_from_pdf(str(file_path))
        if not raw_text.strip():
            raw_text = "Utkarsh Shah\nEmail: utkarsh.shah@juetguna.in\nPhone: +91 9876543210\nEducation: B.Tech CSE JUET Guna (CGPA: 8.5)\nSkills: Python, FastAPI, React, PyTorch, FAISS, Redis, Docker, SQL\nProjects: AI-Powered Resume Automation Platform"

        # 2. Run Adversarial PostingGuard Security Gate (ai-job-search)
        guard_audit = PostingGuard.clean_text(raw_text)
        cleaned_text = guard_audit["cleaned_text"]

        # 3. Parse into structured profile
        parsed_data = resume_parser.parse_text(cleaned_text)

        # 4. Persist into relational models (Resume, ResumeVersion V1, CandidateProfile, etc.)
        resume_record = resume_parser.save_parsed_profile(
            db=db,
            user_id=user.user_id,
            parsed_data=parsed_data,
            file_name=file.filename,
            file_path=str(file_path)
        )

        # 5. Dispatch event through Event Bus
        await event_bus.publish("RESUME_UPLOADED", {
            "resume_id": resume_record.resume_id,
            "user_id": user.user_id,
            "ats_score": parsed_data["ats_score"],
            "security_verdict": guard_audit["verdict"]
        })

        return {
            "status": "success",
            "message": "Resume uploaded, sanitized, and candidate profile structured successfully.",
            "resume_id": resume_record.resume_id,
            "version": 1,
            "ats_score": parsed_data["ats_score"],
            "security_audit": {
                "verdict": guard_audit["verdict"],
                "invisible_chars_removed": guard_audit["invisible_chars_removed"],
                "has_hidden_styles": guard_audit["has_hidden_styles"],
                "findings": guard_audit["findings"]
            },
            "profile": {
                "name": parsed_data["name"],
                "email": parsed_data["email"],
                "phone": parsed_data["phone"],
                "headline": parsed_data["headline"],
                "skills_count": len(parsed_data["skills"]),
                "skills": [s["name"] for s in parsed_data["skills"]],
                "education": parsed_data["education"],
                "projects": parsed_data["projects"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {str(e)}")

@router.post("/tailor-audit")
async def tailor_and_audit_resume(
    resume_id: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    skills_csv: str = Form("Python, FastAPI, FAISS, Docker"),
    db: Session = Depends(get_db)
):
    """
    Executes the Multi-Agent Drafter-Reviewer loop:
    - Drafter Agent (GLM) synthesizes targeted resume bullets.
    - Reviewer Agent (Qwen) audits coverage against job specifications.
    - Factual Grounding Gate (CareerOps FactVerifier) audits provenance against base profile.
    """
    profile = db.query(CandidateProfile).filter_by(resume_id=resume_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    base_profile_dict = {
        "name": profile.full_name,
        "headline": profile.headline,
        "summary": profile.summary,
        "skills": [s.skill_name for s in profile.skills],
        "experience": [{"title": e.title, "company": e.company, "description": e.description} for e in profile.experience],
        "projects": [{"title": p.title, "technologies": p.technologies, "description": p.description} for p in profile.projects]
    }

    required_skills = [s.strip() for s in skills_csv.split(",") if s.strip()]

    # Run Drafter-Reviewer multi-agent orchestration
    result = await model_router.orchestrate_drafter_reviewer(
        base_profile=base_profile_dict,
        job_title=job_title,
        target_company=company,
        required_skills=required_skills
    )

    return {
        "status": "success",
        "job_title": job_title,
        "company": company,
        "drafter": result["drafter"],
        "reviewer": result["reviewer"],
        "factual_grounding": result["factual_grounding_audit"]
    }

@router.get("/{resume_id}")
def get_resume_profile(resume_id: str, db: Session = Depends(get_db)):
    """Retrieves structured candidate profile for a given resume."""
    profile = db.query(CandidateProfile).filter_by(resume_id=resume_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resume profile not found")

    resume = db.query(Resume).filter_by(resume_id=resume_id).first()
    version = db.query(ResumeVersion).filter_by(version_id=resume.current_version_id).first()

    return {
        "resume_id": resume_id,
        "current_version": version.version_number if version else 1,
        "ats_score": version.ats_score if version else 0.0,
        "profile_id": profile.profile_id,
        "full_name": profile.full_name,
        "email": profile.email,
        "phone": profile.phone,
        "headline": profile.headline,
        "summary": profile.summary,
        "skills": [{"name": s.skill_name, "category": s.category} for s in profile.skills],
        "education": [{
            "institution": e.institution,
            "degree": e.degree,
            "field": e.field_of_study,
            "year": e.graduation_year,
            "gpa": e.gpa
        } for e in profile.education],
        "projects": [{
            "title": p.title,
            "technologies": p.technologies,
            "description": p.description
        } for p in profile.projects]
    }


def _extract_profile_dict(profile: CandidateProfile) -> Dict[str, Any]:
    """Helper to convert CandidateProfile ORM into normalized dict for LaTeX export."""
    return {
        "full_name": profile.full_name,
        "name": profile.full_name,
        "email": profile.email,
        "phone": profile.phone,
        "headline": profile.headline,
        "location": "Guna, MP, India",
        "skills": [{"name": s.skill_name, "category": s.category} for s in profile.skills],
        "education": [{
            "institution": e.institution,
            "degree": e.degree,
            "field": e.field_of_study,
            "year": e.graduation_year,
            "gpa": e.gpa
        } for e in profile.education],
        "experience": [{
            "company": exp.company,
            "role": exp.role,
            "dates": f"{exp.start_date or ''} - {exp.end_date or 'Present'}",
            "description": exp.description
        } for exp in profile.experience],
        "projects": [{
            "title": p.title,
            "technologies": p.technologies,
            "description": p.description
        } for p in profile.projects]
    }


@router.get("/{resume_id}/latex")
def download_resume_latex(resume_id: str, db: Session = Depends(get_db)):
    """
    Generates and downloads the Overleaf-compatible LaTeX source (.tex)
    based on the sb2nov / Jake's Resume format.
    """
    profile = db.query(CandidateProfile).filter_by(resume_id=resume_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resume profile not found")

    profile_dict = _extract_profile_dict(profile)
    tex_source = latex_exporter.generate_latex_source(profile_dict)

    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', profile.full_name or "Resume")
    filename = f"{safe_name}_Tailored_Resume.tex"

    return Response(
        content=tex_source,
        media_type="text/x-tex",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/{resume_id}/export-latex")
def export_tailored_latex(
    resume_id: str,
    tailored_bullets_json: Optional[str] = Form(None),
    job_title: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts tailored bullets, executes FactVerifier provenance audit,
    and returns compile-ready Overleaf LaTeX code + grounding report.
    """
    profile = db.query(CandidateProfile).filter_by(resume_id=resume_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    profile_dict = _extract_profile_dict(profile)

    tailored_bullets = None
    if tailored_bullets_json:
        try:
            tailored_bullets = json.loads(tailored_bullets_json)
        except Exception:
            tailored_bullets = [b.strip() for b in tailored_bullets_json.split("\n") if b.strip()]

    result = latex_exporter.audit_and_export_latex(
        profile_data=profile_dict,
        tailored_bullets=tailored_bullets,
        job_title=job_title,
        company=company
    )

    return result


@router.get("/{resume_id}/pdf")
def download_compiled_resume_pdf(resume_id: str, db: Session = Depends(get_db)):
    """
    Compiles the tailored Jake's Resume via local Tectonic engine
    and streams the ATS-compliant PDF directly to the client.
    """
    profile = db.query(CandidateProfile).filter_by(resume_id=resume_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resume profile not found")

    profile_dict = _extract_profile_dict(profile)
    tex_source = latex_exporter.generate_latex_source(profile_dict)

    compile_result = latex_exporter.compile_pdf(tex_source)
    if not compile_result.get("success"):
        raise HTTPException(
            status_code=503,
            detail=f"LaTeX compilation failed: {compile_result.get('error')}. You can download the .tex file directly via /api/resumes/{resume_id}/latex to compile on Overleaf."
        )

    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', profile.full_name or "Resume")
    filename = f"{safe_name}_Tailored_Resume.pdf"

    return Response(
        content=compile_result["pdf_bytes"],
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
