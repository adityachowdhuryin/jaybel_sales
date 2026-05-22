# Backend (Phase C + question catalog)

Local **FastAPI**: PostgreSQL sessions + question catalog + SSE proxy to Vertex AI Agent Engine.

## Setup

```bash
# from repo root
./scripts/start-phase-c.sh   # Postgres on host port 15433 + migrations 001–004

cp backend/.env.example backend/.env
gcloud auth application-default login

PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload --port 8000
```

`DATABASE_URL` default (see `.env.example`):

`postgresql://jaybel:jaybel_local_dev@localhost:15433/jaybel_sales_app`

## Endpoints

| Method | Path |
|--------|------|
| GET | `/health` |
| GET/PATCH | `/api/sessions/me` |
| GET | `/api/sessions` — optional `?q=` search |
| POST | `/api/sessions` |
| GET/DELETE | `/api/sessions/{id}` |
| GET | `/api/sessions/{id}/turns` |
| POST | `/api/sessions/{id}/turns/{turn_id}/feedback` |
| POST | `/api/chat/stream` — SSE; body: `session_id`, `question`, optional `starter_id`, `category_id` |
| GET | `/api/question-catalog/categories` |
| GET | `/api/question-catalog/categories/{category_id}/starters` |
| GET | `/api/question-catalog/search` — `q`, `category_id`, `intent`, `table_id` |
| GET/POST | `/api/question-catalog/follow-ups` |

Catalog file: `content/question_catalog.yaml` (override with env `QUESTION_CATALOG_PATH` or `config/jaybel.yaml`).

## Chat history

Loads last 5 turns from Postgres, sends `[SALES_CONTEXT]{history, history_json, ...}[/SALES_CONTEXT]` to Agent Engine. Final SSE `done` includes `turn_id`.

## Tests

```bash
export DATABASE_URL=postgresql://jaybel:jaybel_local_dev@localhost:15433/jaybel_sales_app
PYTHONPATH=. .venv/bin/pytest tests/test_phase_c_api.py tests/test_question_catalog.py tests/test_chat_history.py -q
```

See `docs/PHASE_C_LOCAL.md`.
