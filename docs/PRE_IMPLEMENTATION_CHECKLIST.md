# Pre-implementation checklist — Jaybel Sales Analytics Agent

**Status:** Phases **A**, **B**, **C**, **question discovery (UI-1–3)**, **v1.2**, **v1.3 chart/answer UX**, and **Phase D** QA runner are implemented in the repo.

See `docs/ARCHITECTURE_LOCAL.md`.

## Completed (in repo)

- [x] GCP config: `config/jaybel.yaml`
- [x] 13 table schema registry YAMLs (validated vs live BQ)
- [x] Join allowlist, glossary, QA set (97 cases, all with `category`)
- [x] **Phase A:** `pipeline/` + tests
- [x] **Phase B:** ADK agent on Agent Engine `8991351443894042624`
- [x] **Phase C:** `backend/`, `frontend/`, Postgres migrations `001`–`004`
- [x] **Question discovery:** `content/question_catalog.yaml`, catalog API, explore UI, history envelope
- [x] **v1.2:** config targets, run-rate, account/embroidery patterns, `analytics_context`
- [x] **v1.3:** `chart_selector`, markdown L5 answers, `AnswerMarkdown` / `MetricCards` / chart types
- [x] **Phase D:** `run_qa_suite.py`, smoke scripts, archetype tests
- [x] Local architecture docs
- [x] Timezone `Australia/Sydney`; app storage = Postgres; UI = localhost

## Verify in GCP (analytics)

- [ ] IAM: compute SA has `bigquery.jobUser` + `dataViewer` on `jaybel_sales_analytics`
- [ ] Vertex AI + Agent Engine enabled in `us-central1`

## Local machine (your Mac) — for testing

- [ ] `docker compose up -d postgres` (or `./scripts/start-phase-c.sh`)
- [ ] `gcloud auth application-default login`
- [ ] `backend/.env` — `DATABASE_URL` (port **15433**), `AGENT_ENGINE_RESOURCE`
- [ ] Start API + UI — see `docs/PHASE_C_LOCAL.md`

**Not required for v1:** Firebase, Firestore.

## Agent Engine

| Item | Value |
|------|--------|
| Engine ID | `8991351443894042624` |
| Redeploy script | `./scripts/deploy-sales-agent-engine.sh --agent-engine-id 8991351443894042624` |

## Locked product decisions

| Decision | Choice |
|----------|--------|
| Analytics warehouse | BigQuery in GCP |
| App data | Local PostgreSQL |
| Query entry | Agent Engine only |
| Auth (v1) | Local dev user in Postgres |
| UI | localhost Next.js + FastAPI |
| Timezone | Australia/Sydney |
| Policy | None — 10GB dry-run soft warning |
