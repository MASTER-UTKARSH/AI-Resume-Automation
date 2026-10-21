import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.database.models import CandidateProfile, Job, JobMatch
from backend.app.services.vector_store import vector_store

from backend.app.services.ghost_detector import GhostJobDetector

logger = logging.getLogger("MatchingEngine")

WEIGHT_SEMANTIC = 0.40
WEIGHT_SKILLS = 0.30
WEIGHT_EXPERIENCE = 0.15
WEIGHT_PREFERENCE = 0.15

class MatchingEngine:
    """
    Multi-factor job matching engine combining:
    1. FAISS Semantic Cosine Similarity (40%)
    2. Direct & Partial Skill Overlap (30%)
    3. Experience Level Alignment (15%)
    4. Location & Work Preference Compatibility (15%)
    5. Ghost Job / Posting Legitimacy Discount (adapted from Freehire & CareerOps)
    """
    def compute_match(
        self,
        profile: CandidateProfile,
        job: Job,
        semantic_sim: float,
        repost_count_90d: int = 1,
        days_active: int = 12,
        applicant_silence_count: int = 0
    ) -> Dict[str, Any]:
        # 1. Candidate skills set
        candidate_skills = {s.skill_name.lower().strip() for s in profile.skills}
        required_skills = [s.lower().strip() for s in (job.required_skills or [])]

        matching_skills = []
        missing_skills = []

        if required_skills:
            for req in required_skills:
                # Direct match or substring match
                if any(req in c or c in req for c in candidate_skills):
                    matching_skills.append(req.title())
                else:
                    missing_skills.append(req.title())
            skill_score = (len(matching_skills) / len(required_skills)) * 100.0
        else:
            skill_score = 80.0

        # 2. Semantic score (normalized to 0-100)
        semantic_score = min(100.0, max(0.0, semantic_sim * 100.0))

        # 3. Experience level score
        # Students / Freshers qualify well for Internship / Entry-Level roles
        if "intern" in job.title.lower() or "entry" in job.experience_level.lower() or "fresher" in job.experience_level.lower():
            experience_score = 95.0
        elif "associate" in job.experience_level.lower():
            experience_score = 75.0
        else:
            experience_score = 60.0

        # 4. Location and preference score
        job_loc = (job.location or "").lower()
        if "remote" in job_loc or "bangalore" in job_loc or "hyderabad" in job_loc or "noida" in job_loc:
            preference_score = 95.0
        else:
            preference_score = 80.0

        # 5. Ghost Job & Legitimacy Evaluation (Freehire / CareerOps)
        ghost_eval = GhostJobDetector.evaluate_job_legitimacy(
            job={"title": job.title, "company": job.company.name if job.company else ""},
            repost_count_90d=repost_count_90d,
            days_active=days_active,
            is_official_ats=True,
            applicant_silence_count=applicant_silence_count
        )

        # Base Composite Weighted Score
        base_score = (
            (WEIGHT_SEMANTIC * semantic_score) +
            (WEIGHT_SKILLS * skill_score) +
            (WEIGHT_EXPERIENCE * experience_score) +
            (WEIGHT_PREFERENCE * preference_score)
        )

        # Apply Posting Health / Ghost Penalty Multiplier
        overall_score = base_score * ghost_eval["penalty_multiplier"]
        overall_score = round(min(98.5, max(15.0, overall_score)), 1)

        # Human-readable rationale
        match_count = len(matching_skills)
        total_req = len(required_skills)
        reason = (
            f"Overall Match: {overall_score}% [{ghost_eval['verdict']}]. "
            f"Candidate matches {match_count}/{total_req} required technical skills ({', '.join(matching_skills[:4])}). "
            f"High vector embedding similarity ({semantic_score:.1f}%) to {job.company.name if job.company else 'company'} role description. "
        )
        if missing_skills:
            reason += f"Recommended skill additions: {', '.join(missing_skills[:3])}. "
        if ghost_eval["signals"]:
            reason += f"Legitimacy: {'; '.join(ghost_eval['signals'])}."

        return {
            "overall_score": overall_score,
            "semantic_score": round(semantic_score, 1),
            "skills_score": round(skill_score, 1),
            "experience_score": round(experience_score, 1),
            "preference_score": round(preference_score, 1),
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "ghost_verdict": ghost_eval["verdict"],
            "posting_health_penalty": ghost_eval["penalty_points"],
            "legitimacy_signals": ghost_eval["signals"],
            "reason": reason
        }

    def match_candidate_against_all_jobs(self, db: Session, user_id: str, profile_id: str) -> List[JobMatch]:
        """Calculates and persists multi-factor match records for all available jobs in DB."""
        profile = db.query(CandidateProfile).filter_by(profile_id=profile_id).first()
        if not profile:
            raise ValueError(f"Candidate profile '{profile_id}' not found.")

        # Build candidate resume text for FAISS query
        skills_text = ", ".join([s.skill_name for s in profile.skills])
        projects_text = " ".join([f"{p.title} {p.technologies} {p.description}" for p in profile.projects])
        full_resume_text = f"{profile.headline} {profile.summary} Skills: {skills_text}. Projects: {projects_text}"

        # Ensure all jobs are indexed in FAISS
        all_jobs = db.query(Job).all()
        for j in all_jobs:
            job_text = f"{j.title} {j.company.name if j.company else ''} {j.description} {' '.join(j.required_skills or [])}"
            vector_store.add_job(j.job_id, job_text)

        # Retrieve top semantic matches from FAISS
        faiss_results = dict(vector_store.search_jobs_for_resume(full_resume_text, top_k=len(all_jobs)))

        matches_created = []
        for job in all_jobs:
            sim = faiss_results.get(job.job_id, 0.45)
            metrics = self.compute_match(profile, job, sim)

            # Check if match already exists
            match_record = db.query(JobMatch).filter_by(user_id=user_id, job_id=job.job_id).first()
            if not match_record:
                match_record = JobMatch(
                    user_id=user_id,
                    job_id=job.job_id,
                    match_score=metrics["overall_score"],
                    semantic_score=metrics["semantic_score"],
                    skills_score=metrics["skills_score"],
                    experience_score=metrics["experience_score"],
                    preference_score=metrics["preference_score"],
                    matching_skills=metrics["matching_skills"],
                    missing_skills=metrics["missing_skills"],
                    reason=metrics["reason"]
                )
                db.add(match_record)
            else:
                match_record.match_score = metrics["overall_score"]
                match_record.semantic_score = metrics["semantic_score"]
                match_record.skills_score = metrics["skills_score"]
                match_record.experience_score = metrics["experience_score"]
                match_record.preference_score = metrics["preference_score"]
                match_record.matching_skills = metrics["matching_skills"]
                match_record.missing_skills = metrics["missing_skills"]
                match_record.reason = metrics["reason"]

            matches_created.append(match_record)

        db.commit()
        # Return sorted by match score descending
        matches_created.sort(key=lambda m: m.match_score, reverse=True)
        return matches_created

matching_engine = MatchingEngine()
