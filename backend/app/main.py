import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.event_bus import event_bus
from backend.app.database.session import init_db, SessionLocal
from backend.app.services.seed_data import seed_database
from backend.app.api import resumes, jobs, agent, telemetry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("App")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database & Event Bus
    logger.info("Initializing Database tables...")
    init_db()
    
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    logger.info("Connecting to Event Bus...")
    await event_bus.connect()

    yield

    # Shutdown: Disconnect Event Bus
    logger.info("Shutting down Event Bus...")
    await event_bus.disconnect()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Event-Driven Multi-Agent Backend for AI-Powered Resume Automation & Career Copilot (JUET Minor Project 1).",
    lifespan=lifespan
)

# Enable CORS for local development and extension communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Paths
static_dir = os.path.join(os.path.dirname(__file__), "static")
static_index = os.path.join(static_dir, "index.html")
ui_dir = os.path.join(os.path.dirname(__file__), "..", "..", "stitch_ai_career_copilot")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

if os.path.exists(ui_dir):
    app.mount("/dashboard", StaticFiles(directory=ui_dir, html=True), name="dashboard")

# Register API Routers
app.include_router(resumes.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(telemetry.router, prefix="/api")

@app.get("/")
@app.get("/app")
def serve_web_app():
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return {"message": "Clyde Web App Static file not found."}

@app.get("/api")
def root_api():
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ONLINE",
        "documentation": "/docs",
        "architecture": "Event-Driven Multi-Agent (FastAPI + FAISS + Redis + PostgreSQL)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
