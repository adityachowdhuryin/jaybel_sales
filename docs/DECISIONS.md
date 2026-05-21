# Product decisions (locked)

Recorded from product owner — do not re-open without explicit change request.

| # | Topic | Decision |
|---|--------|----------|
| D1 | **Relative dates timezone** | `Australia/Sydney` (IANA). “Today” and phrases like **last month**, **yesterday**, **this week** use the **calendar** in this timezone unless the user says **fiscal** (e.g. “last fiscal month” → `dim_date.fiscal_month_no` / `fy`). |
| D2 | **Authentication** | **Firebase Authentication** on GCP project **`jaybel-dev`**, **Google Sign-In** only for v1. Frontend sends Firebase ID token; backend/agent validates before running queries. |
| D3 | **UI hosting (v1)** | **Local development only** on this machine: Next.js at `http://localhost:3000` (`npm run dev`). Production hosting (Vercel / Firebase Hosting) deferred. |
| D4 | **Query entry** | **Vertex AI Agent Engine only** — every chat message is an Agent Engine invocation (dashboard telemetry). |
| D5 | **BigQuery** | Project `jaybel-dev`, dataset `jaybel_sales_analytics`, 13 tables; new-business fact = `fact_new_business_frazer`. |
| D6 | **Policy** | None for v1; 10GB soft dry-run warning (`config/jaybel.yaml`). |
| D7 | **Client example questions** | `Office_Supplies_BI_Analytics_Questions.pdf` → Q061–Q097 in QA set; catalog in `docs/office_supplies_client_questions.md`. Targets/projections from Power BI may need extra BQ tables (see glossary). |

## Firebase setup (implementation step)

When wiring the UI, configure in [Firebase Console](https://console.firebase.google.com/) for project linked to `jaybel-dev`:

1. Enable **Authentication** → **Google** provider.
2. Add authorized domain: **`localhost`** (for local dev).
3. Create a **Web app**; copy config into `frontend/.env.local` (created in implementation):
   - `NEXT_PUBLIC_FIREBASE_API_KEY`
   - `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
   - `NEXT_PUBLIC_FIREBASE_PROJECT_ID=jaybel-dev`
   - (other standard Firebase web fields)

## Local UI (implementation step)

```bash
cd frontend && npm run dev
# http://localhost:3000
```

Agent Engine client env (after first deploy): `NEXT_PUBLIC_AGENT_ENGINE_ID`, `NEXT_PUBLIC_GCP_PROJECT_ID=jaybel-dev`, `NEXT_PUBLIC_GCP_LOCATION=us-central1`.
