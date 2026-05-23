# Phase D — QA runner

## Quick start

```bash
cd "/Users/adityachowdhury/Desktop/sales and analytics project"
PYTHONPATH=. .venv/bin/python scripts/run_qa_suite.py --cases Q061-Q097 --mode keyword
```

## Modes

| Mode | Cost | Use |
|------|------|-----|
| `keyword` | Free | CI — keyword index routing vs `expected_primary_table` |
| `routing` | Vertex L1 | Nightly — full intent router |
| `sql_validate` | Vertex L1+L2+dry-run | Manual — SQL generation + validators |

## Office Supplies v1.2

Cases Q061–Q097 use updated `data_availability`:

- `full_with_config_target` — targets from `config/sales_targets.yaml`
- `partial_run_rate` — run-rate projection disclaimer
- `partial_pattern` — closed account / embroidery patterns
- `not_in_bq_forecast` — Q093 BI variance explanation only

## Smoke test (pipeline, local)

```bash
export SMOKE_REP_CODE=37   # or your rep code from dim_sales_rep
./scripts/smoke_v12_office_supplies.sh
```

## After pipeline changes

Redeploy Agent Engine so `config/` and `pipeline/analytics_context.py` reach production:

```bash
./scripts/deploy-sales-agent-engine.sh --agent-engine-id 8991351443894042624
```

Last redeploy: 2026-05-22 — engine `8991351443894042624` (v1.2 + v1.3 pipeline).

## v1.3 chart tests

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_chart_selector.py tests/test_answer_markdown.py -q
```

## UI smoke

```bash
./scripts/test_improvements_ui.sh
```

## Category validation (live BQ)

```bash
gcloud auth application-default login
PYTHONPATH=. .venv/bin/python scripts/validate_dim_product_categories.py
```
