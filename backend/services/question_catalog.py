"""Question catalog — categories, starters, follow-ups."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from pipeline.config import PROJECT_ROOT, question_catalog_path


def _catalog_path() -> Path:
    override = os.getenv("QUESTION_CATALOG_PATH")
    if override:
        p = Path(override)
        return p if p.is_absolute() else PROJECT_ROOT / p
    return question_catalog_path()


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    path = _catalog_path()
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def reload_catalog() -> None:
    load_catalog.cache_clear()


def list_categories() -> list[dict[str, Any]]:
    return sorted(load_catalog()["categories"], key=lambda c: c.get("order", 99))


def starters_for_category(category_id: str) -> list[dict[str, Any]]:
    return [s for s in load_catalog()["starters"] if s["category_id"] == category_id]


def starter_by_id(starter_id: str) -> dict[str, Any] | None:
    for s in load_catalog()["starters"]:
        if s["id"] == starter_id:
            return s
    return None


def follow_ups_for_starter(starter_id: str) -> list[dict[str, Any]]:
    return [f for f in load_catalog()["follow_ups"] if f["parent_starter_id"] == starter_id]


def match_starter_by_text(question: str) -> dict[str, Any] | None:
    q = _normalize(question)
    for s in load_catalog()["starters"]:
        if _normalize(s["text"]) == q:
            return s
    return None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def follow_ups_from_rules(
    *,
    last_intent: str | None,
    last_table_id: str | None,
    last_category_id: str | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rule in load_catalog().get("rules") or []:
        when = rule.get("when") or {}
        if when.get("last_intent") and when["last_intent"] != last_intent:
            continue
        if when.get("last_table_id") and when["last_table_id"] != last_table_id:
            continue
        if when.get("last_category_id") and when["last_category_id"] != last_category_id:
            continue
        for i, sug in enumerate(rule.get("suggestions") or []):
            out.append(
                {
                    "id": f"rule-{rule['id']}-{i}",
                    "text": sug["text"],
                    "data_availability": sug.get("data_availability", "full"),
                    "source": "rules",
                }
            )
    return out[:5]


def resolve_follow_ups(
    *,
    starter_id: str | None = None,
    question: str | None = None,
    last_turn: dict[str, Any] | None = None,
    ui_context: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    ctx = ui_context or {}
    sid = starter_id or ctx.get("last_starter_id")
    if sid:
        items = follow_ups_for_starter(sid)
        if items:
            return [_public_follow_up(f) for f in items], "curated"
    if question:
        matched = match_starter_by_text(question)
        if matched:
            items = follow_ups_for_starter(matched["id"])
            if items:
                return [_public_follow_up(f) for f in items], "curated"
    if last_turn:
        table = last_turn.get("table_id") or ""
        if table and "." in table:
            table = table.split(".")[-1]
        category = last_turn.get("category_id") or ctx.get("last_category_id")
        items = follow_ups_from_rules(
            last_intent=last_turn.get("intent"),
            last_table_id=table,
            last_category_id=category,
        )
        if items:
            return items, "rules"
    return [], "none"


def _public_follow_up(f: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f["id"],
        "text": f["text"],
        "data_availability": f.get("data_availability", "full"),
        "intent": f.get("intent"),
    }


def search_starters(
    query: str,
    *,
    limit: int = 20,
    category_id: str | None = None,
    table_id: str | None = None,
    intent: str | None = None,
) -> list[dict[str, Any]]:
    q = _normalize(query)
    hits: list[dict[str, Any]] = []
    for s in load_catalog()["starters"]:
        if category_id and s.get("category_id") != category_id:
            continue
        if intent and s.get("intent") != intent:
            continue
        if table_id:
            short = (s.get("expected_table_id") or "").split(".")[-1]
            if table_id not in (s.get("expected_table_id") or "", short):
                continue
        if q and q not in _normalize(s["text"]):
            continue
        if not q and not (category_id or table_id or intent):
            continue
        hits.append(s)
    return hits[:limit]


def starter_count() -> int:
    return len(load_catalog().get("starters") or [])
