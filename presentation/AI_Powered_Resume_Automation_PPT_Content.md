# Minor Project PPT Content Draft

## AI-Powered Resume Automation System

> **Purpose:** This document contains slide-by-slide content for
> creating the mandatory minor-project PowerPoint presentation.
>
> **Important:** The PPT must follow the department template and the
> official slide guidelines. UI screenshots will be inserted later. Do
> **not** use AI-generated images anywhere in the presentation.

------------------------------------------------------------------------

# Slide 1 --- Introduction

## AI-Powered Resume Automation System

### Project Overview

An AI-assisted job and internship application platform designed for
students and freshers. The system analyzes an uploaded resume, builds a
structured candidate profile, discovers relevant opportunities,
evaluates job fit, tailors application documents, and assists with the
application workflow.

### Objective

-   Reduce repetitive effort in job and internship searching.
-   Match candidates with relevant opportunities.
-   Improve resumes according to job descriptions and ATS requirements.
-   Maintain versioned, job-specific resumes and cover letters.
-   Automate supported application workflows while keeping the user in
    control of critical actions.

### Suggested Visual

Use the project workflow diagram: **Resume Upload → Job Discovery →
Matching → Resume Optimization → Review → Approval → Application →
Tracking**

------------------------------------------------------------------------

# Slide 2 --- Problem Statement

## Problem Statement

Students and freshers often face a fragmented and repetitive job
application process:

-   Searching across multiple job sources is time-consuming.
-   The same generic resume is frequently used for different job roles.
-   Job descriptions contain different skill and keyword requirements.
-   Manual tailoring of resumes and cover letters is repetitive.
-   Tracking multiple applications is difficult.
-   Fully automated application systems can perform unintended actions
    if no approval mechanism exists.

### Why Is This Important?

A student may need to evaluate and apply to many opportunities while
maintaining application quality. There is a need for a system that
combines **job discovery, candidate-job matching, document tailoring,
controlled automation, and application tracking** in one workflow.

### Core Problem Addressed

**How can AI and automation reduce repetitive job-application effort
while preserving relevance, accuracy, and user control?**

------------------------------------------------------------------------

# Slide 3 --- Literature Review: Existing Solutions

## Existing Work and Related Systems

### 1. LoopCV

-   Provides job-search and application automation features.
-   Demonstrates the value of automating repetitive job-search
    workflows.
-   Commercial products show that platform-specific automation is more
    practical than trying to support every website universally.

### 2. AIHawk / Jobs Applier AI Agent

-   Open-source project focused on AI-assisted job application
    automation.
-   Useful reference for application workflows, form filling, and
    handling application questions.

### 3. LinkedIn Auto Jobs Applier with AI

-   Demonstrates browser-based automation patterns for job application
    workflows.
-   Useful for studying form traversal and application automation.

### 4. AI Job Search

-   Demonstrates structured candidate information and AI-assisted job
    evaluation.
-   Introduces useful concepts such as draft-review-revision pipelines
    and verification of generated application documents.

### Suggested Visual

A comparison table:

  -----------------------------------------------------------------------------
  System /       Job Search       Resume   Auto Apply     Tracking         User
  Approach                     Tailoring                               Approval
  ------------ ------------ ------------ ------------ ------------ ------------
  Existing Job          Yes      Limited           No      Limited          N/A
  Boards                                                           

  Auto-Apply        Limited      Limited          Yes      Limited   Usually No
  Scripts                                                          

  Proposed              Yes          Yes    Supported          Yes          Yes
  System                                        Sites              
  -----------------------------------------------------------------------------

> Keep the table concise and avoid making unsupported claims about
> proprietary systems.

------------------------------------------------------------------------

# Slide 4 --- Literature Review: Research Gap and Proposed Improvement

## Identified Gaps

Existing approaches often focus on only one or two parts of the
workflow:

-   Job boards mainly focus on job discovery.
-   Auto-apply scripts focus mainly on form automation.
-   Resume tools focus on document generation.
-   Some systems provide automation without a clear approval and
    observability mechanism.

## Proposed Improvement

The proposed system combines these components into a single workflow:

-   Structured candidate profile
-   Multi-factor job matching
-   Resume versioning
-   ATS-oriented verification
-   Drafter → Reviewer → Revision pipeline
-   Hybrid approval system
-   Browser-extension-assisted application automation
-   Application and workflow tracking

### Key Design Principle

**Use AI for language understanding and generation; use deterministic
code for scoring, validation, storage, and workflow control wherever
possible.**

------------------------------------------------------------------------

# Slide 5 --- Work Plan

## Work Plan

> **Important:** Replace the status below according to the actual weekly
> reports before final submission.

  -----------------------------------------------------------------------
  Week                    Planned Work            Status
  ----------------------- ----------------------- -----------------------
  Week 1                  Problem identification  Completed\*
                          and requirement         
                          analysis                

  Week 2                  Literature review and   Completed\*
                          existing system         
                          analysis                

  Week 3                  Frontend architecture   Completed\*
                          and user workflow       
                          design                  

  Week 4                  Backend and multi-agent Completed\*
                          architecture design     

  Week 5                  Database schema and     Completed\*
                          browser-agent           
                          architecture            

  Week 6                  System workflow and     Completed\*
                          UML/sequence diagrams   

  Week 7                  Backend implementation  In Progress / Pending\*
                          setup                   

  Week 8                  Resume and job-matching Pending\*
                          module implementation   

  Week 9                  Browser automation and  Pending\*
                          integration             

  Week 10                 Testing, UI             Pending\*
                          integration, and        
                          evaluation              
  -----------------------------------------------------------------------

\* **Placeholder status. Must be aligned with actual weekly reports.**

------------------------------------------------------------------------

# Slide 6 --- Individual Contribution

## Individual Contribution

> Fill this slide after providing the project team details.

  -----------------------------------------------------------------------
  Member Name             Enrollment No.          Contribution
  ----------------------- ----------------------- -----------------------
  \[Member 1\]            \[Enrollment No.\]      System architecture,
                                                  backend, AI services,
                                                  or assigned work

  \[Member 2\]            \[Enrollment No.\]      \[Contribution\]

  \[Member 3\]            \[Enrollment No.\]      \[Contribution\]
  -----------------------------------------------------------------------

### Contribution Areas Available

-   Requirement analysis
-   Literature review
-   Frontend development
-   Backend development
-   Database design
-   AI/LLM integration
-   Browser extension
-   Testing and documentation

------------------------------------------------------------------------

# Slide 7 --- Work Done So Far: Structural Design

## System Architecture

### Finalized Architecture

**Frontend** - React + TypeScript web application - AI-agent dashboard -
Browser extension - Resume center - Job discovery - Application tracker

**Backend** - FastAPI - Event-driven multi-agent architecture - Redis
event queue - PostgreSQL - FAISS - Browser automation layer

**AI Services** - Orchestrator Agent - Resume Agent - Job Discovery
Agent - ATS Agent - Cover Letter Agent - Reviewer Agent - Application
Agent - Tracking Agent

### Suggested Visual

Insert the **System Architecture / Component Diagram** here.

> If a complete component diagram has not yet been created, use the
> high-level architecture flow from the Notion architecture document.

------------------------------------------------------------------------

# Slide 8 --- Work Done So Far: Behavioral Design

## End-to-End Workflow

### Workflow

1.  User uploads a resume.
2.  Resume Agent extracts structured candidate information.
3.  Candidate profile is stored for future reuse.
4.  Job Discovery Agent gathers jobs through supported source adapters.
5.  Multi-factor matching ranks relevant jobs.
6.  Resume is tailored to the selected job.
7.  ATS and Reviewer Agents evaluate the generated content.
8.  PDF-level verification checks the final document.
9.  A cover letter is generated and reviewed.
10. User approves or requests modifications.
11. Application Agent sends the approved task to the browser extension.
12. The application is submitted on a supported platform.
13. Tracking Agent records the application status.

### Suggested Visual

Insert the finalized **Workflow Diagram** from Notion.

------------------------------------------------------------------------

# Slide 9 --- Work Done So Far: Database and AI Workflow

## Data and AI Architecture

### Multi-User Database Design

**Candidate Domain** - Users - Resumes - Resume Versions - Candidate
Profiles - Skills - Education - Experience - Projects - Certifications -
Preferences

**Job Domain** - Companies - Job Sources - Jobs - Job Matches

**Application Domain** - Cover Letters - Applications - Application
Events

**Agent Domain** - Workflows - Agent Runs - Provider Health

### AI Quality Pipeline

**Drafter → Reviewer → Revision → Final Output**

The Reviewer Agent checks: - Unsupported claims - Missing relevant
keywords - Keyword stuffing - Relevance to the job description - Content
consistency - Formatting and structural issues

### Suggested Visual

Use an ER diagram or simplified database-domain diagram.

------------------------------------------------------------------------

# Slide 10 --- Work Done So Far: Application UI

## Application Interface

> **Placeholder until UI screenshots are available.**

Insert real screenshots of the developed application UI only.

### Recommended Screenshot Areas

1.  **AI-Agent Dashboard**
    -   Current tasks
    -   Agent activity
    -   Recent job matches
2.  **Resume Center**
    -   Uploaded resume
    -   Resume versions
    -   ATS feedback
3.  **Job Discovery**
    -   Job cards
    -   Match score
    -   Filters
4.  **Application Tracker**
    -   Application status
    -   Timeline
    -   Recent activity

### Brief Feature Explanation

-   Dashboard provides visibility into agent activities.
-   Resume Center manages resume versions and optimization results.
-   Job Discovery displays ranked opportunities.
-   Application Tracker records the status of submitted applications.

> **Do not use mock AI-generated screenshots. Use actual application
> screenshots when available.**

------------------------------------------------------------------------

# Slide 11 --- Work To Be Done

## Remaining Tasks

### Implementation

-   Set up the FastAPI backend and database.
-   Implement resume parsing and structured candidate profiles.
-   Implement source adapters for selected job sources.
-   Develop multi-factor job matching.
-   Implement resume tailoring and review workflow.
-   Implement ATS/PDF verification.
-   Develop the browser extension and supported platform adapters.
-   Integrate approval workflow.

### Testing and Evaluation

-   Test API/provider failure handling.
-   Test application workflow on supported platforms.
-   Measure job matching and document-quality results.
-   Perform integration and user testing.
-   Finalize documentation and presentation.

------------------------------------------------------------------------

# Slide 12 --- Conclusion

## Conclusion

The project has completed the major **analysis and architecture design
phase**.

### Progress So Far

-   Problem and workflow identified.
-   Existing solutions and useful reference implementations analyzed.
-   Frontend architecture finalized.
-   Event-driven multi-agent backend designed.
-   Multi-user database schema designed.
-   AI services and model routing designed.
-   Browser-agent architecture designed.
-   End-to-end workflow prepared.

### Expected Outcome

A prototype system that helps students and freshers:

-   Discover relevant opportunities.
-   Understand job-resume compatibility.
-   Create tailored and versioned application documents.
-   Review documents before final use.
-   Automate selected application workflows with user approval.
-   Track applications in one place.

### Final Takeaway

**The goal is not to replace the applicant's decisions; it is to
automate repetitive work and provide an intelligent, controlled
application workflow.**

------------------------------------------------------------------------

# Slide 13 --- References

## References (IEEE Format)

> Verify the exact repository version/access date required by your
> department before final submission.

\[1\] M. Lorentzen, "AI Job Search," GitHub repository. \[Online\].
Available: https://github.com/MadsLorentzen/ai-job-search. \[Accessed:
Sep. 4, 2026\].

\[2\] feder-cr, "Jobs Applier AI Agent AIHawk," GitHub repository.
\[Online\]. Available:
https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk. \[Accessed:
Sep. 4, 2026\].

\[3\] jomacs, "LinkedIn Auto Jobs Applier with AI," GitHub repository.
\[Online\]. Available:
https://github.com/jomacs/linkedIn_auto_jobs_applier_with_AI.
\[Accessed: Sep. 4, 2026\].

\[4\] S. Fer, "Career Ops," GitHub repository. \[Online\]. Available:
https://github.com/santifer/career-ops. \[Accessed: Sep. 4, 2026\].

\[5\] LoopCV, "LoopCV: Job Search Automation Platform." \[Online\].
Available: https://www.loopcv.pro/. \[Accessed: Sep. 4, 2026\].

------------------------------------------------------------------------

# Appendix --- Presenter Notes for Viva

## What is the main innovation of the project?

The project integrates candidate profiling, job matching, document
tailoring, quality review, controlled browser automation, and tracking
into one architecture targeted at students and freshers.

## Why use multiple agents?

Each agent has a focused responsibility. This improves modularity,
debugging, and future extensibility.

## Why not use an LLM for everything?

Deterministic tasks such as scoring, validation, database operations,
and workflow control are generally better handled by code. LLMs are used
mainly for understanding and generating language.

## Why Redis?

Redis supports temporary state, caching, and event-based communication
between workflow components.

## Why PostgreSQL?

The system contains strongly related multi-user data such as users,
resumes, jobs, applications, and workflow records. A relational database
is suitable for maintaining these relationships.

## Why FAISS?

FAISS is used for efficient similarity search over embeddings,
particularly as one component of semantic job matching.

## Is FAISS the complete matching system?

No. The final design uses multi-factor matching: - semantic
similarity, - required skills, - experience level, - location and
preferences, - role-specific constraints.

## Why a Reviewer Agent?

Generation alone is not sufficient. The reviewer stage checks relevance,
unsupported claims, keyword problems, and consistency before finalizing
application documents.

## Why is final submission not fully autonomous?

The project uses a hybrid approval system. Low-risk actions can be
automated, while critical actions---especially application
submission---require user approval.

## Why use a browser extension?

It can work with the user's existing browser session and login state,
reducing the need to store credentials or run paid cloud browsers.

## What is the V1 scope?

-   Company career pages
-   One major job board
-   One internship platform

The project intentionally supports a small number of platforms reliably
instead of attempting universal automation.

------------------------------------------------------------------------

# Information Still Needed Before Final PPT

Please provide:

1.  **Project title exactly as approved by the college**, if different
    from "AI-Powered Resume Automation System".
2.  **Team member names and enrollment numbers**.
3.  **Actual weekly report/work-plan status**, so Slide 5 matches
    official records.
4.  **Current implementation status**:
    -   Only architecture completed?
    -   Any frontend implemented?
    -   Any backend/API implemented?
    -   Any database created?
5.  **College PPT template**, if there is a separate template file.
6.  **UI screenshots** when available.

After receiving these, this draft can be converted into a final
PPT-ready version with exact slide content and screenshot placement.
