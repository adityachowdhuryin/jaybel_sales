"""Deterministic SQL column repair from validator feedback."""

from __future__ import annotations

import re

from pipeline.column_aliases import suggested_replacements
from pipeline.models import ValidationResult


def repair_sql_from_validation(
    sql: str,
    fail: ValidationResult,
    *,
    table_id: str | None = None,
) -> tuple[str, bool]:
    """Apply alias map to fix known bad columns. Returns (sql, changed)."""
    if fail.validator != "column_check":
        return sql, False

    details = fail.details or {}
    tid = table_id or details.get("table_id")
    bad = list(details.get("bad_columns") or [])
    if not bad and fail.message:
        bad = _parse_bad_from_message(fail.message)

    replacements = details.get("suggested_replacements") or suggested_replacements(
        tid or "", bad
    )
    out = sql
    changed = False
    for src, dst in replacements.items():
        new_out = re.sub(rf"\b{re.escape(src)}\b", dst, out, flags=re.IGNORECASE)
        if new_out != out:
            out = new_out
            changed = True
    return out, changed


def _parse_bad_from_message(message: str) -> list[str]:
    m = re.search(r"Invalid columns on [^:]+:\s*\[(.*?)\]", message)
    if not m:
        return []
    inner = m.group(1)
    return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
