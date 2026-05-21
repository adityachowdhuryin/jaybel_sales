# Final readiness review — before implementation

**Date:** Pre-build sign-off  
**Verdict:** **Plan and docs are correct for Jaybel v1 after corrections in this review.** **Buildable** with scoped v1 (see below).

---

## 1. Is the plan correct?

### Confirmed correct (validated)

| Area | Status | Evidence |
|------|--------|----------|
| GCP project / region / dataset | OK | `config/jaybel.yaml`, live BQ access |
| 13 tables + column names/types | OK | `docs/bq_schema_validation_report.md` (re-run: `scripts/validate_bq_schema.py`) |
| Fact table naming | OK | Live table is `fact_new_business_frazer` (not PDF name `fact_new_business`) |
| Join strategy | OK | `schema_registry/join_allowlist.yaml` |
| Fiscal calendar + Sydney timezone | OK | `docs/DECISIONS.md`, glossary |
| Agent Engine–only entry | OK | `docs/AGENT_ENGINE_ARCHITECTURE.md` |
| Auth + localhost UI | OK | `docs/DECISIONS.md` |
| QA coverage | OK | 97 cases (Q001–Q060 generic + Q061–Q097 client) |
| Client targets/projections gap | OK | Documented; `data_availability` flags in QA |

### Corrections applied to the plan (were inconsistent)

| Issue | Resolution |
|-------|------------|
| Plan described **FastAPI SSE** as the main query path while Jaybel requires **Agent Engine only** | v1: UI calls **Agent Engine streaming**; pipeline runs in **agent tools**. Same **UI event types** (`status`, `sql`, `results`, `token`, …) mapped from tool/agent stream — not `GET /api/query/stream` on the hot path. |
| L1 JSON missing **`join_pattern`** | Added to L1 output spec in plan (required when primary table is a fact). |
| Repo diagram showed `fact_new_business.yaml` | Updated to `fact_new_business_frazer.yaml`. |
| Implementation order listed SSE/Cloud Run/Redis before Agent + UI | Reordered into **phases A–D** with infra deferred. |
| “Zero hallucination” stated as absolute | Clarified as **minimize** via validators + UI truth from data table. |
| Buildability still mentioned “Cloud Run tool pattern” | Updated to **in-agent tools** for Jaybel. |

### Known limitations (not plan errors — product scope)

1. **Power BI targets/projections** ($6M, Furniture $387K, BTS, projected GP): not in current BQ tables — agent answers from facts where possible and states when a metric is unavailable (Q063, Q068, Q089–Q094, etc.).
2. **Rep-scoped “my sales”**: needs Firebase user → `dim_sales_rep` mapping (implementation task).
3. **Product category strings** (Office Supplies, Furniture, …): must match `dim_product.main_group_name` in data — verify with `SELECT DISTINCT main_group_name` during build.
4. **~37 client questions** will not all get perfect SQL on first deploy without target tables and rep mapping — routing + honest answers still testable.

---

## 2. Is it buildable?

**Yes**, in phased v1:

| Phase | Deliverable | Confidence |
|-------|-------------|------------|
| **A** | Python pipeline: registry loader, L1–L5, validators, BQ execute (unit/integration tests) | High |
| **B** | Agent Engine app + tools wrapping pipeline; deploy to `jaybel-dev` | High |
| **C** | Next.js localhost UI, Firebase Google sign-in, Agent Engine stream → UI events | High |
| **D** | QA runner on Q001–Q097 (routing + dry-run pass rate) | Medium–high |

**Deferred from v1** (plan still documents them for v1.1+):

- Cloud Memorystore (Redis) cache  
- FastAPI `/api/query/stream` (optional dev harness only)  
- PDF reports + GCS  
- Vertex Memory Bank  
- `pipeline_logs` BQ table  
- Cloud Run for optional session/PDF API  

**Risks to manage during build (not blockers):**

- Agent Engine SDK/streaming API shape may differ slightly from generic “SSE” wording — adapt mapper in frontend.  
- Embedding pre-compute at agent cold start — use lazy load or bundle precomputed vectors if startup SLO slips.  
- `gemini-2.5-flash` model ID — pin actual GA model name available in `jaybel-dev`.  

---

## 3. Sign-off checklist

- [x] Schema registry matches live BigQuery  
- [x] Jaybel product decisions locked (`docs/DECISIONS.md`)  
- [x] Architecture aligned (Agent Engine + tools + local UI)  
- [x] Client questions integrated without removing Q001–Q060  
- [ ] Firebase Console setup (during Phase C)  
- [ ] Agent Engine ID (after Phase B deploy)  
- [ ] IAM on runtime SA (during Phase B deploy)  

**Recommendation:** Proceed with **implementation Phase A, Step 1** in `nl_to_sql_agent_full_plan.md`.
