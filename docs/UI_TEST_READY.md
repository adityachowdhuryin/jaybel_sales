# UI test readiness — SQL hardening + Section A

Use this checklist before manual testing in the browser.

## Prerequisites (automated)

Run once (or after pulling new code):

```bash
SKIP_AGENT_DEPLOY=1 API_PORT=8001 ./scripts/prepare-ui-test.sh
```

With Agent Engine redeploy (only when pipeline/config changed):

```bash
API_PORT=8001 ./scripts/prepare-ui-test.sh
```

Optional full SQL regression (Vertex, ~2 min):

```bash
RUN_SQL_REGRESSION=1 API_PORT=8001 ./scripts/prepare-ui-test.sh
```

## Stack (should already be running)

| Service | URL | Status check |
|---------|-----|--------------|
| **Chat UI** | http://localhost:3000/chat | Page loads |
| **FastAPI** | http://localhost:8001/health | `200 OK` |
| **Postgres** | `localhost:15433` | `docker ps \| grep jaybel_sales_postgres` |
| **Agent Engine** | `8991351443894042624` | Deployed with hardened pipeline |

Start servers if needed:

```bash
# Terminal 1 — API
cd "/Users/adityachowdhury/Desktop/sales and analytics project"
PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001

# Terminal 2 — UI
cd frontend && npm run dev
```

Quick health:

```bash
API_BASE=http://127.0.0.1:8001 ./scripts/test_improvements_ui.sh
```

## GCP auth

Required for Agent Engine + BigQuery from your Mac:

```bash
gcloud auth application-default login
```

## Env files (already configured)

- `backend/.env` — `API_PORT=8001`, `AGENT_ENGINE_RESOURCE=.../8991351443894042624`
- `frontend/.env.local` — `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001`

## What to test

### Fiscal calendar (July–June)

| ID | Question | What to verify |
|----|----------|----------------|
| **FC-01** | What's the current FY and start month and end month? | **2025-2026**, start **July**, end **June** |
| **FC-02** | What's the **last** FY and start month and end month? | **2024-2025** (prior business year — not 2028-2029 from dim_date) |
| **FC-03** | What's the **latest** FY and start month and end month? | Same as current: **2025-2026** (not max fy in table like 2029-2030) |
| **FC-04** | What's the start month of FY 2024-2025? | **July** |

Use a **new chat** after deploy; hard refresh (Cmd+Shift+R). In View SQL, expect `WHERE fy = '2024-2025'` or `'2025-2026'` — never `ORDER BY fy DESC` alone.

### SQL hardening (priority)

| ID | Question | What to verify |
|----|----------|----------------|
| **H-01** | Top 5 customers by GP for each territory in fiscal Q1 2025-2026 | SQL uses `account_name`, `fiscal_quarter`, `ROW_NUMBER`/`PARTITION BY`; answer markdown renders cleanly |
| **H-02** | Top 10 customers by GP in fiscal Q1 2025-2026 | No `customer_name` or `fiscal_q` in SQL |
| **H-03** | *(follow-up)* Now FRA territory only | Keeps GP metric; filter uses `territory_code = 'FRA'` |
| **H-04** | *(follow-up)* Break down by fiscal month | Same filters + fiscal month columns |
| **H-05** | GP by territory for APAC in fiscal Q1 | Guidance or clarification — not invalid SQL with fake region |

### Section A guards + UX

Full matrix: **`docs/SECTION_A_MANUAL_TEST_SET.md`**

Key chains:

- **MA-F02** — Top 10 GP → FRA territory → fiscal month breakdown
- **MA-G*** — off-topic, vague, rep gate, empty results

### Regression already passed (batch)

```bash
python scripts/run_qa_suite.py --mode guard --cases G001-G009          # 9/9
python scripts/run_qa_suite.py --mode sql_regression --cases S001-S012  # 12/12
```

## Sidebar settings

- Set **Sales rep code** (e.g. `37` or `REP01`) before rep-scoped questions (“my sales”, “my GP”).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Agent Engine 502 | `gcloud auth application-default login`; confirm deploy id in `backend/.env` |
| UI can't reach API | Match `API_PORT` in `backend/.env` and `NEXT_PUBLIC_API_BASE_URL` |
| Old SQL behavior | Redeploy: `./scripts/deploy-sales-agent-engine.sh --agent-engine-id 8991351443894042624` |
| Jumbled markdown headers | Hard refresh browser; ensure latest Agent Engine deploy |
| Raw sqlglot error in chat | Same — redeploy; should show orange “Couldn't build a valid query” banner |

## Docs

- SQL hardening ops: `docs/SQL_GENERATION_HARDENING.md`
- Query understanding: `docs/QUERY_UNDERSTANDING.md`
- Manual test set: `docs/SECTION_A_MANUAL_TEST_SET.md`
