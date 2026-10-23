import unittest
from backend.app.services.latex_exporter import LatexExporter, latex_exporter

class TestLatexExporter(unittest.TestCase):
    def setUp(self):
        self.sample_profile = {
            "full_name": "Utkarsh Shah",
            "email": "utkarsh.shah@juetguna.in",
            "phone": "+91 9876543210",
            "location": "Guna, MP, India",
            "linkedin": "linkedin.com/in/utkarsh-shah",
            "github": "github.com/utkarsh-21",
            "education": [{
                "institution": "Jaypee University of Engineering & Technology, Guna",
                "degree": "B.Tech in Computer Science & Engineering",
                "year": "2022 -- 2026",
                "gpa": "8.8 / 10.0"
            }],
            "skills": [
                {"name": "Python", "category": "Languages"},
                {"name": "FastAPI", "category": "Frameworks"},
                {"name": "FAISS", "category": "Databases"},
                {"name": "Docker", "category": "Tools"}
            ],
            "experience": [{
                "company": "Tech Corp",
                "role": "Backend Intern",
                "dates": "May 2025 -- July 2025",
                "location": "Remote",
                "bullets": ["Built high-throughput REST APIs using FastAPI serving 10,000+ users."]
            }],
            "projects": [{
                "title": "AI-Powered Resume Platform",
                "technologies": "FastAPI, FAISS, Redis",
                "dates": "2026",
                "bullets": ["Architected multi-agent system reducing matching latency by 42%."]
            }]
        }

    def test_latex_escaping_and_bolding(self):
        # 1. Escape special characters
        raw = r"High-scale & reliable system with 99.9% uptime and $500 cost in C# / C++."
        escaped = LatexExporter.escape_latex(raw)
        self.assertIn(r"\&", escaped)
        self.assertIn(r"\%", escaped)
        self.assertIn(r"\$", escaped)
        self.assertIn(r"\#", escaped)

        # 2. Markdown bolding conversion
        bullet = "Reduced query latency by **42%** and cut costs by **$10K**."
        rendered_bullet = LatexExporter.render_latex_bullet(bullet)
        self.assertIn(r"\textbf{42\%}", rendered_bullet)
        self.assertIn(r"\textbf{\$10K}", rendered_bullet)

    def test_url_sanitization(self):
        url1 = "linkedin.com/in/utkarsh-shah"
        self.assertEqual(LatexExporter.sanitize_url(url1), "https://linkedin.com/in/utkarsh-shah")

        url2 = "https://github.com/utkarsh-21"
        self.assertEqual(LatexExporter.sanitize_url(url2), "https://github.com/utkarsh-21")

    def test_generate_latex_source(self):
        tex = LatexExporter.generate_latex_source(self.sample_profile)

        # Standard Jake's resume structure checks
        self.assertIn(r"\pdfgentounicode=1", tex)
        self.assertIn(r"Utkarsh Shah", tex)
        self.assertIn(r"\section{Education}", tex)
        self.assertIn(r"\section{Technical Skills}", tex)
        self.assertIn(r"\section{Experience}", tex)
        self.assertIn(r"\section{Projects \& Engineering Experience}", tex)
        self.assertIn(r"\resumeSubheading", tex)
        self.assertIn(r"\resumeProjectHeading", tex)
        self.assertIn(r"\resumeItem", tex)

    def test_tailored_bullets_injection(self):
        tailored_bullets = [
            "Tailored XYZ bullet: Engineered scalable microservices with FastAPI for **50ms** SLA.",
            "Tailored XYZ bullet: Integrated vector search with FAISS improving search recall by **35%**."
        ]

        tex = LatexExporter.generate_latex_source(
            self.sample_profile,
            tailored_bullets=tailored_bullets,
            job_title="AI Engineer",
            target_company="NVIDIA"
        )

        self.assertIn(r"\textbf{50ms}", tex)
        self.assertIn(r"\textbf{35\%}", tex)
        self.assertIn("Tailored XYZ bullet", tex)

    def test_fact_verifier_audit_in_latex_export(self):
        # Grounded bullet should pass
        grounded_bullets = [
            "Built high-throughput REST APIs using FastAPI serving 10,000+ users."
        ]
        grounded_res = LatexExporter.audit_and_export_latex(
            profile_data=self.sample_profile,
            tailored_bullets=grounded_bullets
        )
        self.assertTrue(grounded_res["is_grounded"])
        self.assertEqual(grounded_res["provenance_score"], 100.0)

        # Fabricated bullet with invented numbers/metrics should fail provenance gate
        hallucinated_bullets = [
            "Managed $5,000,000 budget and led 50 engineers with 99.999% reliability."
        ]
        hallucinated_res = LatexExporter.audit_and_export_latex(
            profile_data=self.sample_profile,
            tailored_bullets=hallucinated_bullets
        )
        self.assertFalse(hallucinated_res["is_grounded"])
        self.assertLess(hallucinated_res["provenance_score"], 100.0)
        self.assertGreater(len(hallucinated_res["fact_audit"]["unverified_metrics"]), 0)

    def test_tectonic_binary_detection(self):
        path = LatexExporter.get_tectonic_path()
        self.assertIsNotNone(path)
        self.assertTrue(path.endswith("tectonic"))

    def test_compile_pdf_with_tectonic(self):
        tex = LatexExporter.generate_latex_source(self.sample_profile)
        res = LatexExporter.compile_pdf(tex)
        self.assertTrue(res["success"])
        self.assertGreater(res["file_size"], 1000)
        self.assertIsNotNone(res["pdf_bytes"])

if __name__ == "__main__":
    unittest.main()
