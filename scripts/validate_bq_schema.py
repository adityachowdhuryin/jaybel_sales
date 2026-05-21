#!/usr/bin/env python3
"""Compare schema_registry/tables/*.yaml columns to live BigQuery INFORMATION_SCHEMA."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml
from google.cloud import bigquery

PROJECT = "jaybel-dev"
DATASET = "jaybel_sales_analytics"
REGISTRY_DIR = Path(__file__).resolve().parents[1] / "schema_registry" / "tables"
REPORT_PATH = Path(__file__).resolve().parents[1] / "docs" / "bq_schema_validation_report.md"

# BigQuery API returns INTEGER/FLOAT/BOOLEAN; registry uses INT64/FLOAT64/BOOL
TYPE_ALIASES = {
    "INTEGER": "INT64",
    "INT64": "INT64",
    "FLOAT": "FLOAT64",
    "FLOAT64": "FLOAT64",
    "BOOLEAN": "BOOL",
    "BOOL": "BOOL",
    "STRING": "STRING",
    "DATE": "DATE",
    "TIMESTAMP": "TIMESTAMP",
}


def norm_type(t: str) -> str:
    return TYPE_ALIASES.get(t.upper(), t.upper())


EXPECTED_TABLES = [
    "fact_sales_report",
    "fact_new_business_frazer",
    "dim_date",
    "dim_department",
    "dim_sales_customer",
    "dim_sales_rep",
    "dim_product",
    "stg_sales_report",
    "stg_sales_cust",
    "stg_sales_rep",
    "stg_main_product",
    "stg_new_busin_frazer",
    "stg_total_working_days",
]


def load_registry_columns(table_name: str) -> dict[str, str]:
    path = REGISTRY_DIR / f"{table_name}.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text())
    return {c["name"]: c["type"] for c in data.get("columns", [])}


def fetch_bq_columns(client: bigquery.Client, table_name: str) -> dict[str, str]:
    ref = f"{PROJECT}.{DATASET}.{table_name}"
    table = client.get_table(ref)
    return {f.name: f.field_type for f in table.schema}


def main() -> int:
    client = bigquery.Client(project=PROJECT)
    live_tables = {t.table_id for t in client.list_tables(DATASET)}

    lines: list[str] = [
        "# BigQuery schema validation report",
        "",
        f"**Project:** `{PROJECT}`  ",
        f"**Dataset:** `{DATASET}`  ",
        "",
    ]

    missing_tables = sorted(set(EXPECTED_TABLES) - live_tables)
    extra_tables = sorted(live_tables - set(EXPECTED_TABLES))

    if missing_tables:
        lines.append("## Missing tables in BigQuery")
        for t in missing_tables:
            lines.append(f"- `{t}`")
        lines.append("")

    if extra_tables:
        lines.append("## Extra tables in BigQuery (not in registry)")
        for t in extra_tables:
            lines.append(f"- `{t}`")
        lines.append("")

    all_ok = not missing_tables
    lines.append("## Per-table column diff")
    lines.append("")

    for table_name in EXPECTED_TABLES:
        if table_name not in live_tables:
            lines.append(f"### `{table_name}` — **SKIP** (table not in BQ)")
            lines.append("")
            all_ok = False
            continue

        reg = load_registry_columns(table_name)
        bq = fetch_bq_columns(client, table_name)

        reg_names = set(reg)
        bq_names = set(bq)

        only_reg = sorted(reg_names - bq_names)
        only_bq = sorted(bq_names - reg_names)
        type_mismatch = sorted(
            n
            for n in reg_names & bq_names
            if norm_type(reg[n]) != norm_type(bq[n])
        )

        if only_reg or only_bq or type_mismatch:
            all_ok = False
            status = "MISMATCH"
        else:
            status = "OK"

        lines.append(f"### `{table_name}` — **{status}**")
        lines.append(f"- Registry columns: {len(reg_names)} | BigQuery columns: {len(bq_names)}")
        if only_reg:
            lines.append(f"- **In registry only:** `{', '.join(only_reg)}`")
        if only_bq:
            lines.append(f"- **In BigQuery only:** `{', '.join(only_bq)}`")
        if type_mismatch:
            mism = [f"`{n}` (registry={reg[n]}, bq={bq[n]})" for n in type_mismatch]
            lines.append(f"- **Type mismatch:** {', '.join(mism)}")
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    if all_ok and not extra_tables:
        lines.append("**All 13 tables match the registry (names and types).**")
    else:
        lines.append("**Action required:** update `schema_registry/tables/*.yaml` for mismatches above.")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines))
    print(REPORT_PATH.read_text())
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
