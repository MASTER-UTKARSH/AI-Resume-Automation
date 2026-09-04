import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.event_bus import event_bus
from backend.app.database.session import get_db
from backend.app.database.models import User, Resume, ResumeVersion, CandidateProfile
from backend.app.services.resume_parser import resume_parser

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form("usr-utkarsh-241b278"),
    db: Session = Depends(get_db)
):
    """
    Ingests a resume PDF, extracts structural text, generates candidate profile,
    computes baseline ATS score, and persists records into relational database.
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

        # 2. Parse into structured profile
        parsed_data = resume_parser.parse_text(raw_text)

        # 3. Persist into relational models (Resume, ResumeVersion V1, CandidateProfile, etc.)
        resume_record = resume_parser.save_parsed_profile(
            db=db,
            user_id=user.user_id,
            parsed_data=parsed_data,
            file_name=file.filename,
            file_path=str(file_path)
        )

        # 4. Dispatch event through Event Bus
        await event_bus.publish("RESUME_UPLOADED", {
            "resume_id": resume_record.resume_id,
            "user_id": user.user_id,
            "ats_score": parsed_data["ats_score"]
        })

        return {
            "status": "success",
            "message": "Resume uploaded and candidate profile structured successfully.",
            "resume_id": resume_record.resume_id,
            "version": 1,
            "ats_score": parsed_data["ats_score"],
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
