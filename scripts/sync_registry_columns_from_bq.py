#!/usr/bin/env python3
"""Merge live BigQuery column names/types into schema_registry YAML (keeps descriptions/tags)."""
from __future__ import annotations

from pathlib import Path

import yaml
from google.cloud import bigquery

PROJECT = "jaybel-dev"
DATASET = "jaybel_sales_analytics"
REGISTRY_DIR = Path(__file__).resolve().parents[1] / "schema_registry" / "tables"

# registry yaml basename -> BQ table id (when they differ)
TABLE_MAP = {
    "fact_new_business": "fact_new_business_frazer",
}

BQ_TO_REGISTRY = {
    "INTEGER": "INT64",
    "FLOAT": "FLOAT64",
    "BOOLEAN": "BOOL",
}


def bq_type(field_type: str) -> str:
    return BQ_TO_REGISTRY.get(field_type.upper(), field_type.upper())


def main() -> None:
    client = bigquery.Client(project=PROJECT)
    for yaml_path in sorted(REGISTRY_DIR.glob("*.yaml")):
        stem = yaml_path.stem
        bq_name = TABLE_MAP.get(stem, stem)
        ref = f"{PROJECT}.{DATASET}.{bq_name}"
        table = client.get_table(ref)
        data = yaml.safe_load(yaml_path.read_text())
        existing = {c["name"]: c for c in data.get("columns", [])}

        new_columns = []
        for field in table.schema:
            base = existing.get(field.name, {})
            new_columns.append(
                {
                    "name": field.name,
                    "type": bq_type(field.field_type),
                    "description": base.get("description", f"{field.name} ({field.field_type})"),
                    "nullable": base.get("nullable", field.mode != "REQUIRED"),
                    **(
                        {"sample_values": base["sample_values"]}
                        if "sample_values" in base
                        else {}
                    ),
                }
            )

        data["columns"] = new_columns
        if bq_name != stem:
            data["table_id"] = f"{PROJECT}.{DATASET}.{bq_name}"
            new_path = REGISTRY_DIR / f"{bq_name}.yaml"
        else:
            new_path = yaml_path

        with new_path.open("w") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
        if new_path != yaml_path and yaml_path.exists():
            yaml_path.unlink()
            print(f"renamed {yaml_path.name} -> {new_path.name}")
        print(f"synced {new_path.name} ({len(new_columns)} columns)")


if __name__ == "__main__":
    main()
