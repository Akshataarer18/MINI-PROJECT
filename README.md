# SyncGuard E1 Showcase

A polished local demo for **E1 — Concurrency & Synchronization** built with Python, HTML, CSS, and JavaScript. It uses only the Python standard library; no `pip install` is required.

## Features

- Responsive, presentation-ready dashboard.
- Python HTTP API (`app.py`) serves the frontend and JSON endpoints.
- E1 core engine (`e1_engine.py`) protects in-memory state using `threading.Lock`.
- Optimistic version check: outdated updates return `CONFLICT`.
- Permission gate: disabled edit permission returns `REJECTED`.
- Version increments only after an accepted edit.
- Activity log, current version indicator, stale-edit simulation, and API status.
- Automated unit tests.

## Open in VS Code

1. Extract `SyncGuard_E1_Showcase.zip`.
2. In VS Code, choose **File → Open Folder** and select `SyncGuard_E1_Showcase`.
3. Choose **Terminal → New Terminal**.
4. Confirm Python is installed:
   ```powershell
   python --version
   ```
5. Start the app:
   ```powershell
   python app.py
   ```
   If `python` is not recognized, try `py app.py`.
6. Open `http://127.0.0.1:8000` in Chrome or Edge. Keep the terminal open while using the demo.

## Demonstrate it

1. The page loads the current document and version.
2. Edit the text, keep **Can edit** enabled, and click **Submit edit**. The edit is accepted and the version increments.
3. Click **⚡ Simulate stale edit** to demonstrate a stale-version conflict.
4. Turn off **Can edit** and click **Submit edit** to demonstrate a permission rejection.
5. Click **Load latest** to refresh the editor from the server's current document.

The “Simulate stale edit” button can advance the document version once during its first use so it can demonstrate a conflict even in a fresh server session.

## Run tests

From the project root:

```powershell
python -m unittest discover -s tests -v
```

If needed, use `py` instead of `python`.

## API endpoints

- `GET /api/health` — server health.
- `GET /api/document` — current document content and version.
- `GET /api/info` — feature and limitation information.
- `POST /api/edit` — submit an edit.

Example request body:

```json
{
  "username": "Alice",
  "content": "Updated document text",
  "can_edit": true,
  "expected_version": 1
}
```

## Architecture

```text
Browser (HTML/CSS/JavaScript)
           |
           | HTTP + JSON
           v
       app.py (API)
           |
           v
 e1_engine.py (E1 logic)
  - permission gate
  - threading.Lock
  - version comparison
  - accept / conflict / reject
```

## Honest scope and limitations

This is a **local Sprint 1 demonstration**, not a production-ready collaborative editor.

- Data is stored in memory and resets when the server restarts.
- The lock protects threads inside this one Python process only.
- The permission flag is a demo control, not real authentication; E2 is not integrated.
- Updates replace the whole document; there is no operational transform or CRDT merge.
- This demo does not include a database, WebSockets, multiple-user broadcasting, or deployment security.
- Do not describe these unfinished capabilities as implemented. Explain them as future integration work for E2/E3 and the complete project.

## Suggested review explanation

“My E1 prototype receives an edit request through the Python API. The engine checks edit permission, locks the shared document state, compares the request's expected version with the current version, and then either accepts the edit and increments the version or returns a conflict. I demonstrate an accepted edit, an outdated-version conflict, and a permission rejection. The frontend visualizes these outcomes. Persistence, real authentication, and real-time broadcasting remain future integration work.”
