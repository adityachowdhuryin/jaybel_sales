"""Schema-driven column alias map (config/column_aliases.yaml)."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from pipeline.config import PROJECT_ROOT

ALIASES_PATH = PROJECT_ROOT / "config" / "column_aliases.yaml"


@lru_cache(maxsize=1)
def load_aliases_config() -> dict[str, Any]:
    if not ALIASES_PATH.is_file():
        return {}
    with ALIASES_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_alias(table_id: str | None, column: str) -> str | None:
    cfg = load_aliases_config()
    col = column.lower()
    by_table = cfg.get("by_table") or {}
    if table_id and table_id in by_table:
        mapped = (by_table[table_id] or {}).get(col) or (by_table[table_id] or {}).get(column)
        if mapped:
            return mapped
    global_map = cfg.get("global") or {}
    return global_map.get(col) or global_map.get(column)


def suggested_replacements(table_id: str, bad_columns: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for col in bad_columns:
        repl = resolve_alias(table_id, col)
        if repl and repl != col:
            out[col] = repl
    return out


def apply_column_aliases(sql: str, table_id: str | None = None) -> str:
    """Replace known bad column tokens (word-boundary regex)."""
    cfg = load_aliases_config()
    patterns: list[tuple[str, str]] = []
    for src, dst in (cfg.get("global") or {}).items():
        patterns.append((src, dst))
    if table_id:
        for src, dst in (cfg.get("by_table") or {}).get(table_id, {}).items():
            patterns.append((src, dst))
    out = sql
    seen: set[tuple[str, str]] = set()
    for src, dst in patterns:
        key = (src.lower(), dst)
        if key in seen:
            continue
        seen.add(key)
        out = re.sub(rf"\b{re.escape(src)}\b", dst, out, flags=re.IGNORECASE)
    return out


def value_hints_snippet() -> str:
    cfg = load_aliases_config()
    hints = cfg.get("value_hints") or {}
    lines = ["Value hints (filters):"]
    for col, meta in hints.items():
        if isinstance(meta, dict):
            desc = meta.get("description", "")
            ex = meta.get("examples") or []
            lines.append(f"- {col}: {desc} Examples: {', '.join(str(x) for x in ex)}")
    return "\n".join(lines) if len(lines) > 1 else ""


def glossary_snippet_for_l2() -> str:
    cfg = load_aliases_config()
    lines = ["Column aliases (always use registry names):"]
    for src, dst in (cfg.get("global") or {}).items():
        lines.append(f"- Do not use {src}; use {dst}")
    metrics = cfg.get("metric_columns") or {}
    if metrics:
        lines.append("Metrics:")
        for term, col in metrics.items():
            lines.append(f"- {term} → {col}")
    vh = value_hints_snippet()
    if vh:
        lines.append(vh)
    return "\n".join(lines)
