import logging
from sqlalchemy.orm import Session
from backend.app.database.models import User, Company, JobSource, Job, ProviderHealth
from backend.app.database.session import SessionLocal

logger = logging.getLogger("SeedData")

SAMPLE_USERS = [
    {
        "user_id": "usr-utkarsh-241b278",
        "email": "utkarsh.shah@juetguna.in",
        "full_name": "Utkarsh Shah"
    },
    {
        "user_id": "usr-utsav-241b279",
        "email": "utsav.kothari@juetguna.in",
        "full_name": "Utsav Kothari"
    },
    {
        "user_id": "usr-yashasv-241b295",
        "email": "yashasv.pandey@juetguna.in",
        "full_name": "Yashasv Pandey"
    }
]

SAMPLE_COMPANIES = [
    {"company_id": "comp-nvidia", "name": "NVIDIA", "industry": "AI & Semiconductors", "website": "https://nvidia.com"},
    {"company_id": "comp-google", "name": "Google", "industry": "Cloud & AI Search", "website": "https://google.com"},
    {"company_id": "comp-microsoft", "name": "Microsoft", "industry": "Enterprise Software & AI", "website": "https://microsoft.com"},
    {"company_id": "comp-razorpay", "name": "Razorpay", "industry": "FinTech & Payments", "website": "https://razorpay.com"},
    {"company_id": "comp-uber", "name": "Uber", "industry": "Mobility & Distributed Systems", "website": "https://uber.com"}
]

SAMPLE_SOURCES = [
    {"source_id": "src-career-portal", "name": "Company Career Portal", "type": "CareerPage"},
    {"source_id": "src-linkedin", "name": "LinkedIn Jobs Adapter", "type": "Platform"},
    {"source_id": "src-internshala", "name": "Internshala API", "type": "API"}
]

SAMPLE_JOBS = [
    {
        "job_id": "job-nv-ai-intern",
        "company_id": "comp-nvidia",
        "source_id": "src-career-portal",
        "title": "AI & Deep Learning Software Engineer Intern",
        "experience_level": "Fresher / Entry-Level",
        "location": "Bangalore / Hybrid",
        "description": "NVIDIA is seeking an enthusiastic AI Systems Intern to optimize inference pipelines and work on LLM model acceleration. Candidates should have a strong foundation in Python, PyTorch, C++, and vector retrieval systems (FAISS/Milvus). You will build high-throughput microservices and evaluate quantization algorithms.",
        "required_skills": ["Python", "PyTorch", "FAISS", "CUDA", "FastAPI", "Docker", "Git", "REST APIs"],
        "job_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/AI-Intern"
    },
    {
        "job_id": "job-goog-swe-intern",
        "company_id": "comp-google",
        "source_id": "src-career-portal",
        "title": "Software Engineering Intern - Cloud & Distributed Systems",
        "experience_level": "Fresher / Entry-Level",
        "location": "Bangalore / Hyderabad",
        "description": "Google Cloud infrastructure teams are hiring software interns. You will design, develop, and test scalable distributed backend services. Qualifications include proficiency in Python or Go, algorithms and data structures, SQL databases, and asynchronous message queues.",
        "required_skills": ["Python", "Go", "Distributed Systems", "SQL", "PostgreSQL", "Redis", "Data Structures", "Algorithms"],
        "job_url": "https://careers.google.com/jobs/results/swe-intern-2026"
    },
    {
        "job_id": "job-msft-ml-intern",
        "company_id": "comp-microsoft",
        "source_id": "src-linkedin",
        "title": "Machine Learning Research Intern - Applied AI",
        "experience_level": "Fresher / Entry-Level",
        "location": "Noida / Remote",
        "description": "Microsoft Applied Sciences group is looking for an ML Intern to explore multi-agent LLM systems and retrieval-augmented generation (RAG). Core skills: Python, LangChain/LlamaIndex, FAISS vector embeddings, HuggingFace Transformers, and prompt engineering.",
        "required_skills": ["Python", "Machine Learning", "FAISS", "RAG", "NLP", "Transformers", "PyTorch", "Vector Databases"],
        "job_url": "https://careers.microsoft.com/us/en/job/1789421/ML-Intern"
    },
    {
        "job_id": "job-rzp-backend-intern",
        "company_id": "comp-razorpay",
        "source_id": "src-internshala",
        "title": "Backend Engineering Intern - Payments Core",
        "experience_level": "Fresher / Entry-Level",
        "location": "Bangalore",
        "description": "Join Razorpay's high-throughput payment processing engineering group. Responsibilities include implementing robust RESTful endpoints with FastAPI/Flask, handling relational schema migrations in PostgreSQL, and maintaining Redis caching layers.",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "REST APIs", "Microservices", "Docker"],
        "job_url": "https://razorpay.com/jobs/backend-intern"
    },
    {
        "job_id": "job-uber-fullstack-intern",
        "company_id": "comp-uber",
        "source_id": "src-career-portal",
        "title": "Full Stack Software Engineering Intern",
        "experience_level": "Fresher / Entry-Level",
        "location": "Bangalore",
        "description": "Uber is looking for Full Stack Engineering Interns to build internal operator tools and telemetry dashboards. Work with TypeScript, React, Tailwind CSS on the frontend, and Node.js or Python FastAPI services on the backend.",
        "required_skills": ["React", "TypeScript", "Python", "FastAPI", "Tailwind CSS", "JavaScript", "SQL", "Git"],
        "job_url": "https://uber.com/careers/jobs/fullstack-intern"
    }
]

def seed_database(db: Session):
    """Populates database with essential reference data if empty."""
    # 1. Users
    for u_data in SAMPLE_USERS:
        existing = db.query(User).filter_by(user_id=u_data["user_id"]).first()
        if not existing:
            db.add(User(**u_data))
    
    # 2. Companies
    for c_data in SAMPLE_COMPANIES:
        existing = db.query(Company).filter_by(company_id=c_data["company_id"]).first()
        if not existing:
            db.add(Company(**c_data))

    # 3. Sources
    for s_data in SAMPLE_SOURCES:
        existing = db.query(JobSource).filter_by(source_id=s_data["source_id"]).first()
        if not existing:
            db.add(JobSource(**s_data))

    db.commit()

    # 4. Jobs
    for j_data in SAMPLE_JOBS:
        existing = db.query(Job).filter_by(job_id=j_data["job_id"]).first()
        if not existing:
            db.add(Job(**j_data))

    # 5. Model Providers Health
    providers = ["GLM", "Qwen", "Groq", "Ollama"]
    for p in providers:
        existing = db.query(ProviderHealth).filter_by(provider_name=p).first()
        if not existing:
            db.add(ProviderHealth(
                provider_name=p,
                status="HEALTHY",
                latency=45.0 if p == "Groq" else 120.0
            ))

    db.commit()
    logger.info("Database seeding verified successfully.")

if __name__ == "__main__":
    db = SessionLocal()
    seed_database(db)
    db.close()
