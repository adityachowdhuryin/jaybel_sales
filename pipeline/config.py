"""Load config/jaybel.yaml and resolve project paths."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "jaybel.yaml"
SCHEMA_REGISTRY_DIR = PROJECT_ROOT / "schema_registry" / "tables"
JOIN_ALLOWLIST_PATH = PROJECT_ROOT / "schema_registry" / "join_allowlist.yaml"


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def gcp_project_id() -> str:
    return load_config()["gcp"]["project_id"]


def bq_dataset() -> str:
    return load_config()["bigquery"]["dataset"]


def timezone_name() -> str:
    return load_config()["bigquery"]["timezone"]


def llm_model() -> str:
    return load_config()["vertex"]["llm_model"]


def bytes_scanned_limit_gb() -> float:
    return float(load_config()["bigquery"]["default_bytes_scanned_limit_gb"])


def query_row_limit() -> int:
    return int(load_config()["bigquery"]["default_query_limit"])
