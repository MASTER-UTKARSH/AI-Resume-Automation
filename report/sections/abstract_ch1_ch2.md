# ABSTRACT

Campus placement drives force students to spend hours typing the same personal and academic details into dozens of company portals. Many students turn to public chatbots to rewrite their resumes for each role, which often introduces fake percentages or tools the student never used. This project presents Clyde, a resume automation and job application system built for B.Tech CSE students. It handles PDF parsing, semantic job matching, grounded bullet editing, LaTeX typesetting, and Chrome form autofill without inventing candidate history.

The backend runs on FastAPI (`backend/app/main.py`) and stores user profiles, job listings, match scores, and execution logs in a 19-table SQLAlchemy database. For real-time status updates, `EventBus` connects to Redis Pub/Sub and falls back within one second to an in-memory `asyncio` queue if Redis is not running locally. Uploaded PDFs and scraped job pages pass through `PostingGuard` first to strip hidden CSS blocks, invisible Unicode characters, homoglyphs, and prompt injection strings. `VectorStore` stores 128-dimensional L2-normalized vectors in FAISS `IndexFlatIP`. `MatchingEngine` ranks jobs using four weights: semantic similarity (`40%`), skill overlap (`30%`), experience fit (`15%`), and location preference (`15%`), then applies a penalty from `GhostJobDetector` for stale or reposted listings.

When tailoring resume bullets, `ModelRouter` routes drafting and review calls across Groq (`qwen/qwen3.8-27b`), GLM, Qwen, and Ollama. `FactVerifier` then checks every number and tool name in the output against the student's saved profile before `LatexExporter` compiles a single-column PDF using Tectonic. In the browser, a Chrome Manifest V3 TypeScript extension connects to `/api/extension/ws`, picks an adapter for the current job portal, maps fields with `FormMapper`, attaches the PDF using `DataTransfer`, and stops on a mandatory approval prompt before anything can be submitted. All `24/24` backend (`unittest`) and `24/24` extension (`Vitest`) tests pass.

---

# CHAPTER 1: INTRODUCTION

## 1.1 Background of the Study

During placement and summer internship season, pre-final and final-year engineering students repeat the same routine every evening. A student starts with a base resume PDF, edits a few project bullets to include keywords from a new job posting, recompiles the PDF, opens a Greenhouse, Lever, or Workday link, and types their name, roll number, CGPA, phone number, GitHub URL, and graduation year across a multi-page form. Even when a candidate qualifies for twenty roles, manual data entry caps how many applications they can finish in a day.

Most companies also pass applications through an Applicant Tracking System (ATS) before a recruiter reads them. Older ATS parsers often break on two-column layouts, skip text inside graphics, or rank a qualified student low because exact keywords from the job post are missing. To fix this quickly, students paste their resume and the job description into public chat tools. That creates a real problem in interviews: unconstrained models routinely invent metrics like "cut API latency by 65%", add frameworks the student never touched, or pad bullets with phrases like "synergy" and "thought leader". Interviewers spot those claims within minutes.

Public job boards bring two more headaches. Many listings stay up for months after a team stops hiring, wasting student time on ghost jobs. Scraped HTML pages can also hide text via CSS (`display:none`, `opacity:0`) or invisible Unicode tag characters meant to hijack LLM prompts. Fixing this workflow properly requires handling parsing, sanitization, ranking, fact checking, and browser autofill inside one connected system.

## 1.2 Problem Statement

Existing career tools solve small pieces of this workflow while leaving obvious gaps. Standard Chrome autofill extensions save static contact info, so they cannot rewrite resume bullets for a new posting or build a fresh PDF. AI resume wrappers rewrite text smoothly, but they do not verify whether the new numbers or skills actually exist in the student's background. Headless scripts written in Selenium or Playwright break easily on logged-in portals and sometimes submit incomplete forms with no user review.

We defined four technical requirements for this project:
1. Uploaded PDFs and scraped job descriptions must be cleaned of hidden CSS, zero-width Unicode characters, homoglyphs, and prompt injections before reaching any LLM prompt or SQL table.
2. Keyword counting misses related technical roles, so job matching needs 128-dimensional FAISS inner-product search combined with skill overlap, experience fit, location preference, and ghost-job penalties.
3. Tailored resume bullets must pass deterministic number and vocabulary checks so invented metrics or banned buzzwords never reach the final PDF.
4. Form autofill must run inside the student's own Chrome session through a Manifest V3 extension and enforce a hard human approval step before submission.

## 1.3 Objectives

This minor project has five goals:

1. Build an event-driven FastAPI backend with a 19-table SQLAlchemy schema covering candidate profiles, job sources, matches, applications, and workflow runs, backed by a Redis Pub/Sub and in-memory `asyncio` `EventBus`.
2. Implement deterministic PDF parsing (`ResumeParser`) with single-column `sb2nov` LaTeX generation (`LatexExporter`) and local Tectonic PDF compilation.
3. Set up 128-D vector indexing in FAISS (`IndexFlatIP`) with a four-factor `MatchingEngine` and a two-tier `GhostJobDetector`, fed by seeded roles and live scraping (`JobScraperService`).
4. Run multi-provider bullet tailoring (`ModelRouter`) across Groq, GLM, Qwen, and Ollama with strict `FactVerifier` checks.
5. Build a Chrome Manifest V3 TypeScript extension with an idle-aware `WebSocketManager`, isolated portal adapters in `PlatformRegistry`, an eight-level `FormMapper`, `DataTransfer` PDF upload, and a mandatory `SubmissionEngine` confirmation lock.

## 1.4 Scope of the Project

The platform is built for undergraduate Computer Science and Engineering students applying to software, backend, and ML internships, tested locally with student profiles from Jaypee University of Engineering and Technology (JUET), Guna. The backend covers PDF parsing, input sanitization, live job scraping, FAISS matching, grounded bullet rewriting, LaTeX export, and the Clyde web chat interface. The extension covers Chrome Manifest V3 automation with adapters for Greenhouse, Lever, Workday, LinkedIn, SimplifyJobs, and generic HTML forms.

For security, the extension never stores job-portal passwords and never tries to solve or bypass CAPTCHAs, Cloudflare checks, or OTP prompts. When `SubmissionEngine` sees a verification gate, it pauses and hands control back to the student.

## 1.5 Organization of the Report

Chapter 2 reviews existing ATS checkers, auto-apply bots, and browser autofill extensions. Chapter 3 covers the four-layer architecture, Data Flow Diagrams, UML diagrams, and the 19-table database schema. Chapter 4 walks through the Python backend and TypeScript extension code along with unit and browser test results. Chapter 5 analyzes ranking scores, latency measurements, and bugs fixed during integration. Chapter 6 summarizes the results and lists future improvements. Appendices A through C contain core source files, sample LaTeX output, and test logs.

---

# CHAPTER 2: LITERATURE REVIEW AND BACKGROUND WORK

## 2.1 Existing Systems and Related Work

Career automation tools mostly fall into three groups: static ATS checkers, bulk-apply bots, and browser autofill extensions.

Static checkers like Jobscan and ResumeWorded compare a resume against a job description using word counts and phrase lists [1]. They show missing keywords quickly, but the student still has to edit their Word or LaTeX file, export a new PDF, and type every field on the company website by hand.

Bulk-apply bots sit at the other extreme. Open-source scripts like Auto_Jobs_Applier_AIHawk drive Chrome with Selenium or Playwright on LinkedIn Easy Apply and call LLMs to answer screening questions automatically [2]. Commercial tools like LoopCV also submit applications in bulk in the background. Chasing volume like this causes real problems: made-up claims, broken scrapers when site layouts change, and applications sent out without the user reading them.

Extensions like Simplify Copilot and Teal run inside the user's Chrome browser and detect fields on Greenhouse, Lever, and Workday. They save time on basic contact fields, though they treat the resume as a static file and do not connect semantic matching, bullet tailoring, and fact checking in one backend.

In information retrieval, dense vector search works better than plain BM25 word matching when technical terms vary across postings [3]. FAISS `IndexFlatIP` provides fast exact inner-product search over normalized vectors in memory [4]. On the security side, recent work on indirect prompt injection shows how attackers hide instructions in external HTML using zero-width characters, Unicode tag blocks (`U+E0000`–`U+E007F`), or hidden CSS [5]. Combining input sanitization with provenance checks keeps LLM assistance useful without compromising accuracy. Table 2.1 compares these systems with Clyde.

**Table 2.1: Comparison of Existing Career Automation Systems**

| Feature / Capability | Jobscan | AIHawk / LoopCV | Simplify Extension | Proposed System (Clyde) |
| :--- | :--- | :--- | :--- | :--- |
| Parsing & ATS Scoring | Yes (Static) | Basic | Basic Profile | Deterministic PyPDF + LaTeX |
| Job Discovery & Ranking | No | Portal Scrape Only | Job Board Feed | Live Scrape + 4-Factor FAISS |
| Ghost Job Filtering | No | No | No | Two-Tier Structural + Silence |
| Security Sanitization | No | No | No | `PostingGuard` (Unicode & CSS) |
| Resume Tailoring | Manual Advice | Unverified LLM | No | Drafter-Reviewer + `FactVerifier` |
| Execution Architecture | Web App Only | Headless Bot | Chrome Extension | FastAPI WS + Chrome MV3 |
| Pre-Submit Human Gate | Manual Copy | Auto-Submits | Optional | Mandatory Non-Bypassable Gate |

## 2.2 Limitations of Existing Work

Four recurring problems in existing tools shaped Clyde's design:

1. LLM Hallucinations: Prompting a model without post-checks often produces fake percentages, team sizes, or tools that are not in the student's repository history. Having to defend an invented claim in a technical interview hurts the candidate immediately.
2. Unreviewed Mass Submissions: Auto-apply bots optimize for quantity and send poorly worded answers or wrong resumes before the student can check the form.
3. Untrusted HTML Inputs: Passing raw scraped job descriptions straight into LLM prompts exposes the pipeline to hidden CSS text, mixed-script homoglyphs, and invisible Unicode tag blocks.
4. Ghost Job Noise: Simple keyword or vector matchers rank old postings that have been open for months or reposted repeatedly, sending students toward inactive hiring pipelines.

## 2.3 Need for the Proposed System

Students preparing for campus placements need a tool that cuts out repetitive typing without sacrificing factual accuracy. Fast autofill does not help if the uploaded resume contains made-up numbers or targets a dead job link.

Splitting the work between a FastAPI backend and a Manifest V3 Chrome extension handles both needs. Keeping PDF parsing, sanitization, FAISS ranking, fact verification, and Tectonic builds in Python makes every step easy to inspect and test. Limiting the Chrome extension to DOM mapping, React-safe input updates, `DataTransfer` file attachment, and a hard confirmation lock lets students apply from their own logged-in browser while keeping final control over every submission.
