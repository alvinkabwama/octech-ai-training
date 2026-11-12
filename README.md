# Octech AI training

> **Trainees:** read [TRAINEES.md](TRAINEES.md) first. It explains your branch and how to hand in work.

Practice repo for the Octech AI training programme. It contains the **mini-EDRMS**,
a small practice records system with no AI in it. Over the programme you add AI to it:
summarise and classify (week 4), tool calling (week 5) and an intake agent (week 6).

All sample data is synthetic: invented names, invented organisations and fake
NIN-style IDs (`CM-FAKE-4827-KR` style). Never add real client data to this repo.

## Setup

Requires **Python 3.10+** and git.

### macOS / Linux / Git Bash on Windows (with `make`)

```bash
make setup               # creates .venv and installs the project + dev tools
cp .env.example .env     # add your OpenRouter key (used from week 1)
```

### Windows PowerShell (no `make`)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e ".[dev]"
git config core.hooksPath scripts/hooks
Copy-Item .env.example .env
```

Each `make` target below is a single command; on PowerShell run it with
`.venv\Scripts\python -m ...` (for example `.venv\Scripts\python -m pytest`).

### Tesseract OCR (optional)

OCR uses [Tesseract](https://github.com/tesseract-ocr/tesseract) when it is on your
`PATH`. **You do not need it**: every sample image ships with a sidecar `.txt` file
holding the same text, and the app falls back to that automatically.

- Windows: installer from <https://github.com/UB-Mannheim/tesseract/wiki>, then add its
  folder to `PATH`
- macOS: `brew install tesseract`
- Debian/Ubuntu: `sudo apt install tesseract-ocr`

Without Tesseract, an uploaded image whose filename matches a bundled sample (e.g. `finance_01.png`) gets that sample's sidecar text; any other image returns 503.

## Commands

| Command | What it does | PowerShell equivalent |
|---|---|---|
| `make run` | Start the mini-EDRMS API on <http://127.0.0.1:8000> | `.venv\Scripts\python -m uvicorn mini_edrms.app.main:app --reload` |
| `make test` | Main tests: mini-EDRMS + shared helper (never calls a model) | `.venv\Scripts\python -m pytest` |
| `make check WEEK=<N>` | One week's exercise tests. They fail until the exercise is done; no model calls | `.venv\Scripts\python scripts\run_week.py check <N>` |
| `make live WEEK=<N>` | Run that week's `starter/live.py` against real OpenRouter (needs `OPENROUTER_API_KEY` in `.env`) | `.venv\Scripts\python scripts\run_week.py live <N>` |
| `make fix` | Format and auto-fix lint issues (ruff) | `.venv\Scripts\python -m ruff format . ; .venv\Scripts\python -m ruff check --fix .` |
| `make ci` | Lint, format check and main tests | `.venv\Scripts\python -m ruff check . ; .venv\Scripts\python -m ruff format --check . ; .venv\Scripts\python -m pytest` |
| `make samples` | Regenerate the synthetic sample documents | `.venv\Scripts\python mini_edrms\samples\build_samples.py` |

Weekly exercises live in `exercises/week-<N>-<topic>/` (each has a `LESSON.md`). Their
tests are left out of `make test` / `make ci` on purpose, because they fail until a
trainee finishes the starter code.

Interactive API docs: <http://127.0.0.1:8000/docs> once the server is running.
Data (SQLite database and uploaded files) goes in `./data/`, or in
`MINI_EDRMS_DATA_DIR` if you set it. Delete the folder to start fresh.

## Demo (2 minutes)

```bash
make run                       # terminal 1
python scripts/demo.py         # terminal 2 (PowerShell: .venv\Scripts\python scripts\demo.py)
```

The demo uploads three sample letters, extracts their text, files each one under a
category, routes it to a department and prints the audit log:

```
[1] uploaded finance_01.png
[1] ocr: 'INVOICE No: INV-EX-0451'...
[1] filed under finance
[1] routed to finance
...
Audit log (newest first):
  2026-11-11T09:00:03  doc=3  route  user  department=legal; reason=...
```

To try requests one at a time, open `mini_edrms/demo.http` in VS Code (REST Client
extension) or a JetBrains IDE.

## The mini-EDRMS

| Endpoint                            | Does                                              |
|-------------------------------------|---------------------------------------------------|
| `POST /documents`                   | Upload a `.png`, `.jpg`, `.jpeg` or `.txt` (max 10 MB) |
| `GET /documents?q=`                 | List documents, or search filename and text       |
| `GET /documents/{id}`               | One document                                      |
| `POST /documents/{id}/ocr`          | Extract text (Tesseract or sidecar `.txt`)        |
| `PUT /documents/{id}/category`      | File it: `{"category", "reason"}`                 |
| `POST /documents/{id}/route`        | Route it: `{"department", "reason"}`              |
| `GET /audit?doc_id=`                | Audit log, newest first                           |

- **Categories (file plan):** `correspondence`, `hr`, `finance`, `procurement`, `legal`
- **Departments:** `registry`, `human_resources`, `finance`, `procurement`, `legal`, `director`
- **Statuses:** `uploaded` → `ocr_done` → `filed` → `routed`
- **Errors:** unknown id → 404; invalid category, department or actor → 422 with the
  `allowed` values; empty upload → 400; over 10 MB → 413; wrong file type → 415;
  no Tesseract and no sidecar → 503 with install instructions.
- Every write is recorded in the audit log with an **actor** (`user` or `agent`) and a
  **reason**.

Samples live in `mini_edrms/samples/`: 20 documents (4 per category) plus
`poisoned_letter_01`, which hides a prompt-injection instruction for week 7.
`labels.csv` holds the expected `category` and `department` for each one.

## What you'll make agentic

Every operation is a plain Python function with type hints and a docstring. The
FastAPI routes in `mini_edrms/app/main.py` are thin wrappers around them. In week 5
these same functions become the tools a model can call, without changing the app:

| Function                                   | Becomes the tool that...                  |
|--------------------------------------------|-------------------------------------------|
| `documents.list_documents(conn)`           | lists documents                           |
| `documents.get_document(conn, doc_id)`     | reads one document                        |
| `documents.search_documents(conn, query)`  | searches filenames and text               |
| `ocr.extract_text(conn, doc_id, actor=...)`| extracts a document's text                |
| `filing.set_category(conn, doc_id, category, actor=..., reason=...)` | files a document |
| `routing.route_document(conn, doc_id, department, actor=..., reason=...)` | routes a document |
| `audit.list_audit(conn, doc_id)`           | reads the audit trail                     |

When the week 6 intake agent calls them it passes `actor="agent"` and its reasoning
as `reason`, so the audit log always shows what the agent did and why.

## Repository layout

```
mini_edrms/app/       service functions + FastAPI app
mini_edrms/samples/   synthetic documents, labels.csv, build_samples.py
mini_edrms/tests/     tests
scripts/demo.py       end-to-end demo against a running server
docs/                 programme design and plans
```
