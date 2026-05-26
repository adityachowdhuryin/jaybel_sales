"""Load config/query_understanding.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from pipeline.config import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "config" / "query_understanding.yaml"


@lru_cache(maxsize=1)
def load_query_understanding_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return {}
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _section(name: str) -> dict[str, Any]:
    return load_query_understanding_config().get(name) or {}


def routing_config() -> dict[str, Any]:
    return _section("routing")


def scope_config() -> dict[str, Any]:
    return _section("scope")


def rep_patterns() -> list[str]:
    return list(_section("rep").get("patterns") or [])


def sales_keywords() -> list[str]:
    return list(_section("off_topic").get("sales_keywords") or [])


def external_concepts() -> list[str]:
    return list(_section("external_concepts") or [])


def l0_classifier_config() -> dict[str, Any]:
    return _section("l0_classifier")


def follow_up_config() -> dict[str, Any]:
    return _section("follow_up")


def empty_result_config() -> dict[str, Any]:
    return _section("empty_result")


def metric_signals() -> list[str]:
    return list(load_query_understanding_config().get("metric_signals") or [])


def period_signals() -> list[str]:
    return list(load_query_understanding_config().get("period_signals") or [])
