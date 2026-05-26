"""Resolve relative dates in Australia/Sydney (calendar default, fiscal when asked)."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from pipeline.config import load_config, timezone_name
from pipeline.models import TimeRange

_FISCAL_KW = None

_CURRENT_FY_RE = re.compile(
    r"\b(?:current|this|latest|most\s+recent)\s+(?:fiscal\s+)?(?:year|fy)\b"
    r"|\b(?:current|this|latest)\s+fy\b",
    re.I,
)
_LAST_FY_RE = re.compile(
    r"\b(?:last|previous|prior)\s+(?:fiscal\s+)?(?:year|fy)\b|\blast\s+fy\b",
    re.I,
)


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
    now = _tz_now().date()
    q = question.lower()
    fiscal = is_fiscal_phrase(question)

    # Authoritative fiscal FY labels — override LLM date guesses (e.g. Apr–Sep)
    if fiscal:
        from pipeline.fiscal_calendar import (
            current_fiscal_year_label,
            last_fiscal_year_label,
        )

        m = re.search(r"20\d{2}-20\d{2}", question)
        if m:
            return TimeRange(start="", end="", label=m.group(0))
        if _CURRENT_FY_RE.search(question):
            return TimeRange(
                start="",
                end="",
                label=current_fiscal_year_label(),
            )
        if _LAST_FY_RE.search(question):
            return TimeRange(
                start="",
                end="",
                label=last_fiscal_year_label(),
            )

    if llm_range and llm_range.start and llm_range.end:
        return llm_range

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

    return llm_range


def format_time_range_for_prompt(tr: TimeRange | None) -> str:
    if not tr:
        from pipeline.fiscal_calendar import fiscal_calendar_prompt_block

        return (
            "No explicit time range; use question context and dim_date as needed. "
            + fiscal_calendar_prompt_block()
        )
    if tr.start and tr.end:
        return f"Use dates {tr.start} through {tr.end} inclusive ({tr.label or 'resolved'})."
    if tr.label:
        return (
            f"MANDATORY time filter: WHERE fy = '{tr.label}' (exact string). "
            "Do NOT use ORDER BY fy DESC, MAX(fy), DISTINCT fy without this filter, "
            "or pick the latest row in dim_date — relative phrases are already resolved. "
            "Full FY: fiscal_month_no=1 is July (start), fiscal_month_no=12 is June (end). "
            "Return start_month and end_month via MIN/MAX on fiscal_month_name for months 1 and 12."
        )
    return "No time range."
