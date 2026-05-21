"""Resolve relative dates in Australia/Sydney (calendar default, fiscal when asked)."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from pipeline.config import load_config, timezone_name
from pipeline.models import TimeRange

_FISCAL_KW = None


def _fiscal_keywords() -> list[str]:
    global _FISCAL_KW
    if _FISCAL_KW is None:
        _FISCAL_KW = [
            k.lower()
            for k in load_config()["bigquery"]["relative_dates"].get("fiscal_keywords", [])
        ]
    return _FISCAL_KW


def _tz_now() -> datetime:
    return datetime.now(ZoneInfo(timezone_name()))


def is_fiscal_phrase(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in _fiscal_keywords())


def resolve_time_range(question: str, llm_range: TimeRange | None = None) -> TimeRange | None:
    """Server-side resolution; LLM range used when explicit ISO dates provided."""
    if llm_range and llm_range.start and llm_range.end:
        return llm_range

    now = _tz_now().date()
    q = question.lower()
    fiscal = is_fiscal_phrase(question)

    if "yesterday" in q:
        d = now - timedelta(days=1)
        return TimeRange(start=d.isoformat(), end=d.isoformat(), label="yesterday")

    if "today" in q:
        return TimeRange(start=now.isoformat(), end=now.isoformat(), label="today")

    if "last month" in q and not fiscal:
        first_this = now.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        start = last_prev.replace(day=1)
        return TimeRange(start=start.isoformat(), end=last_prev.isoformat(), label="last month")

    if "this month" in q and not fiscal:
        start = now.replace(day=1)
        return TimeRange(start=start.isoformat(), end=now.isoformat(), label="this month")

    if "last year" in q and not fiscal:
        start = date(now.year - 1, 1, 1)
        end = date(now.year - 1, 12, 31)
        return TimeRange(start=start.isoformat(), end=end.isoformat(), label="last year")

    if "this year" in q and not fiscal:
        return TimeRange(
            start=date(now.year, 1, 1).isoformat(),
            end=now.isoformat(),
            label="this year",
        )

    # FY label e.g. 2025-2026
    m = re.search(r"20\d{2}-20\d{2}", question)
    if m and fiscal:
        return TimeRange(start="", end="", label=m.group(0))  # filter via dim_date.fy in SQL

    return llm_range


def format_time_range_for_prompt(tr: TimeRange | None) -> str:
    if not tr:
        return "No explicit time range; use question context and dim_date as needed."
    if tr.start and tr.end:
        return f"Use dates {tr.start} through {tr.end} inclusive ({tr.label or 'resolved'})."
    if tr.label:
        return f"Use fiscal year label fy = '{tr.label}' on dim_date."
    return "No time range."
