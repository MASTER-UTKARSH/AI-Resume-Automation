import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
FAISS_DIR = DATA_DIR / "faiss"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
FAISS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    APP_NAME: str = "AI-Powered Resume Automation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/app.db")
    
    # Redis Event Bus (falls back to async queue if Redis is not running)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # File storage paths
    UPLOAD_PATH: Path = UPLOADS_DIR
    FAISS_PATH: Path = FAISS_DIR
    
    # Model Router API configurations (optional env overrides)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GLM_API_KEY: str = os.getenv("GLM_API_KEY", "")
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

settings = Settings()
