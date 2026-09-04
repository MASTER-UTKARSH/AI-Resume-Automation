# Implementation Plan: Minor Project Presentation Deck

Create an academic PowerPoint presentation (`.pptx`) for the **AI-Powered Resume Automation System** (Minor Project 1) that strictly complies with the official department presentation format (`Presentation format.pptx`) and mandatory guidelines (`PPT_Instructions.pdf`), leveraging the comprehensive content draft (`AI_Powered_Resume_Automation_PPT_Content.md`), high-fidelity UI design assets (`stitch_ai_career_copilot`), and system architecture specifications.

---

## User Review Required

> [!IMPORTANT]
> **No AI-Generated Images Rule:** As emphasized in `PPT_Instructions.pdf`, the use of AI-generated images is strictly prohibited. All visuals in the deck will consist solely of:
> 1. Real UI screen captures from `stitch_ai_career_copilot/` (Clyde AI Career Copilot).
> 2. Native PowerPoint vector diagrams (shapes, flowcharts, container boxes, connector lines) generated programmatically for system and behavioral architecture.
> 3. Official university branding and logo from the template.

> [!WARNING]
> **Notion Integration Permission:** The Notion workspace bot (`antigravity`) is active in **UTKARSH SHAH’s Notion**, but currently has access to 0 pages because Notion requires explicit page-level sharing.
> To allow the bot to read your "System Architecture" page directly:
> 1. Open the page in Notion.
> 2. Click `···` in the top right corner.
> 3. Under **Connections** (or **Add connections**), select **antigravity**.
> *(Alternatively, if you prefer, we can construct the full architectural diagrams directly from the detailed architecture and behavioral specifications already documented in your `AI_Powered_Resume_Automation_PPT_Content.md` and `stitch_ai_career_copilot/design.md`)*.

---

## Open Questions & Placeholders

> [!NOTE]
> Please confirm or provide details for the following items so they can be accurately reflected in the final slides:

1. **Team Details**:
   - **Student 1:** Utkarsh Shah (Enrollment No. `241B278`)
   - **Student 2 & 3:** Are there teammates for this project, or is this an individual presentation? If team members exist, please provide their names and enrollment numbers.
2. **Supervisor / Guide Name**:
   - Please provide the faculty supervisor's name and designation (currently defaulted to placeholder `[Guide Name]`).
3. **Work Plan Weekly Status**:
   - The template includes a 10-week work plan table. By default, Weeks 1–6 will be marked **Completed**, Week 7 **In Progress**, and Weeks 8–10 **Pending**. Let us know if your official weekly log differs.

---

## Slide-by-Slide Outline (17 Slides)

The deck will strictly follow the 9 mandatory sections outlined in `PPT_Instructions.pdf` using the layout and theme of `Presentation format.pptx` (JUET Guna, 4:3 format):

| Slide # | Guideline Section | Slide Title | Visual / Structural Elements |
| :--- | :--- | :--- | :--- |
| **1** | Title Slide | **AI-Powered Resume Automation System** | Official JUET template layout, university logo, student details (Utkarsh Shah `241B278`), supervisor name. |
| **2** | Table of Contents | **Table of Contents** | 9-item structured agenda covering all mandatory departmental requirements. |
| **3** | 1. Introduction | **Project Overview & Objectives** | Dual-card layout: Project overview, key objectives, and end-to-end 8-stage pipeline badge. |
| **4** | 2. Problem Statement | **Problem Statement & Motivation** | Pain points breakdown (fragmented search, generic resumes, ATS rejections, uncontrolled auto-apply risks), core problem definition. |
| **5** | 3. Literature Review | **Existing Solutions & Comparative Analysis** | Summary of LoopCV, AIHawk, LinkedIn Auto Apply, and AI Job Search + Full comparative matrix table. |
| **6** | 3. Literature Review | **Research Gap & Proposed Improvement** | Identified limitations in existing tools vs. our hybrid multi-agent approach (deterministic verification + LLM language intelligence). |
| **7** | 4. Work Plan | **Project Work Plan & Milestones** | Structured academic table (Weeks 1 to 10) aligned with weekly reports: Problem Analysis → Architecture → Implementation → Evaluation. |
| **8** | 5. Individual Contribution | **Individual Contributions** | Department format table with member names, enrollment numbers, and specific architectural/development responsibilities. |
| **9** | 6. Work Done So Far | **System Architecture (Structural UML)** | High-level component architecture diagram built with clean native vector shapes: Frontend, Event-Driven Backend (FastAPI, Redis, Celery, PostgreSQL, FAISS), and AI Agent cluster. |
| **10** | 6. Work Done So Far | **End-to-End Workflow (Behavioral UML)** | 13-step sequence & state transition diagram: Resume Ingestion → Profile Cache → Discovery → Matching → Tailoring → Review Pipeline → Approval Gate → Extension Dispatch → Tracking. |
| **11** | 6. Work Done So Far | **Multi-User Database & AI Quality Pipeline** | Entity-Domain breakdown (Candidate, Job, Application, and Agent domains) + Drafter → Reviewer → Revision quality control loop. |
| **12** | 6. Work Done So Far | **Application UI: Copilot Dashboard & Resume Center** | High-resolution screenshots from `stitch_ai_career_copilot`: Clyde AI Copilot chat/status view & Resume management with ATS optimization cards. |
| **13** | 6. Work Done So Far | **Application UI: Job Discovery & ATS Analysis** | High-resolution screenshots from `stitch_ai_career_copilot`: Opportunity discovery cards with match scores & ATS keyword/skill gap analytics. |
| **14** | 7. Work to be Done | **Remaining Implementation & Testing Tasks** | Concrete next steps: Backend API completion, LLM prompt pipelines, browser extension site adapters, ATS benchmark testing, user evaluation. |
| **15** | 8. Conclusion | **Conclusion & Expected Outcomes** | Progress summary (design and UI phase complete), key outcomes (streamlined student application pipeline with safety controls), final takeaway. |
| **16** | 9. References | **References (IEEE Format)** | Full IEEE formatted citations for existing research and reference repositories. |
| **17** | Closure | **Thank You & Q&A** | Official JUET template closing slide with logo and Q&A prompt. |

---

## Technical Implementation Approach

1. **Presentation Generation Engine**:
   - Develop a Python automation script using `python-pptx` that loads `Presentation format.pptx` as the master template.
   - Preserve all slide master graphics, JUET logo, header ribbons, and color tokens (`#C0504D`, `#4F81BD`, `#366092`).
   - Automatically inject slide numbers into the template's designated orange marker on every slide.
2. **Diagram Generation**:
   - Construct architectural and workflow diagrams natively using PowerPoint shape primitives (rectangles, rounded pills, accent borders, connectors) to guarantee crisp rendering and 100% compliance with the no-AI-image rule.
3. **UI Screenshot Integration**:
   - Crop and embed actual UI screenshots from `stitch_ai_career_copilot/` (`screen.png` files) into slides 12 and 13 with polished frame styling and annotation labels.
4. **Validation & Visual Verification**:
   - Convert the generated `.pptx` to PDF via headless LibreOffice.
   - Render each slide to 150 DPI PNG using `pdftoppm`.
   - Visually inspect every slide image using `view_file` to ensure zero overlapping text, proper typography hierarchy, consistent margins, and clean alignment.

---

## Verification Plan

### Automated Generation & Visual Inspection
- Run the generation script: `python3 generate_ppt.py`
- Convert to PDF and PNGs: `soffice --headless --convert-to pdf "AI_Powered_Resume_Automation_Presentation.pptx"` and `pdftoppm -png -r 150`
- Inspect all 17 slide images to verify visual perfection, layout integrity, and readability.
- Verify that the resulting presentation opens cleanly in LibreOffice / PowerPoint.
