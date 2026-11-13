# Octech AI Training Programme - Design

Date: 2026-11-11
Owner: Alvin Kabwama
Status: Approved in conversation; awaiting review of this written spec

## 1. Purpose

Teach the Octech AI team (mostly Python developers, no paid AI accounts) how the
HFB chatbot was built and how to add AI - including agents - to Octech products.
Success = by week 8 every participant has built a working chatbot, a RAG bot and
an agentic intake feature on a practice EDRMS, and can explain when to use a fixed
AI workflow versus an agent.

## 2. Constraints

- Free models only, via OpenRouter (`:free` models, 20 req/min, 50 req/day per
  account; 1,000/day after a one-time USD 10 credit purchase). Recommend Octech buys
  the USD 10 credit before week 5.
- No real client data anywhere. Synthetic samples only.
- The production chatbot (`agentic-client-service-bot`) cannot run on free models
  (needs OpenAI/Azure OpenAI + text-embedding-3-large). It is read, not run, by the team.
- Repo follows the Octech engineering standard (clean root, Makefile, ruff, pytest,
  README, ADRs). Local git only; not pushed anywhere until Alvin decides.
- No attribution lines in commits.

## 3. Programme structure

| Week | Topic | Participant builds | Chatbot reading (docs/learning) |
|---|---|---|---|
| Fri | 1-hour overview | OpenRouter account + first call (homework) | Walkthrough manual parts 1-2 |
| 1 | Calling a model: roles, system prompts, parameters | Script with 3 prompt patterns | 01_agents_and_pipelines |
| 2 | Chatbot: memory, streaming, API | Chatbot behind a FastAPI endpoint | 11_sessions_state, 14_streaming |
| 3 | RAG over a small Octech FAQ | Q&A bot with citations and "I don't know" | 02-06, 10_composition_groundedness |
| 4 | AI inside an app (mini-EDRMS) | One-call summarise + classify + extract endpoint | 08_intent_classification |
| 5 | Tool calling | mini-EDRMS functions exposed as tools | pipeline executors |
| 6 | Agents | Intake agent with human review + audit | workflow vs agent |
| 7 | Evaluation and safety | Accuracy on labelled set; poisoned-letter defence | ADR 0042, 0019, 0029; 16_testing |
| 8 | Demo day | Demo, one ADR each, skills re-score | - |

Week 3 embeddings use a free local model (sentence-transformers) + ChromaDB so
retrieval does not consume OpenRouter requests.
Weeks 5-6 use plain OpenAI-SDK tool calling so the agent loop is visible; Microsoft
Agent Framework (MAF) is an optional stretch in week 6 to connect to the chatbot.

Core lesson: the chatbot is a fixed five-step workflow of agents; the week 6 intake
agent chooses its own tools. Participants must be able to say which pattern fits a
given product feature and why.

## 4. Friday session (60 min)

1. 0-10 What a model call, a chatbot and an agent are.
2. 10-30 How the chatbot was built: architecture, five agents, RAG, ADRs as the
   decision record.
3. 30-45 AI across Octech products: EDRMS, QMS, CRM, QA tool examples.
4. 45-55 The 8-week journey + 2-minute mini-EDRMS demo.
5. 55-60 Questions; everyone fills in the skills sheet.

## 5. Repository: octech-ai-training

```
octech-ai-training/
  README.md            setup, OpenRouter key, make commands
  Makefile             setup / run / test / fix / ci
  pyproject.toml
  .env.example         OPENROUTER_API_KEY, OPENROUTER_MODEL
  exercises/weekN/     README (task + done-criteria), starter code, tests
  mini_edrms/          practice app, no AI
    app/               main, db, documents, ocr, filing, routing, audit
    samples/           ~20 synthetic docs + labels.csv + poisoned letter
    tests/
  docs/                learning path, ADR template, skills matrix, specs
```

### 5.1 mini-EDRMS

- FastAPI + SQLite (stdlib sqlite3). Files stored on local disk under `data/`.
- Endpoints: `POST /documents` (upload), `GET /documents`, `GET /documents/{id}`,
  `POST /documents/{id}/ocr`, `PUT /documents/{id}/category`,
  `POST /documents/{id}/route`, `GET /audit`.
- File plan: 5 categories (correspondence, hr, finance, procurement, legal) and a
  small department list for routing.
- OCR: Tesseract (pytesseract) when installed; otherwise falls back to a sidecar
  `.txt` beside each sample, so Windows users are never blocked.
- Every operation is a plain Python service function with type hints and a
  docstring; FastAPI routes are thin wrappers. These functions become agent tools
  in week 5 without changing app internals.
- Audit log records every write with actor (`user` or `agent`) and reason.
- Samples: ~20 synthetic documents, fake names and fake NIN-style IDs only,
  labelled in `labels.csv` (expected category + department). One "poisoned" letter
  contains an injection instruction for week 7.

### 5.2 Exercises

- Each week: README (goal, steps, done-criteria, chatbot reading), starter file(s)
  with TODOs, tests.
- Tests check structure/behaviour with the model call stubbed, so `make test` never
  spends OpenRouter requests. A separate `make live WEEK=n` runs against OpenRouter.
- A reference solution per week is kept out of the participants' branch (folder
  `solutions/`, git-ignored on the training branch or kept by Alvin) and is run once
  live to prove each exercise is achievable on free models.
- Shared helper `exercises/common/llm.py`: OpenRouter client, fallback model list,
  retry on 429.

## 6. Other deliverables

1. Friday deck (~12 slides, Octech design system, Slides artifact).
2. Learning-path document (Docs artifact; copy saved to the Octech project).
3. Skills-gap sheet (Sheets artifact): ~12 skills rated 0-3 at start and week 8,
   one row per participant.

## 7. Build order (Friday-critical first)

1. mini-EDRMS app + samples + tests (needed for the Friday demo).
2. Friday deck.
3. Skills-gap sheet.
4. Learning-path document.
5. Week 1-3 exercises, then weeks 4-8 (before each week starts).

## 8. Testing / done

- `make test` green on mini-EDRMS baseline and on every exercise's stubbed tests.
- Each week's reference solution run once live against OpenRouter free models.
- Deck, doc and sheet reviewed by Alvin.

## 9. Out of scope

- Running the production chatbot for participants.
- Any real EDRMS code or client data.
- Hosting/deploying the training repo.

## 10. Amendments (2026-11-11, agreed after the first draft)

### 10.1 Model provider
OpenRouter is the only LLM provider in every lesson and exercise. All model calls go
through one shared helper (`exercises/common/llm.py`: key from `.env`, fallback model
list, retry on 429). Embeddings use a free local model, never OpenRouter.

### 10.2 Lessons live in this repo
Each week has `exercises/week-N-<topic>/LESSON.md` in the chatbot's module format:
What you'll learn, Concepts, Code walkthrough, Assignment (homework), Show your work
(checkpoint), Stretch, and a short "How the real chatbot does this" box. Lessons are
adapted from `agentic-client-service-bot/docs/learning`, rewritten for OpenRouter and
the mini-EDRMS, with all HFB/client content removed. The originals are not modified.
A week 0 lesson covers git and the branch workflow.

| Week | Core lessons (source modules) | Optional deep dive |
|---|---|---|
| 0 | Git and branch workflow (new), setup (00) | - |
| 1 | Calling a model via OpenRouter (new), agents vs pipelines (01) | - |
| 2 | Sessions and memory (11), streaming (14) | Frontend (17) |
| 3 | RAG, chunking, embeddings, hybrid retrieval, reranking (02-06) | - |
| 4 | Intent classification (08), composition and groundedness (10) on mini-EDRMS | Language detection (07), query rewriting (09) |
| 5 | Tool calling (new) | Escalation and OTP (12) |
| 6 | Agents: intake agent with human review (new) | Caching (13), MAF |
| 7 | Testing (16), observability (15), prompt injection (ADR 0042) | - |
| 8 | Demo day | Deployment (18) |

### 10.3 Simplified mini-bot (not a copy of the production chatbot)
Trainees build a plain-Python mini-bot (~100 lines, no Microsoft Agent Framework):
`classify(question)`, `retrieve(question)` (Chroma + local embeddings) and
`answer(question, chunks)` with an "I don't know" path. Language detection,
reranking, query rewriting, caching and OTP are described in the "How the real
chatbot does this" boxes, not built. MAF is an optional week 6 stretch.

### 10.4 Trainee workflow and assessment
- One repo. `main` is trainer-only. Each trainee has a long-lived branch
  `trainee/<name>` (rachel, tracy, owen, simon), created by the trainer from `main`.
- Each week: merge `origin/main` into `trainee/<name>`, branch
  `trainee/<name>-week-<N>` (git cannot hold both `trainee/x` and `trainee/x/...`),
  open a PR with **base `trainee/<name>`**, never `main`. The trainer reviews and
  merges into the trainee's branch. Nothing is ever merged into `main` from a trainee.
- No technical guard on main (free private repo); the rule is enforced by the trainer
  reviewing main's history.
- PR template carries the week's checkpoint list. Assessment per week: tests pass,
  checkpoint done, PR approved; weeks 6-8 add a live demo. Scores go in the
  skills-gap sheet.
- Checks run locally (`make ci`), not in GitHub Actions, to save Actions minutes.
- Reference solutions stay on the trainer's machine only, never in the shared repo.
- Full trainee instructions: `TRAINEES.md`.
