# SQL Generation Hardening

Operational guide for L2 SQL quality, column aliases, and batch regression after Agent Engine deploy.

## What changed

- **Join-aware schemas** — L2 receives fact + all joined dimension columns via `pipeline/schema_context.py`.
- **Config-driven aliases** — `config/column_aliases.yaml` maps NL/hallucinated names to registry columns.
- **Hybrid repair** — deterministic alias repair first, then up to 2 LLM retries (`config/sql_generation.yaml`).
- **Follow-up SQL context** — prior metric, filters, and SQL excerpt passed to L2.
- **Friendly validation UX** — `sql_validation_failed` guidance banner instead of raw sqlglot traces.

## Tuning aliases

Edit `config/column_aliases.yaml`:

```yaml
global:
  customer_name: account_name
by_table:
  jaybel-dev.jaybel_sales_analytics.fact_sales_report:
    territory: territory_code
value_hints:
  territory_code:
    description: "Codes like JAY, FRA — not APAC"
```

Redeploy Agent Engine once, then re-run regression.

## Batch QA after deploy

```bash
python scripts/run_qa_suite.py --mode guard --cases G001-G009
python scripts/run_qa_suite.py --mode sql_regression --cases S001-S012
python scripts/run_qa_suite.py --mode sql_validate --cases S001-S012   # optional live dry-run
```

Manual UI checks: `docs/SECTION_A_MANUAL_TEST_SET.md`.

## Unit tests (no Vertex)

```bash
python -m pytest tests/test_schema_context.py tests/test_column_repair.py \
  tests/test_followup_sql_context.py tests/test_sql_column_typos.py \
  tests/test_answer_markdown.py -q
```

## Repair loop (pipeline)

1. L2 generates SQL with join schemas + glossary + follow-up block.
2. Validators A/B/C run (column, safety, dry_run).
3. On `column_check` fail → `column_repair.repair_sql_from_validation`.
4. Still failing → L2 retry with structured hint (invalid cols + suggestions).
5. Max 2 LLM retries (configurable).

## Files

| File | Role |
|------|------|
| `config/column_aliases.yaml` | NL → column mappings |
| `config/sql_generation.yaml` | Retry limits, schema token budget |
| `pipeline/schema_context.py` | Join-aware L2 schema bundle |
| `pipeline/column_repair.py` | Deterministic repair |
| `pipeline/followup_sql_context.py` | L2 follow-up block |
| `pipeline/sql_regression_runner.py` | S001–S012 batch runner |
