import unittest
import numpy as np
from backend.app.database.session import SessionLocal, init_db
from backend.app.database.models import User, Job, CandidateProfile, Resume
from backend.app.services.seed_data import seed_database
from backend.app.services.vector_store import vector_store
from backend.app.services.matching_engine import matching_engine
from backend.app.services.resume_parser import resume_parser

class TestFAISSAndMatching(unittest.TestCase):
    def setUp(self):
        init_db()
        self.db = SessionLocal()
        seed_database(self.db)
        self.user = self.db.query(User).filter_by(user_id="usr-utkarsh-241b278").first()

    def tearDown(self):
        self.db.close()

    def test_faiss_vector_normalization_and_indexing(self):
        text1 = "Python machine learning FAISS vector search PyTorch algorithms"
        text2 = "React TypeScript frontend user interface CSS Tailwind"
        
        vec1 = vector_store.generate_embedding(text1)
        vec2 = vector_store.generate_embedding(text2)

        # Check dimension
        self.assertEqual(len(vec1), vector_store.dim)
        self.assertEqual(len(vec2), vector_store.dim)

        # Check L2 unit norm
        self.assertAlmostEqual(float(np.linalg.norm(vec1)), 1.0, places=4)
        self.assertAlmostEqual(float(np.linalg.norm(vec2)), 1.0, places=4)

        # Indexing test
        initial_count = vector_store.job_index.ntotal
        vector_store.add_job("test-job-ml", text1)
        self.assertEqual(vector_store.job_index.ntotal, initial_count + 1)

        # Query test: querying ML text should retrieve test-job-ml with highest similarity
        matches = vector_store.search_jobs_for_resume(text1, top_k=1)
        self.assertGreaterEqual(len(matches), 1)
        top_job_id, sim = matches[0]
        self.assertEqual(top_job_id, "test-job-ml")
        self.assertGreater(sim, 0.80)

    def test_multi_factor_job_matching(self):
        sample_text = """
        Utkarsh Shah
        Email: utkarsh.shah@juetguna.in
        Skills: Python, PyTorch, FAISS, CUDA, FastAPI, Docker, Git, REST APIs
        Education: B.Tech CSE JUET Guna (CGPA: 8.8)
        Projects: AI-Powered Career Copilot and Deep Learning Inference Optimization
        """
        parsed = resume_parser.parse_text(sample_text)
        resume = resume_parser.save_parsed_profile(self.db, self.user.user_id, parsed, "AI_Engineer_Resume.pdf")
        profile = self.db.query(CandidateProfile).filter_by(resume_id=resume.resume_id).first()

        # Run multi-factor matching against all seeded jobs
        ranked_matches = matching_engine.match_candidate_against_all_jobs(
            db=self.db,
            user_id=self.user.user_id,
            profile_id=profile.profile_id
        )

        self.assertGreaterEqual(len(ranked_matches), 3)
        
        # Candidate with PyTorch, CUDA, FAISS, Python should score highest on NVIDIA AI Intern!
        top_match = ranked_matches[0]
        self.assertIn("AI", top_match.job.title)
        self.assertGreater(top_match.match_score, 75.0)
        self.assertGreater(top_match.skills_score, 75.0)

        # Ensure breakdown fields are computed
        self.assertIsNotNone(top_match.matching_skills)
        self.assertIn("Python", top_match.matching_skills)
        self.assertIsNotNone(top_match.reason)

if __name__ == "__main__":
    unittest.main()
