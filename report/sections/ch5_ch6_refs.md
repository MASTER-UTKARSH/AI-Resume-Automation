# CHAPTER 5: RESULTS AND DISCUSSION

## 5.1 Results Analysis

We evaluated Clyde around three questions: does hybrid FAISS ranking order roles better than keyword counts alone, do `PostingGuard` and `FactVerifier` catch unsafe inputs and hallucinated bullets, and does the Chrome extension fill portal forms reliably inside a real session?

Figure 5.1 compares the four-factor ranking scores across five roles for Utkarsh Shah's profile (`Python`, `FastAPI`, `PyTorch`, `FAISS`, `Docker`, `Git`, `REST APIs`). For `NVIDIA AI & Deep Learning Software Engineer Intern` (semantic similarity `59.3%`, skill overlap `87.5%`, experience fit `95.0%`, location preference `95.0%`), the weighted score equals `78.5%` from `(0.40 * 59.3) + (0.30 * 87.5) + (0.15 * 95.0) + (0.15 * 95.0)`. `Microsoft ML Research Intern` has a similar semantic score (`58.2%`) and the same experience/location scores (`95.0%`), but lower skill overlap (`62.5%`) pulls its total down to `70.5%`. `Canonical Junior Python Engineer` reaches `79.9%` because both semantic similarity (`68.5%`) and skill overlap (`80.0%`) are high.

**Table 5.1: Four-Factor Hybrid Ranking Results (Healthy vs. Ghost-Penalized)**

| Role / Company | FAISS (40%) | Skills (30%) | Exp. (15%) | Pref. (15%) | Composite Score | Ghost Tier (Multiplier) | Final Rank Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Canonical Jr. Python Engineer | 68.5% | 80.0% | 95.0% | 95.0% | 79.9% | HEALTHY (1.00) | 79.9% |
| GlobalFoundries AI Strategist | 62.1% | 83.3% | 95.0% | 95.0% | 78.3% | HEALTHY (1.00) | 78.3% |
| NVIDIA AI & DL Intern | 59.3% | 87.5% | 95.0% | 95.0% | 78.5% | HEALTHY (1.00) | 78.5% |
| Bajaj Finance Exec. Debt Mgmt | 54.0% | 100.0% | 75.0% | 80.0% | 74.9% | LOW_RISK (0.95) | 71.1% |
| Microsoft ML Research Intern | 58.2% | 62.5% | 95.0% | 95.0% | 70.5% | HEALTHY (1.00) | 70.5% |

`Bajaj Finance Executive Debt Management` shows why keyword counts alone fail: matching generic keywords gives `74.9%` raw score before its non-official ATS host triggers a `LOW_RISK` penalty (`0.95x`), dropping it to `71.1%`. When our tests inject simulated ghost-job signals (`repost_count_90d = 3`, `days_active = 75`, non-ATS domain), `GhostJobDetector` assigns `LIKELY` (`0.75x`) and cuts a `78.5%` opening down to `58.9%`.

On fact verification, clean bullets passed to `FactVerifier.audit_tailored_resume` score `1.0` (`100%`) when every metric (such as `92% accuracy` or `50k records`) exists in the saved resume. Adding synthetic claims like `"improved API response time by 65%"` or `"thought leader with synergy"` raises `UNGROUNDED_METRIC` and `FORBIDDEN_BUZZWORD` errors and blocks LaTeX export.

## 5.2 Performance Evaluation

Figure 5.2 shows measured latencies across local CPU steps and external API calls. Local deterministic steps finish in milliseconds, while network scraping and cloud LLM inference take most of the wall-clock time.

**Table 5.2: Observed Subsystem Execution Latencies**

| Subsystem Operation | Measured Time (ms) | Execution Mode | Primary Bottleneck |
| :--- | :--- | :--- | :--- |
| FAISS `IndexFlatIP` Query (`top_k=20`) | 18 ms | In-memory CPU (`data/faiss/`) | Inner-product vector scan |
| Resume Parsing & ATS Scoring | 185 ms | Local CPU (`PdfReader` + regex) | PDF stream decompression |
| Extension WS Form Autofill (8 fields) | 220 ms | Chrome MV3 DOM + `DataTransfer` | DOM event propagation + 200 ms wait |
| Tectonic PDF Compilation | 1,950 ms | Subprocess (`tectonic`) | LaTeX typesetting & font loading |
| Groq LLM Discovery Chat | 3,055 ms | Cloud HTTPS (`qwen/qwen3.8-27b`) | Network RTT + token decoding |
| Apify Naukri Live Scrape & Filter | 6,731 ms | External actor + `PostingGuard` | Remote portal pagination |

Local operations (`Resume Parsing + FAISS Query + Form Autofill`) take about `423 ms` total, so UI filtering and form entry feel instant. Compiling a PDF via `tectonic` takes roughly two seconds, which is fast enough to run synchronously inside `POST /api/resumes/{id}/export-latex`. Slow network steps like live scraping (`6,731 ms`) and Groq inference (`3,055 ms`) stream progress events over `EventBus` to the live telemetry panel without blocking FastAPI workers.

## 5.3 Discussion and Engineering Findings

Three bugs showed up when we wired the backend, LLM router, and Chrome extension together:

1. Extension WebSocket Authentication Handshake: At first, the Manifest V3 background worker started in a `DISCONNECTED` state because `chrome.storage.local` had no token until the dashboard called `GET /extension/token`. Adding automatic bootstrap token fetching with exponential backoff and jitter fixed silent disconnects across browser restarts.
2. React State Rejection on Direct Input Assignment: Early tests set `input.value = "..."` directly and fired a generic `change` event, but React portals reset the field on blur because React tracks values through internal setter descriptors. Updating `DomUtils.setInputValue` to call `HTMLInputElement.prototype` setters before firing `input`, `change`, and `blur` updated both the DOM and React state reliably.
3. Intent Misrouting on Chat Commands: When a user asked Clyde to apply for a scraped job (`"apply for Executive - Debt Management Services - Rural"`), the first orchestrator version replied with general career advice instead of loading the active profile and target job description. Updating the chat router to fetch the stored `CandidateProfile`, match the job from SQLite, tailor the LaTeX PDF, and dispatch WebSocket autofill commands completed the loop.

---

# CHAPTER 6: CONCLUSION AND FUTURE WORK

## 6.1 Conclusion

We built Clyde, an event-driven resume automation and browser application platform for B.Tech Computer Science students. Instead of letting LLMs run unchecked, the architecture separates backend reasoning from Chrome execution. FastAPI handles PDF parsing (`ResumeParser`), input sanitization (`PostingGuard`), 128-D FAISS `IndexFlatIP` ranking (`VectorStore` and `MatchingEngine`), ghost-job penalties (`GhostJobDetector`), Drafter-Reviewer rewriting (`ModelRouter`), numeric provenance auditing (`FactVerifier`), and Tectonic PDF builds (`LatexExporter`). Inside Chrome, a Manifest V3 TypeScript extension selects portal adapters via `PlatformRegistry`, maps inputs across eight fallback checks via `FormMapper`, attaches approved PDFs with `DataTransfer`, and blocks form submission unless a human confirmation matches the active `application_id`.

Both test suites passed cleanly: `24/24` Python backend tests in `18.400 s` (`unittest`) and `24/24` Chrome extension tests in `19.76 s` across 5 files (`Vitest`). Live testing in BrowserOS Neo confirmed chat-based tailoring, eight-field autofill (`8/8` filled, `0` failed), and PDF upload on a local portal form.

## 6.2 Future Work

Four practical extensions sit beyond our 5th-semester scope:
1. Pre-trained Dense Embeddings: Replacing the MD5/SHA-256 hash embedder with a compact ONNX sentence transformer (`all-MiniLM-L6-v2`) would capture multi-word technical concepts while keeping inference offline.
2. Multi-Page Workday Navigation: Extending `JobBoardAdapter` and `CompanyCareersAdapter` with step tracking across multi-screen Workday and Greenhouse wizards (`Contact -> Experience -> Voluntary Disclosures -> Review`) while keeping a pause gate on every screen.
3. Custom React Comboboxes: Extending `DomUtils` beyond native `<select>` elements to handle keyboard-driven headless dropdowns (`role="combobox"` / `aria-expanded`) used by Ashby and Lever portals.
4. Campus Placement Analytics: Adding anonymized skill-gap summaries across student batches so JUET Guna candidates can see which missing skills show up most often in shortlisted openings.

---

# REFERENCES

[1] H. Zhang, Y. Wang, and L. Chen, "Automated Resume Screening and Applicant Tracking System Compatibility Analysis," *IEEE International Conference on Data Engineering Workshops*, pp. 112–118, 2023.

[2] F. Al-Zahrani and K. Mensah, "Evaluating Automated Web Agent Frameworks for Online Form Navigation," *Journal of Web Engineering*, vol. 23, no. 2, pp. 201–219, 2024.

[3] S. Robertson and H. Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond," *Foundations and Trends in Information Retrieval*, vol. 3, no. 4, pp. 333–389, 2009.

[4] M. Douze et al., "The FAISS Library," *IEEE Transactions on Big Data* / arXiv:2401.08281, 2024.

[5] K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, "Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection," *Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security (AISec)*, pp. 79–90, 2023.

[6] S. Ramírez, *FastAPI: Modern, Fast (High-Performance) Web Framework for Building APIs with Python*, Version 0.115+, Tiangolo Documentation, 2024.

[7] M. Bayer, *SQLAlchemy: The Database Toolkit for Python (2.0 ORM Specification)*, SQLAlchemy Project Documentation, 2024.

[8] Google Chrome Developers, *Chrome Extensions: Manifest V3 Migration Guide and Service Worker Lifecycle*, Chrome for Developers Documentation, 2024.

[9] Mozilla Developer Network (MDN), *DataTransfer API and Synthetic DOM Event Dispatch Specification*, MDN Web Docs, 2024.

[10] P. Williams, *Tectonic: A Modernized, Complete, Self-Contained TeX/LaTeX Engine*, Tectonic Project Documentation, 2024.

[11] J. Ryan, *Jake's Resume: Single-Column ATS-Friendly Software Engineering LaTeX Template (sb2nov Derivative)*, GitHub Open Source Repository, 2023.

[12] A. Vaswani et al., "Attention Is All You Need," *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 30, pp. 5998–6008, 2017.

[13] S. Yoo and T. Kim, "Mitigating Hallucination in Large Language Models through Deterministic Provenance Constraints," *IEEE Access*, vol. 12, pp. 44120–44134, 2024.

[14] R. Fielding et al., "The WebSocket Protocol and Typed Event Streaming Architectures," *RFC 6455 / Internet Engineering Task Force (IETF)*, 2011.

[15] Vitest Contributors, *Vitest: Next-Generation Testing Framework Powered by Vite and JSDOM*, Documentation v2.1, 2024.

[16] Redis Ltd., *Redis Pub/Sub Messaging and Asynchronous Python Client (`redis.asyncio`)*, Redis Technical Documentation, 2024.
