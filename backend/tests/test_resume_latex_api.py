import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal, init_db
from backend.app.database.models import User, Resume, ResumeVersion, CandidateProfile, CandidateSkill, CandidateEducation, CandidateProject

class TestResumeLatexApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Seed candidate user, resume and profile
        cls.user = cls.db.query(User).filter_by(user_id="usr-test-latex").first()
        if not cls.user:
            cls.user = User(user_id="usr-test-latex", email="test.latex@juetguna.in", full_name="Utkarsh Shah")
            cls.db.add(cls.user)
            cls.db.commit()

        cls.resume = cls.db.query(Resume).filter_by(resume_id="res-test-latex-123").first()
        if not cls.resume:
            cls.resume = Resume(resume_id="res-test-latex-123", user_id=cls.user.user_id, file_name="resume.pdf", original_file_url="/tmp/resume.pdf")
            cls.db.add(cls.resume)
            cls.db.commit()

        cls.profile = cls.db.query(CandidateProfile).filter_by(resume_id=cls.resume.resume_id).first()
        if not cls.profile:
            cls.profile = CandidateProfile(
                resume_id=cls.resume.resume_id,
                user_id=cls.user.user_id,
                full_name="Utkarsh Shah",
                email="utkarsh.shah@juetguna.in",
                phone="+91 9876543210",
                headline="AI & Backend Software Engineer"
            )
            cls.db.add(cls.profile)
            cls.db.commit()

            skill1 = CandidateSkill(profile_id=cls.profile.profile_id, skill_name="Python", category="Languages")
            skill2 = CandidateSkill(profile_id=cls.profile.profile_id, skill_name="FastAPI", category="Frameworks")
            skill3 = CandidateSkill(profile_id=cls.profile.profile_id, skill_name="FAISS", category="Databases")
            edu = CandidateEducation(
                profile_id=cls.profile.profile_id,
                institution="Jaypee University of Engineering & Technology, Guna",
                degree="B.Tech in Computer Science & Engineering",
                graduation_year="2026",
                gpa="8.8 / 10.0"
            )
            proj = CandidateProject(
                profile_id=cls.profile.profile_id,
                title="AI-Powered Resume Platform",
                technologies="FastAPI, FAISS, Redis",
                description="Architected multi-agent system reducing matching latency by 42% across candidate profiles."
            )
            cls.db.add_all([skill1, skill2, skill3, edu, proj])
            cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_download_resume_latex_source(self):
        resp = self.client.get(f"/api/resumes/{self.resume.resume_id}/latex")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/x-tex", resp.headers["content-type"])
        self.assertIn("attachment; filename=", resp.headers["content-disposition"])
        self.assertIn(r"\begin{document}", resp.text)
        self.assertIn("Utkarsh Shah", resp.text)
        self.assertIn(r"\section{Technical Skills}", resp.text)

    def test_export_tailored_latex_endpoint(self):
        tailored_bullets = [
            "Tailored XYZ: Engineered sub-50ms vector search microservices using FastAPI and FAISS.",
            "Tailored XYZ: Scaled distributed indexing pipeline for 100,000 candidate profiles."
        ]
        resp = self.client.post(
            f"/api/resumes/{self.resume.resume_id}/export-latex",
            data={
                "tailored_bullets_json": str(tailored_bullets).replace("'", '"'),
                "job_title": "AI Engineer",
                "company": "Anthropic"
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("tex_source", data)
        self.assertIn("sub-50ms", data["tex_source"])
        self.assertTrue(data["compiler_available"])

    def test_download_compiled_pdf_endpoint(self):
        resp = self.client.get(f"/api/resumes/{self.resume.resume_id}/pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "application/pdf")
        self.assertGreater(len(resp.content), 5000)
        # Check standard PDF header magic bytes
        self.assertTrue(resp.content.startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
