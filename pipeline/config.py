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


def auth_provider() -> str:
    return load_config()["auth"]["provider"]


def default_user_id() -> str:
    return str(load_config()["auth"]["default_user_id"])


def default_user_email() -> str:
    return str(load_config()["auth"]["default_user_email"])


def local_database_url() -> str:
    return str(load_config()["local_app"]["postgres"]["default_url"])


def api_base_url() -> str:
    return str(load_config()["local_app"]["api"]["base_url"])


def agent_engine_resource_env() -> str:
    """Path hint for deploy output (not loaded from env here)."""
    return str(PROJECT_ROOT / "agent" / "AGENT_ENGINE_RESOURCE.env")


def question_catalog_path() -> Path:
    rel = load_config().get("ui", {}).get(
        "question_catalog_path", "content/question_catalog.yaml"
    )
    return PROJECT_ROOT / rel


def sales_targets_path() -> Path:
    rel = load_config().get("client_questions", {}).get(
        "sales_targets_path", "config/sales_targets.yaml"
    )
    return PROJECT_ROOT / rel
