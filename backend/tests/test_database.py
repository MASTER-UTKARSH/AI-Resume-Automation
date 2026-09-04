import unittest
from backend.app.database.session import SessionLocal, init_db
from backend.app.database.models import User, Company, Job, Resume, CandidateProfile, CandidateSkill
from backend.app.services.seed_data import seed_database

class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        init_db()
        self.db = SessionLocal()
        seed_database(self.db)

    def tearDown(self):
        self.db.close()

    def test_seeded_users(self):
        users = self.db.query(User).all()
        self.assertGreaterEqual(len(users), 3)
        user_names = [u.full_name for u in users]
        self.assertIn("Utkarsh Shah", user_names)
        self.assertIn("Utsav Kothari", user_names)
        self.assertIn("Yashasv Pandey", user_names)

    def test_seeded_companies_and_jobs(self):
        companies = self.db.query(Company).all()
        self.assertGreaterEqual(len(companies), 4)

        jobs = self.db.query(Job).all()
        self.assertGreaterEqual(len(jobs), 4)
        job_titles = [j.title for j in jobs]
        self.assertTrue(any("AI" in t for t in job_titles))
        self.assertTrue(any("Software" in t for t in job_titles))

    def test_relational_cascade(self):
        test_user = User(email="test.student@juet.in", full_name="Test Student")
        self.db.add(test_user)
        self.db.commit()

        resume = Resume(user_id=test_user.user_id, file_name="sample.pdf")
        self.db.add(resume)
        self.db.commit()

        profile = CandidateProfile(
            user_id=test_user.user_id,
            resume_id=resume.resume_id,
            full_name="Test Student",
            headline="CSE Undergraduate"
        )
        self.db.add(profile)
        self.db.commit()

        skill = CandidateSkill(profile_id=profile.profile_id, skill_name="Python", category="Languages")
        self.db.add(skill)
        self.db.commit()

        # Check relationships
        self.assertEqual(len(test_user.resumes), 1)
        self.assertEqual(len(resume.profiles), 1)
        self.assertEqual(len(profile.skills), 1)

        # Delete user should cascade
        self.db.delete(test_user)
        self.db.commit()

        self.assertIsNone(self.db.query(Resume).filter_by(resume_id=resume.resume_id).first())
        self.assertIsNone(self.db.query(CandidateProfile).filter_by(profile_id=profile.profile_id).first())

if __name__ == "__main__":
    unittest.main()
