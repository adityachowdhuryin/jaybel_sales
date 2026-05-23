# Jaybel Sales Analytics — NL-to-SQL Agent

Natural-language agent for Jaybel sales data on **BigQuery**, deployed on **Vertex AI Agent Engine** (`jaybel-dev`, `us-central1`).  
**v1 local app:** Next.js + FastAPI + **PostgreSQL on your machine** (no Firebase).

## Documentation

| Doc | Purpose |
|-----|---------|
| [nl_to_sql_agent_full_plan.md](nl_to_sql_agent_full_plan.md) | End-to-end implementation plan |
| [docs/ARCHITECTURE_LOCAL.md](docs/ARCHITECTURE_LOCAL.md) | **Local stack** — Postgres app data, Agent Engine + BQ analytics |
| [docs/PHASE_C_LOCAL.md](docs/PHASE_C_LOCAL.md) | Phase C + question discovery — run locally |
| [docs/UI_QUESTION_DISCOVERY_PLAN.md](docs/UI_QUESTION_DISCOVERY_PLAN.md) | Categories, starters, follow-ups (UI-1–3 complete) |
| [docs/PRE_IMPLEMENTATION_CHECKLIST.md](docs/PRE_IMPLEMENTATION_CHECKLIST.md) | What is done vs what to verify in GCP |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Locked timezone, auth, storage, UI |
| [docs/FINAL_READINESS_REVIEW.md](docs/FINAL_READINESS_REVIEW.md) | Pre-build sign-off |
| [docs/AGENT_ENGINE_ARCHITECTURE.md](docs/AGENT_ENGINE_ARCHITECTURE.md) | Agent Engine request flow + history |
| [docs/PHASE_A_B_SCOPE.md](docs/PHASE_A_B_SCOPE.md) | Why A/B unchanged for Postgres; what was aligned |
| [docs/PHASE_B_DEPLOY.md](docs/PHASE_B_DEPLOY.md) | Deploy / redeploy Agent Engine |
| [docs/business_glossary.md](docs/business_glossary.md) | Business terms → tables/columns |
| [docs/PHASE_D_QA.md](docs/PHASE_D_QA.md) | QA runner + v1.2 Office Supplies coverage |
| [docs/CHART_AND_ANSWER_UX_PLAN.md](docs/CHART_AND_ANSWER_UX_PLAN.md) | v1.3 charts + markdown answer UX |
| [docs/ANSWER_FORMAT.md](docs/ANSWER_FORMAT.md) | L5 markdown section spec |
| [docs/qa_evaluation_set.yaml](docs/qa_evaluation_set.yaml) | 97 routing/regression questions (with `category`) |
| [content/question_catalog.yaml](content/question_catalog.yaml) | UI starters, follow-ups, rules |
| [schema_registry/README.md](schema_registry/README.md) | Table registry layout |

## Charts & formatted answers (v1.3)

- Rule-based charts: line, bar, horizontal bar, pie, **paired** (Actual vs Target), **grouped**
- Markdown answers: Summary, Key figures, Notes, Caveats — see `docs/ANSWER_FORMAT.md`
- Redeploy Agent Engine after `pipeline/` changes

## Office Supplies v1.2 (targets & run-rate)

- **Targets:** [config/sales_targets.yaml](config/sales_targets.yaml) — FY goals compared to BigQuery actuals (not a BQ table)
- **Patterns:** [config/account_patterns.yaml](config/account_patterns.yaml), [config/embroidery_patterns.yaml](config/embroidery_patterns.yaml)
- **Pipeline:** [pipeline/analytics_context.py](pipeline/analytics_context.py) — injected into L1/L2/L5
- **Redeploy** Agent Engine after changes: `./scripts/deploy-sales-agent-engine.sh --agent-engine-id 8991351443894042624`
- **Smoke:** `./scripts/smoke_v12_office_supplies.sh` (set `SMOKE_REP_CODE` from `dim_sales_rep`)

## Configuration

- **GCP:** [config/jaybel.yaml](config/jaybel.yaml) — includes `ui.question_catalog_path`
- **Schemas:** [schema_registry/tables/](schema_registry/tables/) (13 YAML files)
- **Postgres:** [sql/migrations/](sql/migrations/) (`001`–`004`)
- **Docker Postgres:** [docker-compose.yml](docker-compose.yml) — host port **15433**

## Locked for v1 (local)

| Topic | Choice |
|-------|--------|
| Timezone | `Australia/Sydney` (calendar “last month”; fiscal when user says fiscal) |
| App data | **PostgreSQL** on localhost (`jaybel_sales_app`) |
| Auth | Default dev user in Postgres — **no Firebase** |
| UI | `http://localhost:3000` (Next.js) |
| API | `http://localhost:8000` (FastAPI; use **8001** if 8000 is busy — set `NEXT_PUBLIC_API_BASE_URL` accordingly) |
| Analytics | BigQuery in GCP (not in Postgres) |
| Queries | Vertex AI Agent Engine only |

## Quick start (full stack)

```bash
./scripts/start-phase-c.sh   # Postgres + migrations 001–004

# Terminal 1 — API
cp backend/.env.example backend/.env
gcloud auth application-default login   # Agent Engine + BQ
PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload --port 8000
# If port 8000 is in use: --port 8001 and NEXT_PUBLIC_API_BASE_URL=http://localhost:8001

# Terminal 2 — UI
cp frontend/.env.local.example frontend/.env.local
cd frontend && npm install && npm run dev
```

Open **http://localhost:3000/chat**

| Service | URL |
|---------|-----|
| Next.js UI | http://localhost:3000/chat |
| FastAPI | http://localhost:8000 |
| Postgres | localhost:**15433** |

## Phase A pipeline (implemented)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/pytest tests/ -m "not integration"

PYTHONPATH=. .venv/bin/python scripts/run_pipeline_cli.py "Top 5 customers by sales FY 2025-2026"
```

Package: `pipeline/` (registry, L1–L5, validators).

## Phase B — Agent Engine (deployed)

| Item | Value |
|------|--------|
| Engine ID | `8991351443894042624` |
| Display name | Sales and analytics agent |

```bash
./scripts/deploy-sales-agent-engine.sh --agent-engine-id 8991351443894042624
```

Redeploy after changes to `agent/sales_analytics_agent/agent.py` (e.g. conversation history).

## Phase C + question discovery (implemented)

- Session sidebar, streaming chat, charts, CSV/report/chart export, rep profile
- **Browse questions** drawer, 11 categories, 97 starters, follow-up chips
- Multi-turn history via `[SALES_CONTEXT]` → pipeline L1
- Turn feedback (thumbs + comment), session search

## Phase D — QA & smoke (implemented)

```bash
# Keyword routing check (free, no Vertex)
PYTHONPATH=. .venv/bin/python scripts/run_qa_suite.py --cases Q061-Q097 --mode keyword

# Pipeline smoke (Vertex + BQ)
SMOKE_REP_CODE=37 ./scripts/smoke_v12_office_supplies.sh

# Stack health before UI testing
./scripts/test_improvements_ui.sh
```

See [docs/PHASE_D_QA.md](docs/PHASE_D_QA.md).

## Tests (full suite)

```bash
export DATABASE_URL=postgresql://jaybel:jaybel_local_dev@localhost:15433/jaybel_sales_app
PYTHONPATH=. .venv/bin/pytest tests/ -m "not integration" -q
```
