"""Load config/sql_generation.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from pipeline.config import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "config" / "sql_generation.yaml"


@lru_cache(maxsize=1)
def load_sql_generation_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return {}
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def repair_config() -> dict[str, Any]:
    return load_sql_generation_config().get("repair") or {}


def schema_context_config() -> dict[str, Any]:
    return load_sql_generation_config().get("schema_context") or {}


def few_shot_config() -> dict[str, Any]:
    return load_sql_generation_config().get("few_shot") or {}
