from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.core.event_bus import event_bus
from backend.app.database.session import get_db
from backend.app.database.models import Job, JobMatch, CandidateProfile, Company
from backend.app.services.matching_engine import matching_engine

router = APIRouter(prefix="/jobs", tags=["Jobs & Semantic Matching"])

class MatchRequest(BaseModel):
    user_id: str
    resume_id: str

@router.get("")
def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists discovered job postings across company portals and job boards."""
    jobs = db.query(Job).limit(limit).all()
    results = []
    for j in jobs:
        results.append({
            "job_id": j.job_id,
            "title": j.title,
            "company": j.company.name if j.company else "Tech Company",
            "industry": j.company.industry if j.company else "Software",
            "location": j.location,
            "experience_level": j.experience_level,
            "required_skills": j.required_skills or [],
            "description": j.description,
            "job_url": j.job_url
        })
    return {"total": len(results), "jobs": results}

@router.post("/match")
async def match_jobs(request: MatchRequest, db: Session = Depends(get_db)):
    """
    Executes Week 7 FAISS semantic retrieval + 4-factor matching algorithm:
    1. FAISS Cosine Similarity (40%)
    2. Skills Overlap (30%)
    3. Experience Level (15%)
    4. Location / Preference (15%)
    """
    profile = db.query(CandidateProfile).filter_by(resume_id=request.resume_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found for this resume_id")

    try:
        ranked_matches = matching_engine.match_candidate_against_all_jobs(
            db=db,
            user_id=request.user_id,
            profile_id=profile.profile_id
        )

        await event_bus.publish("MATCHES_COMPUTED", {
            "user_id": request.user_id,
            "resume_id": request.resume_id,
            "total_matches": len(ranked_matches),
            "top_score": ranked_matches[0].match_score if ranked_matches else 0.0
        })

        results = []
        for m in ranked_matches:
            job = m.job
            results.append({
                "match_id": m.match_id,
                "job_id": job.job_id,
                "title": job.title,
                "company": job.company.name if job.company else "Tech Company",
                "location": job.location,
                "overall_score": m.match_score,
                "breakdown": {
                    "semantic_similarity": m.semantic_score,
                    "skills_match": m.skills_score,
                    "experience_alignment": m.experience_score,
                    "preference_fit": m.preference_score
                },
                "matching_skills": m.matching_skills,
                "missing_skills": m.missing_skills,
                "reason": m.reason,
                "job_url": job.job_url
            })

        return {
            "status": "success",
            "candidate_name": profile.full_name,
            "total_matches": len(results),
            "matches": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job matching error: {str(e)}")
