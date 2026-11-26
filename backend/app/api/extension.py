"""Extension Integration API & WebSocket Server
Connects the Clyde AI Multi-Agent backend to the Chrome Browser Extension.
Handles bi-directional event streaming, candidate profile delivery, and task orchestration.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db, SessionLocal
from backend.app.core.event_bus import event_bus
from backend.app.database.models import User, Resume, CandidateProfile, Application, Workflow, AgentRun

logger = logging.getLogger("ExtensionAPI")
router = APIRouter(prefix="/extension", tags=["Browser Extension"])

# In-memory registry for connected browser extensions
class ExtensionConnectionManager:
    def __init__(self):
        # Maps client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Maps client_id -> metadata (user_id, tab_info, connected_at)
        self.client_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect(self, client_id: str, websocket: WebSocket, metadata: Dict[str, Any]):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_metadata[client_id] = metadata
        logger.info(f"Extension client '{client_id}' connected. Active: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_metadata:
            del self.client_metadata[client_id]
        logger.info(f"Extension client '{client_id}' disconnected. Remaining: {len(self.active_connections)}")

    async def send_event(self, client_id: str, event_type: str, payload: Dict[str, Any], task_id: Optional[str] = None, workflow_id: Optional[str] = None):
        ws = self.active_connections.get(client_id)
        if ws:
            envelope = {
                "event_id": f"evt-{uuid.uuid4().hex[:12]}",
                "event_type": event_type,
                "workflow_id": workflow_id or f"wf-{uuid.uuid4().hex[:8]}",
                "task_id": task_id or f"tsk-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
                "correlation_id": str(uuid.uuid4())
            }
            await ws.send_text(json.dumps(envelope))
            logger.info(f"Dispatched event '{event_type}' to extension client '{client_id}'")
            return envelope
        else:
            logger.warning(f"Failed to dispatch: Client '{client_id}' not found.")
            return None

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        for cid in list(self.active_connections.keys()):
            await self.send_event(cid, event_type, payload)

extension_manager = ExtensionConnectionManager()

# ==========================================
# 1. Extension Auth & Candidate Profile Endpoints
# ==========================================

@router.get("/token")
def get_extension_token(user_id: str = "usr-utkarsh-241b278", db: Session = Depends(get_db)):
    """Issues a short-lived token for the Chrome Extension."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        user = db.query(User).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    token = f"ext_tok_{uuid.uuid4().hex}_{user.user_id}"
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "user_name": user.full_name,
        "expires_in_seconds": 3600
    }

@router.get("/candidate-profile")
def get_candidate_profile(user_id: str = "usr-utkarsh-241b278", db: Session = Depends(get_db)):
    """
    Returns normalized candidate profile fields for deterministic autofill by the Form Mapper.
    """
    user = db.query(User).filter_by(user_id=user_id).first()
    profile = db.query(CandidateProfile).filter_by(user_id=user_id).first()
    if not profile:
        profile = db.query(CandidateProfile).first()

    if not profile:
        raise HTTPException(status_code=404, detail="No candidate profile found")

    resume = db.query(Resume).filter_by(resume_id=profile.resume_id).first()

    first_name = ""
    last_name = ""
    if profile.full_name:
        parts = profile.full_name.split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    skills = [s.skill_name for s in profile.skills] if profile.skills else []
    education = [{
        "institution": e.institution,
        "degree": e.degree,
        "field_of_study": e.field_of_study,
        "graduation_year": e.graduation_year,
        "gpa": e.gpa
    } for e in profile.education] if profile.education else []

    experience = [{
        "company": exp.company,
        "role": exp.role,
        "start_date": exp.start_date,
        "end_date": exp.end_date,
        "description": exp.description
    } for exp in profile.experience] if profile.experience else []

    projects = [{
        "title": p.title,
        "technologies": p.technologies,
        "description": p.description,
        "link": p.link
    } for p in profile.projects] if profile.projects else []

    return {
        "candidate_id": profile.user_id,
        "full_name": profile.full_name or "Utkarsh Shah",
        "first_name": first_name or "Utkarsh",
        "last_name": last_name or "Shah",
        "email": profile.email or "utkarsh.shah@juetguna.in",
        "phone": profile.phone or "+91 98765 43210",
        "location": "Guna, Madhya Pradesh, India",
        "headline": profile.headline or "AI & Full-Stack Systems Engineer",
        "summary": profile.summary or "Computer Science student at Jaypee University of Engineering & Technology building agentic architectures.",
        "linkedin_url": "https://linkedin.com/in/utkarshshah-juet",
        "github_url": "https://github.com/utkarsh21",
        "portfolio_url": "https://utkarshshah.dev",
        "work_authorization": "Yes, legally authorized to work in India",
        "requires_sponsorship": "No",
        "education": education,
        "experience": experience,
        "skills": skills,
        "projects": projects,
        "active_resume": {
            "resume_id": profile.resume_id,
            "pdf_url": f"/api/resumes/{profile.resume_id}/pdf",
            "latex_url": f"/api/resumes/{profile.resume_id}/latex",
            "file_name": resume.file_name if resume else "Utkarsh_Shah_Resume.pdf"
        }
    }

# ==========================================
# 2. WebSocket Real-Time Automation Channel
# ==========================================

@router.websocket("/ws")
async def extension_websocket(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
):
    """
    WebSocket connection for the Browser Extension Background Service Worker.
    Streams execution plans, monitors DOM inspection, and confirms submission approvals.
    """
    cid = client_id or f"client-{uuid.uuid4().hex[:8]}"
    metadata = {
        "client_id": cid,
        "token": token,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "ip": websocket.client.host if websocket.client else "unknown"
    }

    await extension_manager.connect(cid, websocket, metadata)

    # Publish connection event to backend Event Bus
    await event_bus.publish("EXTENSION_CONNECTED", {
        "client_id": cid,
        "metadata": metadata
    })

    # Acknowledge connection
    welcome_event = {
        "event_id": f"evt-{uuid.uuid4().hex[:12]}",
        "event_type": "EXTENSION_CONNECTED_ACK",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "status": "AUTHENTICATED",
            "server": "Clyde AI Multi-Agent Automation Backend",
            "capabilities": ["INSPECT_PAGE", "FILL_FORM", "UPLOAD_RESUME", "UPLOAD_COVER_LETTER", "SUBMIT_APPLICATION"]
        }
    }
    await websocket.send_text(json.dumps(welcome_event))

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                event_data = json.loads(raw_text)
                event_type = event_data.get("event_type", "UNKNOWN")
                payload = event_data.get("payload", {})
                workflow_id = event_data.get("workflow_id", "wf-default")
                task_id = event_data.get("task_id", "tsk-default")

                logger.info(f"Received extension event '{event_type}' from '{cid}' (task: {task_id}): {payload}")

                # Forward event into system Event Bus
                await event_bus.publish(event_type, {
                    "client_id": cid,
                    "event_data": event_data
                })

                # Handle specific extension events
                if event_type == "HEALTH_CHECK":
                    await websocket.send_text(json.dumps({
                        "event_type": "HEALTH_CHECK_ACK",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "payload": {"status": "HEALTHY", "active_clients": len(extension_manager.active_connections)}
                    }))

                elif event_type == "PAGE_DETECTED":
                    logger.info(f"Extension detected supported job site: {payload.get('platform_name')} on {payload.get('url')}")

                elif event_type == "APPLICATION_READY":
                    logger.info(f"Application ready for approval. User action required. App ID: {payload.get('application_id')}")

                elif event_type == "APPLICATION_COMPLETED":
                    logger.info(f"Application successfully submitted! Confirmation: {payload.get('confirmation_number')}")

            except json.JSONDecodeError:
                logger.error("Malformed JSON payload received from extension.")
            except Exception as e:
                logger.error(f"Error processing extension event: {e}")

    except WebSocketDisconnect:
        extension_manager.disconnect(cid)
        await event_bus.publish("EXTENSION_DISCONNECTED", {"client_id": cid})
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}")
        extension_manager.disconnect(cid)

