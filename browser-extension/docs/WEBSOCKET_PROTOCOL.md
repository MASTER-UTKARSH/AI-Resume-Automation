# Clyde WebSocket Communication Protocol Specification

## 1. Overview

The Clyde Browser Extension connects to the FastAPI backend via a bidirectional WebSocket connection at:
`ws://localhost:8000/api/extension/ws?client_id=<ID>&token=<SESSION_TOKEN>`

---

## 2. Message Envelope Format

All events exchanged over the WebSocket must conform to the strict JSON `EventEnvelope` schema:

```typescript
export interface EventEnvelope<T = Record<string, unknown>> {
  event_id: string;         // Unique event UUID (e.g., "evt-123456")
  event_type: EventType;    // Standard event type enum
  workflow_id: string;      // Current career workflow instance (e.g., "wf-app-901")
  task_id: string;          // Specific unit of work (e.g., "tsk-autofill-42")
  application_id?: string;  // Bound job application ID
  timestamp: string;        // ISO 8601 UTC timestamp
  payload: T;               // Strongly typed payload object
  correlation_id?: string;  // Trace identifier linking requests and responses
}
```

---

## 3. Event Catalog

### Backend to Extension Events

| Event Type | Description | Key Payload Fields |
| :--- | :--- | :--- |
| `INSPECT_PAGE` | Requests content script to scan DOM and classify page | `{ "tab_id": 101 }` |
| `PREPARE_APPLICATION` | Instructs extension to prepare candidate profile for current job | `{ "application_id": "app-1", "candidate_profile": {...} }` |
| `FILL_FORM` | Executes field autofill using candidate profile | `{ "application_id": "app-1", "fields": [...] }` |
| `UPLOAD_RESUME` | Instructs extension to attach approved resume file | `{ "application_id": "app-1", "resume_url": "...", "file_name": "resume.pdf" }` |
| `UPLOAD_COVER_LETTER` | Populates or uploads tailored cover letter | `{ "application_id": "app-1", "cover_letter_text": "..." }` |
| `SUBMIT_APPLICATION` | Submits form **only if approval token is present** | `{ "application_id": "app-1", "approval_token": "tok_xyz" }` |
| `CANCEL_TASK` | Halts currently running task | `{ "task_id": "tsk-1" }` |
| `HEALTH_CHECK` | Heartbeat ping from server | `{ "ping": 1732467000 }` |

### Extension to Backend Events

| Event Type | Description | Key Payload Fields |
| :--- | :--- | :--- |
| `EXTENSION_CONNECTED` | Initial handshake with client version & capabilities | `{ "client_id": "...", "version": "1.0.0" }` |
| `PAGE_DETECTED` | Emitted when tab loads a supported job portal | `{ "platform_name": "Greenhouse", "is_supported": true }` |
| `PAGE_INSPECTED` | Returns extracted DOM details and form presence | `{ "form_detected": true, "total_fields": 8 }` |
| `FORM_FILLED` | Summary of populated vs skipped fields | `{ "populated_count": 6, "skipped_count": 0 }` |
| `RESUME_UPLOADED` | Confirmation of file attachment | `{ "success": true, "file_name": "resume.pdf" }` |
| `APPROVAL_REQUIRED` | Alerts backend that human review is required | `{ "application_id": "app-1", "preview": {...} }` |
| `APPLICATION_COMPLETED`| Successfully submitted application | `{ "application_id": "app-1", "confirmation_text": "..." }` |
| `USER_ACTION_REQUIRED` | Halts automation for CAPTCHA / 2FA completion | `{ "reason": "Cloudflare Turnstile Detected" }` |
| `APPLICATION_FAILED` | Error report when task cannot proceed | `{ "error_code": "FIELD_MAPPING_FAILED", "message": "..." }` |

---

## 4. Reconnection and Failure Recovery

1. **Keep-Alive**: Heartbeat pings sent every 20 seconds.
2. **Backoff**: If connection drops, exponential backoff attempts reconnection up to 10 retries ($T_{\text{initial}} = 1000\text{ms}, T_{\text{max}} = 30000\text{ms}$).
3. **Token Cache**: Tokens stored in `chrome.storage.local` survive service worker restarts.

