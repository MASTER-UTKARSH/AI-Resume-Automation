import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey, DateTime, JSON, Boolean
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

# ==========================================
# 1. Identity Domain
# ==========================================
class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    job_matches = relationship("JobMatch", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")

# ==========================================
# 2. Resume & Candidate Profile Domain
# ==========================================
class Resume(Base):
    __tablename__ = "resumes"

    resume_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    original_file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    current_version_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="resumes")
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")
    profiles = relationship("CandidateProfile", back_populates="resume", cascade="all, delete-orphan")

class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    version_id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.resume_id"), nullable=False)
    version_number = Column(Integer, default=1)
    resume_content = Column(JSON, nullable=False)  # Full structured JSON content
    ats_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="versions")

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    profile_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    resume_id = Column(String(36), ForeignKey("resumes.resume_id"), nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    headline = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="profiles")
    skills = relationship("CandidateSkill", back_populates="profile", cascade="all, delete-orphan")
    education = relationship("CandidateEducation", back_populates="profile", cascade="all, delete-orphan")
    experience = relationship("CandidateExperience", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("CandidateProject", back_populates="profile", cascade="all, delete-orphan")

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    skill_id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.profile_id"), nullable=False)
    skill_name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), default="Technical")
    confidence_score = Column(Float, default=1.0)

    profile = relationship("CandidateProfile", back_populates="skills")

class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    edu_id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.profile_id"), nullable=False)
    institution = Column(String(255), nullable=False)
    degree = Column(String(100), nullable=True)
    field_of_study = Column(String(100), nullable=True)
    graduation_year = Column(String(20), nullable=True)
    gpa = Column(String(20), nullable=True)

    profile = relationship("CandidateProfile", back_populates="education")

class CandidateExperience(Base):
    __tablename__ = "candidate_experience"

    exp_id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.profile_id"), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    profile = relationship("CandidateProfile", back_populates="experience")

class CandidateProject(Base):
    __tablename__ = "candidate_projects"

    project_id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.profile_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(String(500), nullable=True)
    link = Column(String(500), nullable=True)

    profile = relationship("CandidateProfile", back_populates="projects")

# ==========================================
# 3. Job Domain
# ==========================================
class Company(Base):
    __tablename__ = "companies"

    company_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    website = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)

    jobs = relationship("Job", back_populates="company")

class JobSource(Base):
    __tablename__ = "job_sources"

    source_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # API, CareerPage, Platform

    jobs = relationship("Job", back_populates="source")

class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.company_id"), nullable=False)
    source_id = Column(String(36), ForeignKey("job_sources.source_id"), nullable=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)  # List of strings
    experience_level = Column(String(50), default="Fresher / Entry-Level")
    location = Column(String(100), default="Remote / Bangalore")
    job_url = Column(String(500), nullable=True)
    posted_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="jobs")
    source = relationship("JobSource", back_populates="jobs")
    matches = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")

class JobMatch(Base):
    __tablename__ = "job_matches"

    match_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    match_score = Column(Float, nullable=False)
    semantic_score = Column(Float, default=0.0)
    skills_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    preference_score = Column(Float, default=0.0)
    matching_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="job_matches")
    job = relationship("Job", back_populates="matches")

# ==========================================
# 4. Application Domain
# ==========================================
class CoverLetter(Base):
    __tablename__ = "cover_letters"

    cover_letter_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Application(Base):
    __tablename__ = "applications"

    application_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    resume_version_id = Column(String(36), ForeignKey("resume_versions.version_id"), nullable=True)
    cover_letter_id = Column(String(36), ForeignKey("cover_letters.cover_letter_id"), nullable=True)
    status = Column(String(50), default="Saved")  # Saved, Ready, Applied, Interview, Rejected, Accepted
    applied_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="applications")
    events = relationship("ApplicationEvent", back_populates="application", cascade="all, delete-orphan")

class ApplicationEvent(Base):
    __tablename__ = "application_events"

    event_id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.application_id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    details = Column(JSON, nullable=True)

    application = relationship("Application", back_populates="events")

# ==========================================
# 5. Agent & Telemetry Domain
# ==========================================
class Workflow(Base):
    __tablename__ = "workflows"

    workflow_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    status = Column(String(50), default="RUNNING")
    current_step = Column(String(100), nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="workflows")
    agent_runs = relationship("AgentRun", back_populates="workflow", cascade="all, delete-orphan")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    agent_run_id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.workflow_id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(50), default="SUCCESS")
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    error_message = Column(Text, nullable=True)

    workflow = relationship("Workflow", back_populates="agent_runs")

class ProviderHealth(Base):
    __tablename__ = "provider_health"

    provider_id = Column(String(36), primary_key=True, default=generate_uuid)
    provider_name = Column(String(50), nullable=False, unique=True)
    status = Column(String(50), default="HEALTHY")
    latency = Column(Float, default=0.0)
    last_checked = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class EmbeddingReference(Base):
    __tablename__ = "embedding_references"

    ref_id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False)  # 'resume' or 'job'
    entity_id = Column(String(36), nullable=False)
    faiss_index_id = Column(Integer, nullable=False)
