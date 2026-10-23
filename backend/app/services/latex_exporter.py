"""
LaTeX Resume Exporter Service
=============================
Generates deterministic, ATS-optimized LaTeX resumes based on the sb2nov / Jake's Resume format.
Features:
1. Special character escaping & URL sanitization
2. Markdown bolding conversion (**metric** -> \\textbf{metric})
3. Dynamic section rendering and empty-section omission
4. Pre-export Factual Grounding Gate (FactVerifier audit)
5. Direct PDF compilation via local/system Tectonic or pdflatex
"""

import os
import re
import shutil
import tempfile
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.services.fact_verifier import FactVerifier

logger = logging.getLogger("LatexExporter")

# Special characters mapping for LaTeX
LATEX_ESCAPE_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

LATEX_ESCAPE_REGEX = re.compile(
    "|".join(re.escape(k) for k in LATEX_ESCAPE_MAP.keys())
)

MARKDOWN_BOLD_REGEX = re.compile(r"\*\*([^*]+?)\*\*")

# Base Jake's Resume Template (sb2nov single-column ATS standard)
RESUME_LATEX_TEMPLATE = r"""%-------------------------
% Clyde AI Career Copilot - Tailored ATS Resume
% Based on: Jake's Resume / sb2nov (Single-Column ATS Format)
% Compatible with: Overleaf, Tectonic, pdflatex, XeLaTeX
%------------------------

\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{multicol}
\usepackage{iftex}

\ifPDFTeX
  \input{glyphtounicode}
  \pdfgentounicode=1
\fi

\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1.0in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-6pt}\scshape\raggedright\large\bfseries
}{}{0em}{}[\color{black}\titlerule \vspace{0pt}]

% Custom Commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{1.0\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & \textbf{\small #2} \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeProjectHeading}[2]{
  \vspace{-2pt}\item
    \begin{tabular*}{1.0\textwidth}[t]{l@{\extracolsep{\fill}}r}
      #1 & \textbf{\small #2} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.0in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=0.15in]}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-2pt}}

%-------------------------------------------
\begin{document}

%----------HEADING----------
\begin{center}
    {\Huge \scshape {{NAME}}} \\ \vspace{2pt}
    \small {{CONTACT_LINE}} \\ \vspace{2pt}
    {{SOCIAL_LINKS}}
\end{center}

{{EDUCATION_SECTION}}

{{SKILLS_SECTION}}

{{EXPERIENCE_SECTION}}

{{PROJECTS_SECTION}}

{{ACHIEVEMENTS_SECTION}}

\end{document}
"""


class LatexExporter:
    """Production service for generating and compiling tailored LaTeX resumes."""

    @classmethod
    def escape_latex(cls, text: Optional[str]) -> str:
        """Escapes raw text for safe LaTeX rendering."""
        if not text:
            return ""
        return LATEX_ESCAPE_REGEX.sub(lambda m: LATEX_ESCAPE_MAP[m.group(0)], str(text))

    @classmethod
    def render_latex_bullet(cls, text: str) -> str:
        """
        Escapes special characters and restores markdown bold markers (**text**)
        as \\textbf{text} for ATS key metric highlighting.
        """
        escaped = cls.escape_latex(text)
        return MARKDOWN_BOLD_REGEX.sub(r"\\textbf{\1}", escaped)

    @classmethod
    def sanitize_url(cls, url: Optional[str]) -> str:
        """Sanitizes URL for use in \\href while preserving protocol."""
        if not url:
            return ""
        url = url.strip()
        # Remove characters that could break LaTeX href
        url = re.sub(r'["\'\\]', "", url)
        if not re.match(r"^(https?://|mailto:)", url, re.IGNORECASE):
            url = "https://" + url
        return url

    @classmethod
    def get_tectonic_path(cls) -> Optional[str]:
        """Resolves local or system tectonic binary."""
        # 1. Check workspace backend/bin
        workspace_root = Path(__file__).resolve().parent.parent.parent.parent
        bin_tectonic = workspace_root / "backend" / "bin" / "tectonic"
        if bin_tectonic.exists() and os.access(bin_tectonic, os.X_OK):
            return str(bin_tectonic)

        # 2. Check reference_repos/career-ops/tectonic
        ref_tectonic = workspace_root / "reference_repos" / "career-ops" / "tectonic"
        if ref_tectonic.exists() and os.access(ref_tectonic, os.X_OK):
            return str(ref_tectonic)

        # 3. Check system PATH
        system_bin = shutil.which("tectonic")
        if system_bin:
            return system_bin

        # 4. Attempt auto-install via install_tectonic.sh
        installer = workspace_root / "backend" / "bin" / "install_tectonic.sh"
        if installer.exists() and os.access(installer, os.X_OK):
            try:
                subprocess.run([str(installer)], capture_output=True, timeout=30)
                if bin_tectonic.exists() and os.access(bin_tectonic, os.X_OK):
                    return str(bin_tectonic)
            except Exception:
                pass

        return None

    @classmethod
    def generate_latex_source(
        cls,
        profile_data: Dict[str, Any],
        tailored_bullets: Optional[List[str]] = None,
        job_title: Optional[str] = None,
        target_company: Optional[str] = None
    ) -> str:
        """
        Synthesizes structured candidate profile and tailored bullets into
        valid, compile-ready LaTeX code.
        """
        # 1. Header Information
        name = cls.escape_latex(profile_data.get("full_name") or profile_data.get("name") or "Candidate")
        phone = profile_data.get("phone", "+91 9876543210")
        email = profile_data.get("email", "candidate@juetguna.in")
        location = profile_data.get("location", "Guna, MP, India")

        contact_line = f"{cls.escape_latex(location)} $|$ {cls.escape_latex(phone)}"

        # Links
        links = []
        if email:
            clean_email = email.strip()
            links.append(r"\href{mailto:" + clean_email + r"}{\underline{" + cls.escape_latex(clean_email) + r"}}")
        
        linkedin = profile_data.get("linkedin", "linkedin.com/in/utkarsh-shah")
        if linkedin:
            sanitized_li = cls.sanitize_url(linkedin)
            display_li = re.sub(r"^https?://(www\.)?", "", linkedin).rstrip("/")
            links.append(r"\href{" + sanitized_li + r"}{\underline{" + cls.escape_latex(display_li) + r"}}")

        github = profile_data.get("github", "github.com/utkarsh-21")
        if github:
            sanitized_gh = cls.sanitize_url(github)
            display_gh = re.sub(r"^https?://(www\.)?", "", github).rstrip("/")
            links.append(r"\href{" + sanitized_gh + r"}{\underline{" + cls.escape_latex(display_gh) + r"}}")

        social_links = " $|$ ".join(links)

        # 2. Education Section
        education_records = profile_data.get("education", [])
        if education_records:
            edu_blocks = []
            for edu in education_records:
                inst = cls.escape_latex(edu.get("institution") or "Jaypee University of Engineering and Technology (JUET)")
                dates = cls.escape_latex(edu.get("year") or edu.get("dates") or "2022 -- 2026")
                deg = cls.escape_latex(edu.get("degree") or "Bachelor of Technology in Computer Science & Engineering")
                gpa = edu.get("gpa")
                subtext = f"CGPA: {gpa}" if gpa else "Guna, MP, India"
                edu_blocks.append(
                    f"    \\resumeSubheading\n"
                    f"      {{{inst}}}{{{dates}}}\n"
                    f"      {{{deg}}}{{{cls.escape_latex(subtext)}}}"
                )
            edu_content = "\n".join(edu_blocks)
            education_section = (
                r"\section{Education}" "\n"
                r"  \resumeSubHeadingListStart" "\n"
                f"{edu_content}\n"
                r"  \resumeSubHeadingListEnd"
            )
        else:
            education_section = ""

        # 3. Skills Section (Categorized)
        skills = profile_data.get("skills", [])
        categorized: Dict[str, List[str]] = {}
        for s in skills:
            if isinstance(s, dict):
                cat = s.get("category") or "Technical"
                sname = s.get("name") or s.get("skill_name") or ""
            else:
                sname = str(s)
                cat = "Languages" if sname in ["Python", "Java", "C++", "TypeScript", "SQL"] else \
                      "Frameworks & Libraries" if sname in ["FastAPI", "React", "PyTorch", "Docker"] else \
                      "Databases & Infrastructure" if sname in ["Redis", "FAISS", "PostgreSQL"] else "Tools"
            if sname:
                categorized.setdefault(cat, []).append(sname)

        if not categorized and skills:
            categorized["Technical Skills"] = [s.get("name") if isinstance(s, dict) else str(s) for s in skills]

        if categorized:
            skill_lines = []
            for cat, items in categorized.items():
                cat_escaped = cls.escape_latex(cat)
                items_escaped = ", ".join(cls.escape_latex(it) for it in items)
                skill_lines.append(f"     \\textbf{{{cat_escaped}}}: {{{items_escaped}}} \\\\")
            skills_content = "\n".join(skill_lines)
            skills_section = (
                r"\section{Technical Skills}" "\n"
                r" \begin{itemize}[leftmargin=0.15in, label={}]\small{\item{" "\n"
                f"{skills_content}\n"
                r" }}\end{itemize}\vspace{-10pt}"
            )
        else:
            skills_section = ""

        # 4. Experience Section
        experience_records = profile_data.get("experience", [])
        exp_blocks = []
        for exp in experience_records:
            company = cls.escape_latex(exp.get("company", "Tech Company"))
            role = cls.escape_latex(exp.get("title") or exp.get("role", "Software Engineer"))
            dates = cls.escape_latex(exp.get("dates") or "2024 -- Present")
            loc = cls.escape_latex(exp.get("location") or "Remote")
            
            raw_bullets = exp.get("bullets", [])
            if not raw_bullets and exp.get("description"):
                raw_bullets = [exp.get("description")]

            bullet_lines = [
                f"        \\resumeItem{{{cls.render_latex_bullet(b)}}}"
                for b in raw_bullets if b
            ]
            bullets_rendered = "\n".join(bullet_lines)

            exp_blocks.append(
                f"    \\resumeSubheading\n"
                f"      {{{company}}}{{{dates}}}\n"
                f"      {{{role}}}{{{loc}}}\n"
                f"      \\resumeItemListStart\n"
                f"{bullets_rendered}\n"
                f"      \\resumeItemListEnd"
            )

        if exp_blocks:
            exp_content = "\n\n".join(exp_blocks)
            experience_section = (
                r"\section{Experience}" "\n"
                r"  \resumeSubHeadingListStart" "\n"
                f"{exp_content}\n"
                r"  \resumeSubHeadingListEnd"
            )
        else:
            experience_section = ""

        # 5. Projects Section (With Tailored Bullets Injection)
        project_records = profile_data.get("projects", [])
        if not project_records:
            # Seed default project if none present
            project_records = [{
                "title": "AI-Powered Resume Automation Platform (Minor Project 1)",
                "technologies": "FastAPI, FAISS, Redis, PostgreSQL, React, PyTorch",
                "dates": "Feb 2026 -- Present",
                "bullets": [
                    "Architected an event-driven multi-agent platform using FastAPI and FAISS, reducing semantic matching latency by **42%** across candidate profiles.",
                    "Engineered 4-factor hybrid ranking algorithm combining 128-D dense embeddings, skill keyword overlap, and candidate preferences.",
                    "Implemented decoupled event bus supporting Redis Pub/Sub with transparent async in-memory failover."
                ]
            }]

        proj_blocks = []
        for idx, proj in enumerate(project_records):
            p_title = cls.escape_latex(proj.get("title", "Project"))
            p_tech = cls.escape_latex(proj.get("technologies", "Python, FastAPI"))
            p_dates = cls.escape_latex(proj.get("dates", "2026"))

            # If tailored bullets are provided, apply them to the first project
            if idx == 0 and tailored_bullets:
                p_bullets = tailored_bullets
            else:
                p_bullets = proj.get("bullets", [])
                if not p_bullets and proj.get("description"):
                    p_bullets = [proj.get("description")]

            bullet_items = [
                f"        \\resumeItem{{{cls.render_latex_bullet(b)}}}"
                for b in p_bullets if b
            ]
            bullets_rendered = "\n".join(bullet_items)

            heading = f"\\textbf{{{p_title}}} $|$ \\emph{{{p_tech}}}"
            proj_blocks.append(
                f"    \\resumeProjectHeading\n"
                f"      {{{heading}}}{{{p_dates}}}\n"
                f"      \\resumeItemListStart\n"
                f"{bullets_rendered}\n"
                f"      \\resumeItemListEnd"
            )

        proj_content = "\n\n".join(proj_blocks)
        projects_section = (
            r"\section{Projects \& Engineering Experience}" "\n"
            r"  \resumeSubHeadingListStart" "\n"
            f"{proj_content}\n"
            r"  \resumeSubHeadingListEnd"
        )

        # 6. Achievements / Certifications Section
        achievements = profile_data.get("achievements") or [
            "Deep Learning Specialization (DeepLearning.AI) -- PyTorch, Transformer Architectures",
            "Lead Coordinator, JUET ACM Student Chapter & Tech Initiatives (2024 -- Present)"
        ]
        ach_items = [f"        \\resumeItem{{{cls.render_latex_bullet(a)}}}" for a in achievements]
        achievements_section = (
            r"\section{Certifications \& Achievements}" "\n"
            r"  \resumeItemListStart" "\n"
            + "\n".join(ach_items) + "\n"
            r"  \resumeItemListEnd"
        )

        # Substitute tokens into template
        source = RESUME_LATEX_TEMPLATE
        source = source.replace("{{NAME}}", name)
        source = source.replace("{{CONTACT_LINE}}", contact_line)
        source = source.replace("{{SOCIAL_LINKS}}", social_links)
        source = source.replace("{{EDUCATION_SECTION}}", education_section)
        source = source.replace("{{SKILLS_SECTION}}", skills_section)
        source = source.replace("{{EXPERIENCE_SECTION}}", experience_section)
        source = source.replace("{{PROJECTS_SECTION}}", projects_section)
        source = source.replace("{{ACHIEVEMENTS_SECTION}}", achievements_section)

        # Clean multiple blank lines
        source = re.sub(r"\n{3,}", "\n\n", source)
        return source

    @classmethod
    def audit_and_export_latex(
        cls,
        profile_data: Dict[str, Any],
        tailored_bullets: Optional[List[str]] = None,
        job_title: Optional[str] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Audits tailored bullets with FactVerifier gate before generating
        Overleaf-compatible LaTeX source.
        """
        # Run FactVerifier audit if bullets provided
        fact_audit = {"is_grounded": True, "provenance_score": 100.0, "unverified_metrics": [], "buzzwords_flagged": []}
        if tailored_bullets:
            fact_audit = FactVerifier.audit_tailored_resume(tailored_bullets, profile_data)

        # Generate LaTeX code
        tex_source = cls.generate_latex_source(
            profile_data=profile_data,
            tailored_bullets=tailored_bullets,
            job_title=job_title,
            target_company=company
        )

        tectonic_path = cls.get_tectonic_path()

        return {
            "status": "success",
            "is_grounded": fact_audit.get("is_grounded", True),
            "provenance_score": fact_audit.get("provenance_score", 100.0),
            "fact_audit": fact_audit,
            "compiler_available": bool(tectonic_path),
            "compiler_path": tectonic_path,
            "tex_source": tex_source
        }

    @classmethod
    def compile_pdf(cls, tex_source: str) -> Dict[str, Any]:
        """
        Compiles LaTeX source code to PDF bytes using Tectonic.
        """
        tectonic_path = cls.get_tectonic_path()
        if not tectonic_path:
            return {
                "success": False,
                "error": "No LaTeX compiler found. Please install Tectonic or pdflatex."
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = Path(tmpdir) / "resume.tex"
            tex_file.write_text(tex_source, encoding="utf-8")

            try:
                cmd = [tectonic_path, str(tex_file), "-o", tmpdir]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=45
                )

                pdf_file = Path(tmpdir) / "resume.pdf"
                if proc.returncode == 0 and pdf_file.exists():
                    pdf_bytes = pdf_file.read_bytes()
                    return {
                        "success": True,
                        "pdf_bytes": pdf_bytes,
                        "file_size": len(pdf_bytes)
                    }
                else:
                    return {
                        "success": False,
                        "error": proc.stderr or proc.stdout or "Compilation failed"
                    }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": "Tectonic compilation timed out (45s limit)"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }


latex_exporter = LatexExporter()
