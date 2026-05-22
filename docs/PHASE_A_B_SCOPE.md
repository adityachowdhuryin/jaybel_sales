# Phases A & B — scope vs local PostgreSQL (Phase C)

## Short answer

**Phases A and B do not use Firebase, Firestore, or local PostgreSQL.** They were always about **BigQuery analytics** in GCP and **Vertex AI Agent Engine** deployment.

The Postgres pivot affects **Phase C only** (sessions, users, chat history on your Mac). No warehouse migration.

| Phase | Responsibility | Storage / runtime |
|-------|----------------|-------------------|
| **A** | NL→SQL pipeline (L1–L5), validators, BQ execute | BigQuery + Vertex LLM (cloud) |
| **B** | ADK agent + `query_sales_analytics` tool on Agent Engine | Same as A, deployed to GCP |
| **C** | Next.js UI + FastAPI + Postgres | Local Postgres + API proxies Agent Engine |

## What was already correct (no rework required)

- `pipeline/` — no Firebase/Firestore imports; reads `config/jaybel.yaml` for BQ/Vertex only
- `agent/sales_analytics_agent/agent.py` — tool wraps pipeline; no session persistence in agent
- Schema registry, join allowlist, tests, deploy script bundle (`pipeline/`, `config/`, `schema_registry/`)
- Deployed engine `8991351443894042624` — still valid for Phase C

## Alignment changes made (before Phase C)

These prepare Phase C without changing the analytics architecture:

1. **`config/jaybel.yaml`** — `auth.provider: local_postgres`, `local_app` block (already updated)
2. **`pipeline/config.py`** — helpers: `default_user_id()`, `local_database_url()`, `api_base_url()`
3. **`pipeline/user_context.py`** — optional `sales_rep_code` / `user_id` in L1/L2 prompts (“my sales”)
4. **`agent.py`** — tool accepts optional `sales_rep_code`, `user_id`; FastAPI can pass them later
5. **Scripts/docs** — deploy/smoke-test docs point to `backend/.env`, not Firebase frontend env

## Agent Engine redeploy

Latest redeploy (conversation history via `[SALES_CONTEXT]`):

```bash
./scripts/deploy-sales-agent-engine.sh --agent-engine-id 8991351443894042624
```

Engine: `8991351443894042624` — display name **Sales and analytics agent**.

## Phase C + question discovery (implemented — not A/B)

- `backend/routers/question_catalog.py`, `content/question_catalog.yaml`
- Conversation history in Agent message (`[SALES_CONTEXT]`)
- UI: explore drawer, follow-ups, feedback — see `docs/UI_QUESTION_DISCOVERY_PLAN.md`

## Phase C owns these (not A/B)

- `docker compose` + `sql/migrations/001_initial.sql`
- `backend/` FastAPI + Postgres CRUD + SSE proxy
- `frontend/` Next.js calling `http://localhost:8000` only

See `docs/ARCHITECTURE_LOCAL.md` and `docs/PHASE_C_LOCAL.md`.
