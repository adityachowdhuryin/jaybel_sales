# Product decisions (locked)

Recorded from product owner. **Updated:** local Postgres for app data (no Firebase).

| # | Topic | Decision |
|---|--------|----------|
| D1 | **Relative dates timezone** | `Australia/Sydney` (IANA). Calendar phrases unless user says **fiscal**. |
| D2 | **Authentication (v1)** | **No Firebase.** Local dev: default user in Postgres (`dev@localhost`) or simple email on `users` table. No Google Sign-In required for v1 local run. |
| D3 | **UI hosting (v1)** | **Local only:** Next.js `http://localhost:3000` on your machine. |
| D4 | **App data storage** | **PostgreSQL on local device** — users, `chat_sessions`, `chat_turns`. **Not** Firestore. **Not** Firebase. |
| D5 | **Analytics data** | **Google BigQuery** in GCP (`jaybel-dev.jaybel_sales_analytics`) — unchanged. |
| D6 | **Query entry** | **Vertex AI Agent Engine only** — each chat message = Agent Engine invocation (telemetry). |
| D7 | **API layer** | **FastAPI required** at `http://localhost:8000` — sessions in Postgres + proxies `stream_query` to UI via SSE. |
| D8 | **Policy** | None for v1; 10GB BQ dry-run soft warning. |
| D9 | **Client questions** | Office Supplies PDF → Q061–Q097 in QA set. |
| D10 | **v1.2 targets & projections** | FY targets in `config/sales_targets.yaml` (not BQ). Run-rate via `stg_total_working_days` subqueries. Q093 remains BI-only. |
| D11 | **v1.2 deploy** | Agent Engine `8991351443894042624` redeployed 2026-05-22 with `config/` + `analytics_context`. |
| D12 | **v1.3 charts & answers** | Rule-based `chart_selector` (line/bar/pie/paired/grouped); L5 markdown sections; UI renders after stream ends. Redeploy Agent Engine after `pipeline/` changes. |

## v1.2 validation

```bash
PYTHONPATH=. .venv/bin/python scripts/validate_dim_product_categories.py
SMOKE_REP_CODE=37 ./scripts/smoke_v12_office_supplies.sh
```

## Local PostgreSQL setup

```bash
docker compose up -d postgres
export DATABASE_URL=postgresql://jaybel:jaybel_local_dev@localhost:15433/jaybel_sales_app
psql "$DATABASE_URL" -f sql/migrations/001_initial.sql
```

Copy `backend/.env.example` → `backend/.env`.

## Local UI

```bash
# API (terminal 1)
cd backend && uvicorn main:app --reload --port 8000

# UI (terminal 2)
cd frontend && npm run dev
```

## Question discovery (implemented)

- Starters from `content/question_catalog.yaml` (97 questions, 11 categories)
- Browse via drawer; follow-ups after each answer; history sent to pipeline via Agent Engine
- Spec: `docs/UI_QUESTION_DISCOVERY_PLAN.md`

Frontend env: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` (see `frontend/.env.local.example`).

## Agent Engine (unchanged)

- ID: `8991351443894042624`
- Resource: `agent/AGENT_ENGINE_RESOURCE.env`
- Analytics queries: Agent tool → BigQuery (cloud)

## Explicitly out of scope for v1 local

- Firebase Authentication
- Cloud Firestore
- Firebase Hosting
- Moving BigQuery warehouse into Postgres
