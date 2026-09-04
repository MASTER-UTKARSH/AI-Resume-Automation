from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.model_router import model_router
from backend.app.core.event_bus import event_bus
from backend.app.database.session import get_db
from backend.app.database.models import User, Resume, Job, JobMatch, Workflow
from backend.app.services.vector_store import vector_store

router = APIRouter(prefix="/telemetry", tags=["Telemetry & Observability"])

@router.get("/health")
def get_system_health(db: Session = Depends(get_db)):
    """System health dashboard for model providers, vector store, and event bus."""
    counts = {
        "users": db.query(User).count(),
        "resumes": db.query(Resume).count(),
        "jobs": db.query(Job).count(),
        "matches_computed": db.query(JobMatch).count(),
        "workflows": db.query(Workflow).count()
    }

    return {
        "status": "OPERATIONAL",
        "model_providers": model_router.get_provider_health(),
        "event_bus": {
            "mode": "Redis" if event_bus.is_connected else "Async In-Memory Queue (Decoupled)",
            "recent_events_count": len(event_bus.get_history())
        },
        "vector_store": {
            "dimension": vector_store.dim,
            "jobs_indexed": vector_store.job_index.ntotal,
            "resumes_indexed": vector_store.resume_index.ntotal
        },
        "database_metrics": counts
    }

@router.get("/events")
def get_recent_events():
    """Recent event log from the event queue."""
    return {"recent_events": event_bus.get_history()}
