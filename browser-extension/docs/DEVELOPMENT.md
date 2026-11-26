# Clyde Browser Extension - Developer Setup & Testing Guide

## 1. Prerequisites

- **Node.js**: v18 or later
- **npm**: v9 or later
- **Google Chrome** or Chromium-based browser (Brave, Edge)
- **FastAPI Backend**: Clyde core running on `http://localhost:8000`

---

## 2. Build Instructions

Navigate to the extension directory and build:

```bash
cd "Minor 1/browser-extension"
npm install
npm run build
```

The compiled Manifest V3 extension will be written to `browser-extension/dist/`.

---

## 3. Loading in Chrome

1. Open Google Chrome and navigate to `chrome://extensions`.
2. Toggle on **Developer mode** in the top-right corner.
3. Click the **Load unpacked** button in the top-left corner.
4. Select the `browser-extension/dist` folder.
5. The **Clyde Career Agent** extension icon will appear in your Chrome toolbar.
6. Click the extension icon to open the Clyde Dark Editorial popup UI.

---

## 4. Running Automated Tests

Run unit and integration tests with Vitest:

```bash
# Run all unit and integration tests
npm run test

# Run tests in watch mode during development
npm run test:watch
```

Test coverage includes:
- `tests/unit/platform-detection.test.ts`: Detection rules and ATS fingerprints.
- `tests/unit/form-mapper.test.ts`: 8-level heuristic field matching.
- `tests/unit/autofill-engine.test.ts`: Controlled input population and event dispatching.
- `tests/unit/submission-security.test.ts`: User approval token enforcement and CAPTCHA pausing.
- `tests/unit/websocket-protocol.test.ts`: Event serialization and jitter backoff calculation.

---

## 5. Testing with Mock Application Pages

The test suite includes 4 realistic job application pages in `tests/mock-pages/`:

1. `standard-job-form.html`: Standard HTML form with full candidate fields and resume upload.
2. `react-controlled-form.html`: React synthetic controlled input test page.
3. `multi-step-form.html`: Multi-stage application wizard.
4. `protected-captcha-form.html`: Human verification challenge page (Cloudflare Turnstile).

To test with a mock page:
1. Start a simple static file server:
   ```bash
   npx serve tests/mock-pages -p 3000
   ```
2. Open `http://localhost:3000/standard-job-form.html` in Chrome.
3. Open the Clyde extension popup. Notice that it detects the page, displays candidate profile data, and allows running the autofill flow.

---

## 6. Connecting to Clyde Backend

Ensure the Clyde FastAPI backend is running:
```bash
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Verify backend health:
```bash
curl http://127.0.0.1:8000/api/extension/token
curl http://127.0.0.1:8000/api/extension/candidate-profile
```

