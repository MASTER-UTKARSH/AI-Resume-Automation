# CHAPTER 3: SYSTEM DESIGN AND METHODOLOGY

## 3.1 System Architecture

Clyde is split into four separate layers so no browser script talks directly to external websites or runs LLM inference on its own. Figure 3.1 shows the full path from the FastAPI backend down to the DOM of a company application form.

The API tier lives inside `backend/app/` on FastAPI. Requests from the web UI (`backend/app/static/index.html`) and WebSocket messages from Chrome enter through five routers (`agent.py`, `jobs.py`, `resumes.py`, `extension.py`, and `telemetry.py`) and publish events onto `EventBus` (`backend/app/core/event_bus.py`). `EventBus` tries to connect to Redis Pub/Sub with a one-second `socket_connect_timeout`. If Redis is not running locally, it falls back to an `asyncio` in-memory queue that keeps the last 50 events for the live telemetry panel.

Below the routers sits the service and ML layer (`backend/app/services/` and `backend/app/core/`). `PostingGuard` cleans uploaded PDFs and scraped job descriptions before `ResumeParser` writes candidate data into a 19-table SQLAlchemy database. `VectorStore` (`backend/app/services/vector_store.py`) manages two FAISS `IndexFlatIP` files (`jobs.faiss` and `resumes.faiss`) using 128-dimensional L2-normalized vectors. `MatchingEngine` combines vector similarity with rule checks and `GhostJobDetector` penalties, while `ModelRouter` runs the two-stage Drafter-Reviewer tailoring loop checked by `FactVerifier`.

The browser tier runs inside the user's Chrome profile as a Manifest V3 TypeScript extension (`browser-extension/`). `WebSocketManager` keeps an authenticated connection open using short-lived tokens from `GET /extension/token`. `MessageRouter` checks `task_id` values against `TaskManager` to avoid duplicate runs, finds the target tab, and sends commands (`CMD_INSPECT_PAGE`, `CMD_FILL_FORM`, `CMD_UPLOAD_RESUME`) to the content script. Portal adapters (`GreenhouseAdapter`, `LeverAdapter`, `WorkdayAdapter`, `LinkedInJobsAdapter`, `SimplifyJobsAdapter`, and `GenericJobAdapter`) pass DOM fields to `FormMapper` and `AutofillEngine`, and `SubmissionEngine` stops on a human confirmation dialog before any submit button is clicked.

## 3.2 Design Methodology

Building around a student's actual application workflow led to four design choices:

1. Server-side reasoning, browser-side execution: All job ranking, prompt building, PDF compilation, and fact checking stay in FastAPI. Chrome scripts only inspect inputs, set DOM values, attach approved PDFs, and read confirmation banners. Keeping selection logic out of content scripts protects API keys and lets us run backend unit tests without opening a browser.
2. Deterministic field matching first: Instead of sending full HTML pages to an LLM to locate "Phone" or "LinkedIn" inputs, `FormMapper` checks an ordered list of regex rules over `<label for>`, enclosing `<label>`, `placeholder`, `name`, `id`, ARIA attributes, and preceding sibling elements. Ambiguous inputs get low confidence scores and stay blank for manual entry.
3. Factual grounding over fluent rewrites: LLMs tend to invent percentages when asked to strengthen a bullet. Every tailored section goes through `FactVerifier` (`backend/app/services/fact_verifier.py`) before `LatexExporter` builds a PDF. Any unverified number or banned buzzword stops the export.
4. Non-bypassable user approval gate: `SubmissionEngine.executeSubmission` requires `approved_by_user: true` tied to the active `application_id` and immediately pauses with `NEEDS_USER_ACTION` if reCAPTCHA, hCaptcha, Cloudflare Turnstile, or an OTP field is detected.

## 3.3 Data Flow and UML Diagrams

### 3.3.1 Data Flow Diagram (Level 0 and Level 1)

Figure 3.2 traces how data moves through the platform. At Level 0 (Context View), the student uploads a base resume PDF and sets career preferences, receives ranked jobs and tailored LaTeX/PDF resumes, and reviews autofilled Chrome forms before submitting. External actors include live job portals/Apify actors for discovery and company career pages in the browser.

At Level 1, six processes handle the pipeline:
- Process 1.0 (Ingestion & Guard): `ResumeParser` and `JobScraperService` extract text and pass it through `PostingGuard.clean_text` before saving records to SQLite/PostgreSQL.
- Process 2.0 (Indexing & Ranking): `VectorStore` builds 128-D embeddings and `MatchingEngine` computes the weighted score with `GhostJobDetector` adjustment.
- Process 3.0 (Tailoring & Verification): `ModelRouter.orchestrate_drafter_reviewer` aligns project bullets with the job description and runs `FactVerifier.audit_tailored_resume`.
- Process 4.0 (LaTeX & PDF Generation): `LatexExporter` escapes special LaTeX characters and calls Tectonic to build the single-column ATS PDF.
- Process 5.0 (Extension Dispatch): `ExtensionConnectionManager` sends `FILL_FORM` and `UPLOAD_RESUME` messages over WebSockets to the Chrome background service worker.
- Process 6.0 (Approval & Tracking): `SubmissionEngine` shows the `ApplicationPreview` payload; after user approval and submission, `ResultCapture` updates the `Application` status in the database.

### 3.3.2 Use Case Diagram

Figure 3.3 shows interactions between three actors: Candidate Student, Backend Agent System, and Target ATS Portal. Student actions include profile setup, PDF upload, skill verification, triggering live scrapes, approving tailored bullets, and checking Chrome form previews. Backend services run sanitization, FAISS retrieval, ghost filtering, fact auditing, and LaTeX builds. External portals expose form DOM elements and return submission confirmations.

### 3.3.3 Sequence Diagram

Figure 3.4 shows the message flow from picking a matched role in the web console to completing an autofill in Chrome. FastAPI loads the student profile, runs tailoring through `ModelRouter` (Groq/Qwen/GLM/Ollama), verifies every line in `FactVerifier`, compiles the PDF with Tectonic, sends `FILL_FORM` and `UPLOAD_RESUME` over `/extension/ws`, waits for `DOMUtils.setInputValue` and `DataTransfer` in the content script, and blocks at `SubmissionEngine` until the student approves submission.

### 3.3.4 Class Diagram

Figure 3.5 maps the main Python and TypeScript classes. On the backend, `EventBus`, `PostingGuard`, `MatchingEngine`, `GhostJobDetector`, `ModelRouter`, `FactVerifier`, and `LatexExporter` read and write SQLAlchemy ORM models through service interfaces. In the extension, `WebSocketManager` and `MessageRouter` coordinate `PlatformRegistry`, site adapters extending `BasePlatformAdapter`, `FormMapper`, `AutofillEngine`, `ResumeUploadEngine`, and `SubmissionEngine`.

### 3.3.5 Entity-Relationship (ER) Diagram

Figure 3.6 models the 19 SQLAlchemy tables defined in `backend/app/database/models.py`:
- User and candidate domain: `users`, `resumes`, `resume_versions`, `candidate_profiles`, `candidate_skills`, `candidate_education`, `candidate_experience`, `candidate_projects`.
- Discovery and matching domain: `companies`, `job_sources`, `jobs`, `job_matches`.
- Application and tracking domain: `cover_letters`, `applications`, `application_events`.
- Workflow and telemetry domain: `workflows`, `agent_runs`, `provider_health`, `embedding_references`.

Every `resume_version` points back to its parent `Resume` so `FactVerifier` always checks against original source records rather than an earlier AI draft.

---

# CHAPTER 4: SYSTEM IMPLEMENTATION AND TESTING

## 4.1 Tools and Technologies Used

Table 4.1 lists the software stack used in our development and test environment.

**Table 4.1: Software Stack and Dependencies**

| Layer | Component | Tool / Version / Configuration |
| :--- | :--- | :--- |
| Backend Runtime | Web Framework & ASGI Server | Python 3, FastAPI, Uvicorn (`0.0.0.0:8000`) |
| Relational Storage | ORM & Database | SQLAlchemy 2.x, SQLite (`clyde.db`, 19 tables) |
| Event Messaging | Pub/Sub & Local Failover | Redis (`redis.asyncio`, 1s connect timeout) + `asyncio.Queue` |
| Vector Retrieval | Similarity Index | FAISS (`faiss.IndexFlatIP`, 128-D L2-normalized vectors) |
| PDF & Document Engine | Parsing & Typesetting | PyPDF (`PdfReader`), Tectonic CLI, Jake's Resume LaTeX template |
| LLM Providers | Hybrid Model Routing | Groq (`qwen/qwen3.8-27b`), GLM, Qwen, Ollama local fallback |
| Web Scraping | Live Role Discovery | HTTPX + Apify Naukri/ATS feed with `PostingGuard` filter |
| Browser Extension | Client Automation | Chrome Manifest V3, TypeScript 5.x, Vite bundler |
| Automated Testing | Backend & Extension Suites | `unittest` (24 backend tests), Vitest + JSDOM (24 TS tests) |

## 4.2 Implementation Details

### 4.2.1 Resume Parsing and Adversarial Sanitization (`ResumeParser` & `PostingGuard`)

When a student uploads a PDF to `POST /resumes/upload`, `ResumeParser` (`backend/app/services/resume_parser.py`) reads the text with `PdfReader` and falls back to raw UTF-8 decoding for plain text files or broken headers. Regular expressions pull out email addresses, phone numbers, CGPA values, and technical skills matched against a 35-term engineering lexicon (`Python`, `FastAPI`, `PyTorch`, `FAISS`, `Docker`, `Redis`, etc.). Early in testing we noticed raw `PdfReader` output sometimes splits words across columns or leaves hidden zero-width spaces, so every extracted string passes through `PostingGuard.clean_text` before hitting the database.

`PostingGuard` (`backend/app/core/posting_guard.py`) sanitizes PDFs and scraped web pages in four steps:
1. Stripping invisible Unicode characters including `U+200B`–`U+200F`, bidirectional overrides (`U+202A`–`U+202E`), and Unicode tag sequences (`U+E0000`–`U+E007F`).
2. Removing hidden HTML elements using CSS rules like `display:none`, `visibility:hidden`, `opacity:0`, or `font-size:0px`.
3. Running 10 regex patterns for indirect prompt injections (such as `"ignore previous instructions"`, `"act as admin"`, `"system prompt"`, `"always hire"`).
4. Catching mixed-script Cyrillic or Greek homoglyphs inside Latin words and flagging links outside known ATS domains (`greenhouse.io`, `lever.co`, `myworkdayjobs.com`, `ashbyhq.com`, `smartrecruiters.com`, `workable.com`, `icims.com`).

### 4.2.2 Vector Indexing and Four-Factor Hybrid Ranking (`VectorStore`, `MatchingEngine`, `GhostJobDetector`)

Job descriptions and candidate profiles are mapped to 128-dimensional vectors inside `VectorStore` (`backend/app/services/vector_store.py`). To avoid downloading large transformer weights onto student laptops, `VectorStore._embed_text` hashes lowercase tokens into MD5 and SHA-256 buckets, adds a +2.0 weight boost for core engineering frameworks, and divides by the L2 norm (using a `1e-9` floor so blank inputs do not divide by zero). Vectors are stored in two `faiss.IndexFlatIP` files (`data/faiss/jobs.faiss` and `resumes.faiss`). Since every vector is unit length, inner product in `IndexFlatIP` gives exact cosine similarity.

`MatchingEngine` (`backend/app/services/matching_engine.py`) combines four sub-scores instead of relying on vector distance alone:
- Semantic similarity (`WEIGHT_SEMANTIC = 0.40`) from the normalized dot product.
- Direct skill overlap (`WEIGHT_SKILLS = 0.30`) counting how many required job skills exist in the student's profile.
- Experience fit (`WEIGHT_EXPERIENCE = 0.15`) scoring student and fresher roles at full weight while discounting senior roles (`5+ years`).
- Location preference (`WEIGHT_PREFERENCE = 0.15`) checking remote compatibility and preferred cities (`Bangalore`, `Hyderabad`, `Pune`, `Noida`, `Gurgaon`, `Remote`).

The weighted score is multiplied by `penalty_multiplier` from `GhostJobDetector` (`backend/app/services/ghost_detector.py`), which checks repost counts over 90 days, days active past 35 or 60 days, non-ATS hosts, and applicant silence counts. Listings marked `LIKELY` lose 25% (`0.75`), `POSSIBLE` lose 10%, `LOW_RISK` lose 5%, and final percentages clamp to `[15.0, 98.5]`.

### 4.2.3 Model Routing, Fact Verification, and LaTeX Compilation

`ModelRouter` (`backend/app/core/model_router.py`) routes LLM requests across `groq` (`qwen/qwen3.8-27b`), `glm`, `qwen`, and local `ollama` backends based on task type (`writing`, `reasoning`, `fast`, `local`) and sends latency metrics to `EventBus`. In `orchestrate_drafter_reviewer`, a drafting model aligns project bullets with the job description, a reviewing model trims phrasing to keep single-line ATS balance, and `FactVerifier.audit_tailored_resume` checks the draft against the saved profile.

`FactVerifier` (`backend/app/services/fact_verifier.py`) runs three checks:
1. Numeric provenance (`QUANT_METRIC_REGEX`): pulls every percentage, dollar value, millisecond timing, multiplier (`2x`), and suffix (`10k`) from the draft and rejects any number absent from the base profile.
2. Buzzword filter (`FORBIDDEN_BUZZWORDS`): flags clichés like `"synergy"`, `"rockstar"`, `"ninja"`, `"thought leader"`, `"best-in-class"`, `"disruptive"`, and `"dynamic self-starter"`.
3. Vocabulary integrity: warns when capitalized engineering acronyms or tools not present in the source text show up in tailored bullets.

Approved profiles go to `LatexExporter` (`backend/app/services/latex_exporter.py`), which escapes all 10 special LaTeX characters (`\`, `&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`), turns Markdown bold (`**...**`) into `\textbf{...}`, populates the single-column Jake's Resume / `sb2nov` template, and compiles the PDF with `tectonic`.

### 4.2.4 Chrome Manifest V3 Extension & Platform Adapter Registry

Figure 4.1 shows the extension's internal flow. Because Chrome Manifest V3 kills idle service workers without warning, `WebSocketManager` (`browser-extension/src/background/websocket-manager.ts`) reloads the session token from `chrome.storage.local`, connects to `ws://localhost:8000/extension/ws`, sends periodic heartbeats, and reconnects with exponential backoff and jitter. `MessageRouter` tracks `task_id` values in `TaskManager` so retries never fill a form twice.

`PlatformRegistry` runs `detect(url, doc)` across six adapter classes (`GreenhouseAdapter`, `LeverAdapter`, `WorkdayAdapter`, `LinkedInJobsAdapter`, `SimplifyJobsAdapter`, and `GenericJobAdapter`). Each adapter calls `FormMapper` (`browser-extension/src/automation/form-mapper.ts`), which checks `label[for]`, parent `<label>`, `placeholder`, `name`, `id`, `aria-label` / `aria-labelledby`, preceding sibling nodes, and adapter-specific selectors. `AutofillEngine` writes values via `DomUtils.setInputValue`. Assigning `el.value = ...` directly fails on React portals because React wraps native input setters; `DomUtils.setInputValue` calls the native `HTMLInputElement.prototype` setter descriptor and dispatches `input`, `change`, and `blur` events. Resume PDFs attach to `<input type="file">` inputs via the `DataTransfer` API, followed by a 200 ms check. `SubmissionEngine` always enforces `requires_user_approval = true` on `ApplicationPreview`.

## 4.3 Testing Methods

We tested the system at three levels: Python backend unit tests (`unittest`), TypeScript extension tests (`Vitest` + `JSDOM`), and live end-to-end runs in BrowserOS Neo on a local application page (`http://localhost:3000/standard-job-form.html`). Backend tests checked SQLite/PostgreSQL table creation, PDF parsing, `PostingGuard` injection blocking, FAISS ranking, ghost penalties, `FactVerifier` rejections, `LatexExporter` escaping, and API round-trips. Extension tests checked all eight `FormMapper` rules, React setter events, `SubmissionEngine` CAPTCHA and approval locks, `PlatformRegistry` routing, and WebSocket message parsing.

## 4.4 Test Results

All automated and manual checks passed after final fixes. Table 4.2 lists the test coverage and results.

**Table 4.2: Automated and End-to-End Verification Results**

| Test Suite / Case ID | Target Module | Test Focus | Result |
| :--- | :--- | :--- | :--- |
| Backend Suite (`unittest`, 24 tests) | `backend/tests/` (`7` files) | DB schema, PDF parse, FAISS match, LaTeX escape, API workflow | 24/24 Passed |
| `form-mapper.test.ts` (Vitest) | `FormMapper` | 8-level label/ARIA/placeholder/sibling mapping rules | Passed |
| `autofill-engine.test.ts` (Vitest) | `AutofillEngine` & `DomUtils` | Native setter dispatch, `<select>`, checkbox/radio verification | Passed |
| `submission-security.test.ts` (Vitest) | `SubmissionEngine` | Blocks missing approval, token mismatch, CAPTCHA/OTP iframes | Passed |
| `platform-detection.test.ts` (Vitest) | `PlatformRegistry` | Greenhouse, Lever, Workday, LinkedIn, generic adapter routing | Passed |
| `websocket-protocol.test.ts` (Vitest) | `MessageRouter` | Typed event envelopes and `task_id` deduplication | Passed |
| Live BrowserOS Neo Run | Full System + MV3 Extension | Web chat tailoring + mock portal autofill & PDF upload | 8/8 Fields Filled |

During live testing on BrowserOS Neo at `http://localhost:3000/standard-job-form.html`, the extension attached `Utkarsh_Shah_Resume.pdf` via `DataTransfer`, populated eight form fields (`filled_count: 8`, `failed_count: 0`), and stopped with `requires_user_approval: true`.

The screenshots from these runs show each stage working end-to-end. Figure 4.2 shows the Resume Library where uploaded PDFs are parsed and scored. Figure 4.3 shows the Job Discovery Console with ranked openings and `PostingGuard` domain badges. Figure 4.4 shows the Clyde chat running a live Apify job scrape and tailoring prompt, and Figure 4.5 shows the compiled single-column `sb2nov` LaTeX resume modal. Figure 4.6 displays the live `EventBus` telemetry stream (`Groq`, `GLM`, `Qwen`), and Figure 4.7 shows the Chrome extension autofill and pre-submit confirmation prompt in BrowserOS Neo.
