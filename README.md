# Jaybel Sales Analytics — NL-to-SQL Agent

Natural-language agent for Jaybel sales data on BigQuery, deployed on **Vertex AI Agent Engine** (`jaybel-dev`, `us-central1`).

## Documentation

| Doc | Purpose |
|-----|---------|
| [nl_to_sql_agent_full_plan.md](nl_to_sql_agent_full_plan.md) | End-to-end implementation plan |
| [docs/PRE_IMPLEMENTATION_CHECKLIST.md](docs/PRE_IMPLEMENTATION_CHECKLIST.md) | What is done vs what to verify in GCP |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Locked timezone, auth, UI hosting |
| [docs/FINAL_READINESS_REVIEW.md](docs/FINAL_READINESS_REVIEW.md) | Pre-build sign-off (plan correctness + buildability) |
| [docs/AGENT_ENGINE_ARCHITECTURE.md](docs/AGENT_ENGINE_ARCHITECTURE.md) | Agent Engine–only request flow |
| [docs/business_glossary.md](docs/business_glossary.md) | Business terms → tables/columns (incl. Office Supplies BI) |
| `Office_Supplies_BI_Analytics_Questions.pdf` | Client-provided example questions |
| [docs/qa_evaluation_set.yaml](docs/qa_evaluation_set.yaml) | 97 routing/regression questions (60 generic + 37 client) |
| [docs/office_supplies_client_questions.md](docs/office_supplies_client_questions.md) | Client BI question catalog (PDF) |
| [schema_registry/README.md](schema_registry/README.md) | Table registry layout |

## Configuration

- **GCP:** [config/jaybel.yaml](config/jaybel.yaml)
- **Schemas:** [schema_registry/tables/](schema_registry/tables/) (13 YAML files)
- **Joins:** [schema_registry/join_allowlist.yaml](schema_registry/join_allowlist.yaml)

## Validate / sync schemas with live BigQuery

```bash
.venv/bin/python scripts/validate_bq_schema.py      # writes docs/bq_schema_validation_report.md
.venv/bin/python scripts/sync_registry_columns_from_bq.py  # refresh column lists from BQ
```

## Regenerate table YAMLs (from PDF bootstrap script)

```bash
.venv/bin/python scripts/generate_schema_registry.py
```

## Locked for v1

- **Timezone:** `Australia/Sydney` (calendar “last month”; fiscal only when user says fiscal)
- **Auth:** Firebase Google Sign-In on `jaybel-dev`
- **UI:** `http://localhost:3000` (local dev)

## Next step

**Ready** — start implementation plan **Step 1** (registry loader), then agent tools + Agent Engine deploy, then local Next.js UI.
