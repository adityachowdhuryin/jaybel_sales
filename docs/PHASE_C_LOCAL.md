# Phase C — Local UI + PostgreSQL (implementation guide)

Read **`docs/ARCHITECTURE_LOCAL.md`** first — this is the corrected stack (no Firebase).

**Status:** Phase C and **question discovery UI (UI-1–3)** are implemented in the repo.

## Pre-flight

| Check | Status |
|-------|--------|
| Phases A & B | Done — `docs/PHASE_A_B_SCOPE.md` |
| Agent Engine | `8991351443894042624` — history + `history_json` redeployed |
| Postgres migrations | `001`–`004` via `./scripts/start-phase-c.sh` |
| Question catalog | `content/question_catalog.yaml` (97 starters) |

## Goals

1. Next.js chat UI at `http://localhost:3000/chat`
2. FastAPI at `http://localhost:8000` — sessions, catalog, chat SSE proxy
3. PostgreSQL on your Mac for **app** persistence only
4. Every analytics query via **Vertex AI Agent Engine** → BigQuery

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET/PATCH | `/api/sessions/me` | Dev user + `sales_rep_code` |
| GET | `/api/sessions?q=` | List/search sessions |
| POST | `/api/sessions` | New session |
| GET/DELETE | `/api/sessions/{id}` | Session CRUD |
| GET | `/api/sessions/{id}/turns` | Turn history |
| POST | `/api/sessions/{id}/turns/{turn_id}/feedback` | Thumbs + comment |
| POST | `/api/chat/stream` | SSE proxy (body: `session_id`, `question`, optional `starter_id`, `category_id`) |
| GET | `/api/question-catalog/categories` | Category grid |
| GET | `/api/question-catalog/categories/{id}/starters` | Starters per category |
| GET | `/api/question-catalog/search` | Search (`q`, `category_id`, `intent`, `table_id`) |
| GET/POST | `/api/question-catalog/follow-ups` | Curated + rule-based chips |

SSE `done` event includes `turn_id` (Postgres) for follow-ups and feedback.

## Postgres schema (migrations)

| Migration | Adds |
|-----------|------|
| `001_initial.sql` | `users`, `chat_sessions`, `chat_turns` |
| `002_agent_engine_session.sql` | `agent_engine_session_id` on sessions |
| `003_session_ui_context.sql` | `ui_context` JSONB; `starter_id`, `category_id` on turns |
| `004_turn_feedback.sql` | `feedback_rating`, `feedback_comment` on turns |

## UI features (question discovery)

See **`docs/UI_QUESTION_DISCOVERY_PLAN.md`**.

- **Browse questions** — slide-over drawer, 11 categories, starter list
- Starters **fill input** (edit before Send); `data_availability` badges
- **Follow-up chips** after each answer (curated + rules; show more)
- **Session search** in sidebar
- **Thumbs + comment** on turns
- Sticky **chart + table** split when both exist
- **My Performance** category requires rep code in sidebar

## Conversation history

Before each message, FastAPI loads the last 5 turns and sends:

```text
[SALES_CONTEXT]{"history":[...],"history_json":"...","sales_rep_code":"..."}[/SALES_CONTEXT]

{user question}
```

Deployed `agent.py` parses this and calls `Pipeline.run(history=...)`.

## Quick start

```bash
./scripts/start-phase-c.sh

gcloud auth application-default login

# API
cp backend/.env.example backend/.env
PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload --port 8000

# UI
cp frontend/.env.local.example frontend/.env.local
cd frontend && npm run dev
```

Open **http://localhost:3000/chat**

If port 8000 is busy: use `--port 8001` and `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001` in `frontend/.env.local`.

## Tests

```bash
export DATABASE_URL=postgresql://jaybel:jaybel_local_dev@localhost:15433/jaybel_sales_app
PYTHONPATH=. .venv/bin/pytest tests/test_phase_c_api.py tests/test_question_catalog.py tests/test_chat_history.py tests/test_catalog_integrity.py tests/test_q031_q032_history.py -q
```

## Not in Phase C

- Firebase Auth / Firestore
- Cloud hosting
- Copying BigQuery into Postgres
- LLM-generated follow-ups (UI-4 / deferred)

## Prerequisites

- Docker (Postgres) or native PostgreSQL 14+
- Node.js 18+
- Python 3.11+ + `requirements.txt` + `psycopg[binary]`
- `gcloud auth application-default login`
