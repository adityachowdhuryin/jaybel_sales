# Local app architecture (Phase C) — corrected

This document replaces the earlier assumption that **Firebase + Firestore** would store app data.  
Your requirement: **run everything on your Mac for now**, with **local PostgreSQL** for application data.

---

## What did NOT change

| Layer | Still true |
|-------|------------|
| **Sales analytics data** | **Google BigQuery** (`jaybel-dev.jaybel_sales_analytics`) |
| **NL → SQL pipeline** | Phase A `pipeline/` (route, SQL, validate, execute BQ, answer) |
| **Query entry (telemetry)** | **Vertex AI Agent Engine** — each question = `stream_query` |
| **Timezone** | `Australia/Sydney` |
| **Agent Engine ID** | `8991351443894042624` |

Analytics are **not** in Postgres. Postgres holds **app state** and **UI metadata** only.

---

## What changed

| Before | Now |
|--------|-----|
| Firebase Google Sign-In | **Local dev user** in Postgres |
| Firestore for sessions | **PostgreSQL** — sessions, turns, `ui_context`, feedback |
| UI only free-text | **Question catalog** — categories, starters, follow-ups (`content/question_catalog.yaml`) |

---

## Runtime diagram

```mermaid
flowchart LR
  subgraph local [Your Mac]
    UI[Next.js :3000]
    API[FastAPI :8000]
    PG[(PostgreSQL :15433)]
    YML[question_catalog.yaml]
  end
  subgraph gcp [GCP]
    AE[Agent Engine]
    BQ[(BigQuery)]
  end
  UI -->|REST + SSE| API
  UI -->|read-only catalog| API
  API --> PG
  API --> YML
  API -->|stream_query + SALES_CONTEXT history| AE
  AE -->|query_sales_analytics| BQ
```

### Per message flow

1. User submits question (or picks starter → fills input → Send).
2. UI opens SSE to `POST /api/chat/stream` with optional `starter_id` / `category_id`.
3. FastAPI loads last **5** turns from Postgres → builds `[SALES_CONTEXT]` envelope.
4. FastAPI calls Agent Engine `stream_query`.
5. Agent tool runs pipeline with `history` → BigQuery → streams events.
6. FastAPI forwards SSE to browser; on completion persists turn and emits `done` with `turn_id`.
7. UI loads **follow-up chips** via `POST /api/question-catalog/follow-ups` (uses turn + `ui_context`).

---

## PostgreSQL

| Table | Purpose |
|-------|---------|
| `users` | Dev user; `sales_rep_code` for rep-scoped questions |
| `chat_sessions` | Sidebar; `agent_engine_session_id`; `ui_context` (`last_starter_id`, `last_category_id`) |
| `chat_turns` | Full turn payload + `starter_id` / `category_id` + optional feedback |

Migrations: `sql/migrations/001` through `004`.

---

## Question catalog (read-only, repo file)

- Path: `content/question_catalog.yaml` (config: `config/jaybel.yaml` → `ui.question_catalog_path`)
- Build: `scripts/build_question_catalog.py` (from `docs/qa_evaluation_set.yaml`)
- Served by FastAPI — **not** stored in Postgres (except turn-level `starter_id` / `category_id`)

---

## Local services

```bash
./scripts/start-phase-c.sh
PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload --port 8000
cd frontend && npm run dev
```

Open **http://localhost:3000/chat**

---

## Environment

| File | Purpose |
|------|---------|
| `backend/.env` | `DATABASE_URL`, `AGENT_ENGINE_RESOURCE` |
| `frontend/.env.local` | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` |

UI should call **only** FastAPI (not Agent Engine directly).

---

## Deferred

- Firebase, Firestore, Redis, server PDF/GCS, Memory Bank, cloud hosting
- UI-4: LLM follow-ups, command palette, mobile sheet
