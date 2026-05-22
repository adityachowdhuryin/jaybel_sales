# Phase B — Vertex AI Agent Engine

## What was added

| Path | Purpose |
|------|---------|
| `agent/sales_analytics_agent/agent.py` | ADK `root_agent` + `query_sales_analytics` tool (wraps `pipeline.Pipeline`) |
| `agent/sales_analytics_agent/.agent_engine_config.json` | Display name + service account for deploy |
| `scripts/deploy-sales-agent-engine.sh` | Stage bundle + `adk deploy agent_engine` |
| `scripts/query_agent_engine.py` | Post-deploy smoke test via `stream_query` |

## Prerequisites

1. [Google ADK](https://google.github.io/adk-docs/) installed (`pip install google-adk` or use A2A project venv).
2. `gcloud auth application-default login` with access to **jaybel-dev**.
3. Runtime SA `115724636423-compute@developer.gserviceaccount.com` has:
   - `roles/aiplatform.user`
   - `roles/bigquery.jobUser`
   - `roles/bigquery.dataViewer` on `jaybel_sales_analytics`

## Deploy

```bash
cd "/Users/adityachowdhury/Desktop/sales and analytics project"

# New engine
./scripts/deploy-sales-agent-engine.sh --force-new-engine

# Update existing engine
./scripts/deploy-sales-agent-engine.sh --agent-engine-id YOUR_NUMERIC_ID
```

Copy the **Reasoning Engine ID** from the command output into:

```bash
# agent/AGENT_ENGINE_RESOURCE.env
AGENT_ENGINE_RESOURCE=projects/jaybel-dev/locations/us-central1/reasoningEngines/<ID>

# backend/.env (Phase C local API)
AGENT_ENGINE_RESOURCE=projects/jaybel-dev/locations/us-central1/reasoningEngines/<ID>
DATABASE_URL=postgresql://jaybel:jaybel_local_dev@localhost:15433/jaybel_sales_app
```

## Redeploy when

- Changes to `agent/sales_analytics_agent/agent.py` (e.g. `history_json`, `[SALES_CONTEXT]` parsing)
- Changes to `pipeline/` bundled in the deploy staging folder

```bash
./scripts/deploy-sales-agent-engine.sh --agent-engine-id 8991351443894042624
```

## Smoke test

```bash
export AGENT_ENGINE_RESOURCE=projects/jaybel-dev/locations/us-central1/reasoningEngines/<ID>
PYTHONPATH=. .venv/bin/python scripts/query_agent_engine.py \
  --question "What was total sales in fiscal year 2025-2026?"
```

Every `stream_query` call appears in **Vertex AI → Agent Engine** dashboard telemetry.

## UI (Phase C + question discovery)

Next.js → **FastAPI** (`http://localhost:8000`) → Agent Engine; Postgres for sessions; catalog from `content/question_catalog.yaml`. See `docs/PHASE_C_LOCAL.md`, `docs/UI_QUESTION_DISCOVERY_PLAN.md`.
