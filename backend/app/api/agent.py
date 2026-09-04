from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.core.model_router import model_router
from backend.app.core.event_bus import event_bus
from backend.app.database.session import get_db
from backend.app.database.models import Workflow, AgentRun

router = APIRouter(prefix="/agent", tags=["AI Agent & Orchestration"])

class AgentChatRequest(BaseModel):
    user_id: str
    message: str
    task_type: str = "general" # writing, reasoning, fast, general
    workflow_id: str = None

@router.post("/chat")
async def chat_with_agent(req: AgentChatRequest, db: Session = Depends(get_db)):
    """
    Clyde AI Career Copilot chat endpoint:
    Orchestrates user instructions, routes tasks through Model Router, 
    and logs agent execution telemetry into the database.
    """
    # 1. Manage Workflow State
    wf_id = req.workflow_id
    if not wf_id:
        wf = Workflow(
            user_id=req.user_id,
            status="ACTIVE",
            current_step=f"Handling: '{req.message[:30]}...'"
        )
        db.add(wf)
        db.commit()
        wf_id = wf.workflow_id
    else:
        wf = db.query(Workflow).filter_by(workflow_id=wf_id).first()
        if wf:
            wf.current_step = f"Executing: '{req.message[:30]}...'"
            db.commit()

    # 2. Determine agent and routing
    p_lower = req.message.lower()
    task_type = "writing" if ("tailor" in p_lower or "cover" in p_lower or "resume" in p_lower) else \
                "reasoning" if ("architecture" in p_lower or "plan" in p_lower or "system" in p_lower) else \
                "fast" if ("match" in p_lower or "score" in p_lower or "quick" in p_lower) else "general"

    agent_name = "Resume Agent" if "resume" in p_lower else \
                 "ATS Agent" if ("ats" in p_lower or "score" in p_lower) else \
                 "Job Discovery Agent" if "job" in p_lower else "Orchestrator Agent"

    # 3. Model Router dispatch
    start_t = datetime.now(timezone.utc)
    llm_resp = await model_router.generate_response(prompt=req.message, task_type=task_type)
    end_t = datetime.now(timezone.utc)

    # 4. Record AgentRun Telemetry in DB
    run_log = AgentRun(
        workflow_id=wf_id,
        agent_name=agent_name,
        status="SUCCESS",
        start_time=start_t,
        end_time=end_t
    )
    db.add(run_log)
    db.commit()

    # 5. Publish to Event Bus
    await event_bus.publish("AGENT_TASK_COMPLETED", {
        "workflow_id": wf_id,
        "agent": agent_name,
        "provider": llm_resp["provider"],
        "latency_ms": llm_resp["latency_ms"]
    })

    return {
        "workflow_id": wf_id,
        "agent_name": agent_name,
        "provider_used": llm_resp["provider"],
        "latency_ms": llm_resp["latency_ms"],
        "reply": llm_resp["content"]
    }

@router.get("/workflows")
def list_workflows(user_id: str, db: Session = Depends(get_db)):
    """Lists all active and completed workflows with nested agent execution logs."""
    wfs = db.query(Workflow).filter_by(user_id=user_id).order_by(Workflow.started_at.desc()).limit(10).all()
    results = []
    for w in wfs:
        runs = [{
            "run_id": r.agent_run_id,
            "agent": r.agent_name,
            "status": r.status,
            "duration_ms": int((r.end_time - r.start_time).total_seconds() * 1000) if r.end_time and r.start_time else 0
        } for r in w.agent_runs]
        results.append({
            "workflow_id": w.workflow_id,
            "status": w.status,
            "current_step": w.current_step,
            "started_at": w.started_at.isoformat() if w.started_at else None,
            "agent_runs": runs
        })
    return {"workflows": results}
