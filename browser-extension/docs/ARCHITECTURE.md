# Clyde AI Browser Agent Extension - Architecture

## 1. High-Level System Architecture

```
                    +------------------------------------+
                    |        FastAPI Backend Core        |
                    |  (Orchestrator & Application Agent)|
                    +-----------------+------------------+
                                      |
                      WebSocket Event Protocol (JSON)
                      ws://localhost:8000/api/extension/ws
                                      |
                                      v
+--------------------------------------------------------------------------+
|                  Chrome Browser Extension (Manifest V3)                  |
|                                                                          |
|  +--------------------------------------------------------------------+  |
|  |                 Background Service Worker                          |  |
|  |  - WebSocket Manager (Exponential Backoff + Jitter)                |  |
|  |  - Task Lifecycle Manager (Deduplication + Human-in-the-Loop Gate) |  |
|  |  - Message Router (Active Tab Resolution & Dispatch)               |  |
|  +---------------------------------+----------------------------------+  |
|                                    |                                     |
|                   Chrome Runtime Port / Message Passing                  |
|                                    |                                     |
|                                    v                                     |
|  +--------------------------------------------------------------------+  |
|  |                 Content Script Execution Layer                     |  |
|  |                                                                    |  |
|  |   +-----------------------+     +-------------------------------+  |  |
|  |   |   Platform Detector   | --> |     Platform Registry         |  |  |
|  |   +-----------------------+     +---------------+---------------+  |  |
|  |                                                 |                     |  |
|  |                                     Active Platform Adapter           |  |
|  |                                                 v                     |  |
|  |   +-----------------------+     +-------------------------------+  |  |
|  |   |   8-Strategy Mapper   | <-> |    Autofill & Upload Engines  |  |  |
|  |   +-----------------------+     +---------------+---------------+  |  |
|  |                                                 |                     |  |
|  |                                                 v                     |  |
|  |                                 +-------------------------------+  |  |
|  |                                 |   Submission Security Gate    |  |  |
|  |                                 | (Token Match + User Approval) |  |  |
|  |                                 +-------------------------------+  |  |
|  +--------------------------------------------------------------------+  |
+--------------------------------------------------------------------------+
                                      |
                                      v
                            +--------------------+
                            | Job Portal Webpage |
                            |  (DOM Elements)    |
                            +--------------------+
```

---

## 2. Core Architectural Principle

> **"Backend decides WHAT to do. Browser Extension executes HOW to do it."**

The browser extension is solely an execution layer. It does not make career decisions, scrape independently without direction, or generate fabricated content. It receives task plans over a secured WebSocket channel, inspects the current DOM, presents a structured preview to the user, and executes DOM actions safely.

---

## 3. Chrome Manifest V3 Compliance & Service Worker Lifecycle

In Manifest V3, background pages are replaced with event-driven Service Workers which can terminate when idle (approx. 30 seconds of inactivity).

### Mitigations Built Into Clyde Extension:
1. **Stateless Connection Resilience**:
   The `WebSocketManager` stores session tokens and active task IDs in `chrome.storage.local`. Upon service worker resurrection, it immediately restores connection state and queries active tabs.
2. **Exponential Backoff with Random Jitter**:
   Reconnection follows:
   $$\text{delay} = \min(T_{\text{initial}} \times 1.8^{\text{attempt}}, T_{\text{max}}) \pm \text{jitter}$$
   preventing thundering herd problems on backend restarts.
3. **Structured Tab Targeting**:
   Tasks bind to explicit tab IDs. If a tab navigates or closes, the task manager cleans up and reports `TASK_CANCELLED` to the backend.

---

## 4. Subsystem Breakdown

### A. Platform Detector & Registry
- Evaluates URLs against regular expressions and DOM structural fingerprints.
- Dispatches execution to specialized adapters (`GreenhouseAdapter`, `LeverAdapter`, `WorkdayAdapter`, `LinkedInJobsAdapter`, `SimplifyJobsAdapter`).
- Gracefully falls back to `GenericJobAdapter` when a site has job application form markup.

### B. Form Mapper (8-Level Heuristic Hierarchy)
Maps DOM inputs deterministically without expensive LLM roundtrips:
1. Associated `<label for="...">`
2. Enclosing `<label>`
3. `placeholder` attribute
4. `name` attribute
5. `id` attribute
6. `aria-label` / `aria-labelledby`
7. Sibling and parent contextual text
8. Platform-specific selector fallbacks

### C. DOM Autofill Engine
- Employs native prototype setters (`HTMLInputElement.prototype.value`) so that React, Vue, and Angular internal fiber state registers changes.
- Dispatches standard bubbling `input` and `change` events.
- Never fabricates information: missing fields are reported as unfilled.

### D. Submission Security Gate
- **Enforces explicit human approval**: Under no circumstances will the extension submit an application automatically without the user clicking "Approve Submission" in the Clyde UI.
- Validates cryptographic approval token binding `application_id`.
- Automatically halts when human verification gates (CAPTCHA, Turnstile, hCaptcha, MFA) are present, prompting the candidate to complete the check.

