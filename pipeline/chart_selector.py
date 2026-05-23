"""Deterministic chart_spec from L1 intent and query result shape."""

from __future__ import annotations

import re
from typing import Any

from pipeline.models import L1Result, QueryResult

TIME_DIM_HINTS = (
    "date",
    "month",
    "fiscal",
    "fy",
    "quarter",
    "year",
    "period",
    "week",
)
LABEL_DIM_HINTS = (
    "name",
    "account",
    "customer",
    "product",
    "category",
    "group",
    "territory",
    "rep",
    "item",
)
MEASURE_HINTS = (
    "sales",
    "revenue",
    "gp",
    "profit",
    "margin",
    "qty",
    "quantity",
    "total",
    "amount",
    "variance",
    "count",
    "average",
    "avg",
)
CURRENCY_HINTS = ("sales", "revenue", "gp_dollar", "gp$", "cost", "variance", "target", "actual")
PERCENT_HINTS = ("percent", "pct", "gp%", "margin", "rate")


def _norm(name: str) -> str:
    return name.lower().replace(" ", "_")


def _is_numeric_column(rows: list[dict[str, Any]], col: str) -> bool:
    for r in rows[:20]:
        v = r.get(col)
        if v is None:
            continue
        if isinstance(v, (int, float)):
            return True
        try:
            float(v)
            return True
        except (TypeError, ValueError):
            return False
    return False


def _score_dimension(col: str) -> int:
    n = _norm(col)
    if n in ("f0_", "f1_"):
        return -10
    score = 0
    if any(h in n for h in TIME_DIM_HINTS):
        score += 10
    if any(h in n for h in LABEL_DIM_HINTS):
        score += 5
    if n.endswith("_key") or n == "id":
        score -= 5
    return score


def _score_measure(col: str) -> int:
    n = _norm(col)
    score = 0
    if any(h in n for h in MEASURE_HINTS):
        score += 10
    if n in ("f0_",) or re.match(r"^f\d+_$", n):
        score += 3
    if any(h in n for h in ("target", "actual", "projected")):
        score += 8
    if "percent" in n or "pct" in n:
        score += 6
    return score


def _infer_format(col: str) -> str | None:
    n = _norm(col)
    if any(h in n for h in PERCENT_HINTS):
        return "percent"
    if any(h in n for h in CURRENCY_HINTS):
        return "currency"
    return "number"


def _pick_actual_target_series(
    rows: list[dict[str, Any]], columns: list[str]
) -> list[dict[str, str]] | None:
    """Detect actual + target measure columns for grouped / paired bars."""
    nums = [c for c in columns if _is_numeric_column(rows, c)]
    actual = [c for c in nums if "actual" in _norm(c)]
    target = [c for c in nums if "target" in _norm(c)]
    if not actual or not target:
        return None
    a, t = actual[0], target[0]
    return [
        {"key": a, "label": "Actual", "format": _infer_format(a) or "currency"},
        {"key": t, "label": "Target", "format": _infer_format(t) or "currency"},
    ]


def _pick_columns(
    rows: list[dict[str, Any]], columns: list[str]
) -> tuple[str | None, str | None]:
    if not rows or not columns:
        return None, None
    cols = list(columns) if columns else list(rows[0].keys())
    dim_candidates = [c for c in cols if not _is_numeric_column(rows, c)]
    num_candidates = [c for c in cols if _is_numeric_column(rows, c)]
    if not num_candidates:
        for c in cols:
            if c not in dim_candidates:
                num_candidates.append(c)
    if not dim_candidates and len(cols) >= 2:
        dim_candidates = [cols[0]]
        num_candidates = [c for c in cols[1:] if c != cols[0]]
    if not num_candidates:
        return None, None
    x = max(dim_candidates, key=_score_dimension, default=None) if dim_candidates else None
    y = max(num_candidates, key=_score_measure, default=num_candidates[0])
    if x is None and len(cols) >= 2:
        x = cols[0] if cols[0] != y else cols[1] if len(cols) > 1 else None
    return x, y


def _avg_label_len(rows: list[dict[str, Any]], x: str) -> float:
    lens = [len(str(r.get(x, ""))) for r in rows[:20]]
    return sum(lens) / max(len(lens), 1)


def _looks_like_time_axis(rows: list[dict[str, Any]], x: str) -> bool:
    n = _norm(x)
    if any(h in n for h in TIME_DIM_HINTS):
        return True
    sample = [str(r.get(x, "")) for r in rows[:5]]
    return any(re.match(r"^\d{4}", s) for s in sample)


def select_chart(
    question: str,
    l1: L1Result,
    query_result: QueryResult,
) -> dict[str, Any] | None:
    """Return chart_spec dict or None (table-only / KPI on UI)."""
    rows = query_result.rows
    if not rows:
        return None

    row_count = len(rows)
    intent = (l1.intent or "").lower()
    q = question.lower()

    if intent == "lookup" or row_count > 25:
        return None

    title = _title_from_question(question, l1)
    cols = query_result.columns or list(rows[0].keys())
    series = _pick_actual_target_series(rows, cols)
    x, y = _pick_columns(rows, cols)

    # Single row → KPI cards; optional Actual vs Target paired bar
    if row_count == 1:
        if series:
            return {
                "chart_type": "paired_bar",
                "x": "metric",
                "y": series[0]["key"],
                "title": title,
                "format": series[0].get("format"),
                "series": series,
                "source": "chart_selector",
            }
        return None

    if not y and not series:
        return None

    if series and row_count >= 2 and x:
        return {
            "chart_type": "grouped_bar",
            "x": x,
            "y": series[0]["key"],
            "title": title,
            "format": series[0].get("format"),
            "orientation": "vertical",
            "series": series,
            "source": "chart_selector",
        }

    if not y:
        return None
    fmt = _infer_format(y or "")
    chart_type = "bar"
    orientation: str | None = None

    if intent == "trend" or _looks_like_time_axis(rows, x or ""):
        chart_type = "line"
    elif ("breakdown" in q or "share" in q or "mix" in q) and row_count <= 8 and x:
        chart_type = "pie"
    elif intent == "ranking":
        chart_type = "bar"
        if x and _avg_label_len(rows, x) > 12:
            orientation = "horizontal"
    elif intent == "comparison":
        chart_type = "bar"
        if x and _avg_label_len(rows, x) > 14:
            orientation = "horizontal"
    elif intent == "aggregation" and row_count <= 8:
        chart_type = "bar"

    if chart_type == "pie" and row_count > 8:
        chart_type = "bar"

    if not x:
        return None

    return {
        "chart_type": chart_type,
        "x": x,
        "y": y,
        "title": title,
        "format": fmt,
        "orientation": orientation,
        "source": "chart_selector",
    }


def _title_from_question(question: str, l1: L1Result) -> str:
    q = question.strip()
    if len(q) <= 60:
        return q
    if l1.plan:
        return l1.plan[0][:80]
    return "Results"
