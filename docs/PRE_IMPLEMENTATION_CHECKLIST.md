# Pre-implementation checklist — Jaybel Sales Analytics Agent

Status: **Phase A complete** — pipeline library in `pipeline/`; **Phase B next** (Agent Engine). See `docs/DECISIONS.md` and `docs/FINAL_READINESS_REVIEW.md`.

## Completed (in repo)

- [x] GCP project config: `config/jaybel.yaml`
- [x] 13 table schema registry YAMLs (validated vs live BQ): `schema_registry/tables/`
- [x] Join allowlist: `schema_registry/join_allowlist.yaml`
- [x] Business glossary: `docs/business_glossary.md`
- [x] QA evaluation set (97 cases: Q001–Q060 generic + Q061–Q097 client): `docs/qa_evaluation_set.yaml`
- [x] Client question catalog (Office Supplies BI PDF): `docs/office_supplies_client_questions.md`
- [x] Source client PDF: `Office_Supplies_BI_Analytics_Questions.pdf`
- [x] Agent Engine architecture: `docs/AGENT_ENGINE_ARCHITECTURE.md`
- [x] Agent Engine config template: `agent/.agent_engine_config.json`
- [x] Source schema PDF: `Jaybel_Sales_Analytics_Detailed_Schema.pdf`
- [x] BQ schema validation report: `docs/bq_schema_validation_report.md`
- [x] **Timezone:** `Australia/Sydney` (calendar-relative dates)
- [x] **Auth:** Firebase Google Sign-In on `jaybel-dev`
- [x] **UI v1:** localhost (`http://localhost:3000`)
- [x] **Phase A:** `pipeline/` package + unit tests (12 pass) + BQ dry-run integration

## Verify in GCP (during implementation — not blocking prep)

- [ ] **IAM:** Service account `115724636423-compute@developer.gserviceaccount.com` has `bigquery.jobUser` + dataset `bigquery.dataViewer` on `jaybel_sales_analytics`
- [ ] **Vertex AI API** enabled in `jaybel-dev`
- [ ] **Agent Engine** enabled in `us-central1`
- [ ] **Firebase Console:** Google provider on; `localhost` in authorized domains; Web app config in `frontend/.env.local`

## After first Agent Engine deploy (implementation milestone)

| Item | Why |
|------|-----|
| **Agent Engine resource ID** | `NEXT_PUBLIC_AGENT_ENGINE_ID` in `frontend/.env.local` |

## Optional (non-blocking)

| Item | Why |
|------|-----|
| Dedicated runtime SA | Cleaner prod IAM vs default compute SA |
| Real rep/account codes in QA | Replace placeholders in `docs/qa_evaluation_set.yaml` |
| `pipeline_logs` BQ table | Evaluation / metrics framework |

## Locked product decisions

| Decision | Choice |
|----------|--------|
| Multi-table | Approved join graph (facts + dims) |
| Staging for analytics | Avoid unless raw/source |
| Policy | None — 10GB dry-run soft warning |
| Entry | Agent Engine only |
| Timezone | Australia/Sydney |
| Auth | Firebase Google on jaybel-dev |
| UI | Localhost dev |
