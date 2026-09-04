import unittest
from backend.app.database.session import SessionLocal, init_db
from backend.app.database.models import User, Resume, CandidateProfile
from backend.app.services.resume_parser import resume_parser

class TestResumeParser(unittest.TestCase):
    def setUp(self):
        init_db()
        self.db = SessionLocal()
        self.user = self.db.query(User).first()
        if not self.user:
            self.user = User(email="utkarsh.shah@juetguna.in", full_name="Utkarsh Shah")
            self.db.add(self.user)
            self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_text_parsing_and_ats_score(self):
        sample_resume_text = """
        Utkarsh Shah
        Email: utkarsh.shah@juetguna.in
        Phone: +91 9876543210
        GitHub: https://github.com/utkarshshah
        LinkedIn: https://linkedin.com/in/utkarshshah

        Summary:
        Final year Computer Science student specializing in multi-agent distributed systems and applied AI.

        Education:
        Jaypee University of Engineering & Technology, Guna
        B.Tech in Computer Science & Engineering
        CGPA: 8.6 / 10 | Year of Graduation: 2026

        Technical Skills:
        Languages: Python, C++, Java, JavaScript, TypeScript, SQL
        Frameworks: FastAPI, React, PyTorch, Node.js, Tailwind CSS
        Databases & Tools: PostgreSQL, Redis, FAISS, Docker, Git, REST APIs

        Projects:
        AI-Powered Resume Automation & Career Copilot
        Engineered an event-driven multi-agent platform for resume optimization and semantic job matching.
        Technologies: FastAPI, FAISS, Redis, PostgreSQL, React, TypeScript.
        """
        parsed = resume_parser.parse_text(sample_resume_text)

        self.assertEqual(parsed["name"], "Utkarsh Shah")
        self.assertEqual(parsed["email"], "utkarsh.shah@juetguna.in")
        self.assertIn("9876543210", parsed["phone"])
        
        # Skills verification
        skill_names = [s["name"] for s in parsed["skills"]]
        self.assertIn("Python", skill_names)
        self.assertIn("FastAPI", skill_names)
        self.assertIn("FAISS", skill_names)
        self.assertIn("PostgreSQL", skill_names)

        # ATS baseline score should be high for this complete resume
        self.assertGreaterEqual(parsed["ats_score"], 80.0)

        # Persistence test
        resume_record = resume_parser.save_parsed_profile(
            db=self.db,
            user_id=self.user.user_id,
            parsed_data=parsed,
            file_name="Utkarsh_Shah_Resume.pdf"
        )
        self.assertIsNotNone(resume_record.resume_id)

        # Fetch profile
        profile = self.db.query(CandidateProfile).filter_by(resume_id=resume_record.resume_id).first()
        self.assertIsNotNone(profile)
        self.assertGreaterEqual(len(profile.skills), 5)
        self.assertGreaterEqual(len(profile.education), 1)
        self.assertGreaterEqual(len(profile.projects), 1)

if __name__ == "__main__":
    unittest.main()
