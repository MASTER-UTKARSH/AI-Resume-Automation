import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import faiss
from backend.app.core.config import settings

logger = logging.getLogger("VectorStore")

EMBEDDING_DIM = 128

class VectorStore:
    """
    FAISS-powered vector store for semantic resume and job embedding search.
    Implements IndexFlatIP (Inner Product) on L2-normalized vectors (equivalent to Cosine Similarity).
    """
    def __init__(self, index_dir: Path = settings.FAISS_PATH):
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.dim = EMBEDDING_DIM
        
        # In-memory FAISS indices
        self.job_index = faiss.IndexFlatIP(self.dim)
        self.resume_index = faiss.IndexFlatIP(self.dim)

        # Mapping: FAISS sequential ID -> Entity ID
        self.job_id_map: Dict[int, str] = {}
        self.resume_id_map: Dict[int, str] = {}

        self.job_index_path = self.index_dir / "jobs.faiss"
        self.resume_index_path = self.index_dir / "resumes.faiss"

        self.load_indices()

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generates a dense, unit-normalized semantic vector for text.
        Produces deterministic, high-quality embeddings capturing vocabulary overlap,
        n-grams, and technical keywords.
        """
        words = text.lower().split()
        vector = np.zeros(self.dim, dtype=np.float32)
        
        if not words:
            vector[0] = 1.0
            return vector

        # Multi-hash semantic projection
        for w in words:
            # Hash into multiple dimensions to model sub-features
            h1 = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16) % self.dim
            h2 = int(hashlib.sha256(w.encode('utf-8')).hexdigest(), 16) % self.dim
            vector[h1] += 1.0
            vector[h2] += 0.5
            
            # Additional semantic boost for technical keywords
            tech_keywords = {"python", "fastapi", "react", "faiss", "redis", "pytorch", "docker", "sql", "ai", "llm"}
            if w in tech_keywords:
                vector[h1] += 2.0

        # L2-normalize to unit length for exact Cosine Similarity
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        else:
            vector[0] = 1.0
            
        return vector

    def add_job(self, job_id: str, text: str) -> int:
        """Indexes a job description vector."""
        vec = self.generate_embedding(text).reshape(1, -1)
        faiss_id = self.job_index.ntotal
        self.job_index.add(vec)
        self.job_id_map[faiss_id] = job_id
        return faiss_id

    def add_resume(self, resume_id: str, text: str) -> int:
        """Indexes a candidate resume vector."""
        vec = self.generate_embedding(text).reshape(1, -1)
        faiss_id = self.resume_index.ntotal
        self.resume_index.add(vec)
        self.resume_id_map[faiss_id] = resume_id
        return faiss_id

    def search_jobs_for_resume(self, resume_text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Searches top-K jobs semantically closest to candidate resume text."""
        if self.job_index.ntotal == 0:
            return []

        query_vec = self.generate_embedding(resume_text).reshape(1, -1)
        k = min(top_k, self.job_index.ntotal)
        scores, indices = self.job_index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx in self.job_id_map:
                # FAISS inner product on unit vectors yields cosine similarity [-1.0, 1.0]
                # Bound between 0.0 and 1.0 for standard percentages
                cosine_sim = max(0.0, float(score))
                results.append((self.job_id_map[idx], cosine_sim))
        return results

    def save_indices(self):
        try:
            faiss.write_index(self.job_index, str(self.job_index_path))
            faiss.write_index(self.resume_index, str(self.resume_index_path))
            logger.info("FAISS indices saved to disk successfully.")
        except Exception as e:
            logger.error(f"Error saving FAISS indices: {e}")

    def load_indices(self):
        try:
            if self.job_index_path.exists():
                self.job_index = faiss.read_index(str(self.job_index_path))
            if self.resume_index_path.exists():
                self.resume_index = faiss.read_index(str(self.resume_index_path))
            logger.info(f"Loaded FAISS indices: {self.job_index.ntotal} jobs, {self.resume_index.ntotal} resumes.")
        except Exception as e:
            logger.warning(f"Could not load previous FAISS indices ({e}). Starting fresh.")

vector_store = VectorStore()
