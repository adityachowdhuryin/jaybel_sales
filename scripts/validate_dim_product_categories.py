#!/usr/bin/env python3
"""Compare dim_product.main_group_name in BigQuery to config/jaybel.yaml examples."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from pipeline.bq_client import get_client
from pipeline.config import load_config


def main() -> None:
    cfg = load_config()
    project = cfg["gcp"]["project_id"]
    dataset = cfg["bigquery"]["dataset"]
    sql = f"""
    SELECT DISTINCT main_group_name
    FROM `{project}.{dataset}.dim_product`
    WHERE main_group_name IS NOT NULL
    ORDER BY 1
    """
    client = get_client()
    rows = list(client.query(sql).result())
    live = {r.main_group_name for r in rows}
    expected = set(cfg.get("client_questions", {}).get("product_categories_examples") or [])
    print("Live main_group_name values:")
    for name in sorted(live):
        print(f"  - {name}")
    missing = expected - live
    extra = live - expected
    if missing:
        print("\nConfigured examples NOT in BigQuery:", sorted(missing))
    if extra:
        print("\nIn BigQuery but not in config examples (sample):", sorted(extra)[:20])
    if missing:
        sys.exit(1)
    print("\nOK: all configured category examples exist in dim_product.")


if __name__ == "__main__":
    main()
