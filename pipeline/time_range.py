"""Resolve relative dates in Australia/Sydney (calendar month/day; fiscal year for "year")."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from pipeline.config import load_config, timezone_name
from pipeline.models import TimeRange

_FISCAL_KW = None
_RELATIVE_CFG = None

_CURRENT_FY_RE = re.compile(
    r"\b(?:current|this|latest|most\s+recent)\s+(?:fiscal\s+)?(?:year|fy)\b"
    r"|\b(?:current|this|latest)\s+fy\b",
    re.I,
)
_LAST_FY_RE = re.compile(
    r"\b(?:last|previous|prior)\s+(?:fiscal\s+)?(?:year|fy)\b|\blast\s+fy\b",
    re.I,
)
_THIS_YEAR_RE = re.compile(r"\bthis\s+year\b|\bcurrent\s+year\b", re.I)
_LAST_YEAR_RE = re.compile(r"\b(?:last|previous|prior)\s+year\b", re.I)
_YTD_RE = re.compile(
    r"\b(?:fy[\s-]?)?ytd\b|\byear[\s-]to[\s-]date\b|\bytd\b",
    re.I,
)
_BARE_YEAR_RE = re.compile(r"\byear\b", re.I)
_YOY_RE = re.compile(r"\byear[\s-]over[\s-]year\b|\byoy\b", re.I)


def _relative_cfg() -> dict:
    global _RELATIVE_CFG
    if _RELATIVE_CFG is None:
        _RELATIVE_CFG = load_config()["bigquery"].get("relative_dates") or {}
    return _RELATIVE_CFG


def _fiscal_keywords() -> list[str]:
    global _FISCAL_KW
    if _FISCAL_KW is None:
        base = [
            k.lower()
            for k in _relative_cfg().get("fiscal_keywords", [])
        ]
        if _relative_cfg().get("year_means_fiscal", True):
            base.extend(["year", "ytd", "year to date", "year-over-year", "yoy"])
        _FISCAL_KW = list(dict.fromkeys(base))
    return _FISCAL_KW


def _tz_now() -> datetime:
    return datetime.now(ZoneInfo(timezone_name()))


def _calendar_year_exceptions() -> list[str]:
    return [str(x).lower() for x in _relative_cfg().get("calendar_year_exceptions") or []]


def is_calendar_year_exception(text: str) -> bool:
    lower = text.lower()
    return any(exc in lower for exc in _calendar_year_exceptions())


def year_phrase_means_fiscal(text: str) -> bool:
    if not _relative_cfg().get("year_means_fiscal", True):
        return False
    if is_calendar_year_exception(text):
        return False
    if _YTD_RE.search(text):
        return True
    if _THIS_YEAR_RE.search(text) or _LAST_YEAR_RE.search(text):
        return True
    if _YOY_RE.search(text):
        return True
    if _BARE_YEAR_RE.search(text):
        return True
    return False


def is_fiscal_phrase(text: str) -> bool:
    lower = text.lower()
    if is_calendar_year_exception(text):
        return any(
            k in lower
            for k in (
                "fiscal",
                "fy",
                "fiscal year",
                "fiscal month",
                "fiscal quarter",
            )
        )
    explicit = ("fiscal", "fy", "fiscal year", "fiscal month", "fiscal quarter")
    if any(k in lower for k in explicit):
        return True
    return year_phrase_means_fiscal(text)


def _fy_ytd_range(now: date) -> TimeRange:
    from pipeline.fiscal_calendar import fiscal_year_label_for_date, fiscal_year_start_date

    fy_label = fiscal_year_label_for_date(now)
    start = fiscal_year_start_date(now)
    return TimeRange(
        start=start.isoformat(),
        end=now.isoformat(),
        label=fy_label,
    )


def resolve_time_range(question: str, llm_range: TimeRange | None = None) -> TimeRange | None:
    """Server-side resolution; LLM range used when explicit ISO dates provided."""
    now = _tz_now().date()
    q = question.lower()
    fiscal = is_fiscal_phrase(question)

    if fiscal and _YTD_RE.search(question) and not is_calendar_year_exception(question):
        return _fy_ytd_range(now)

    # Authoritative fiscal FY labels — override LLM date guesses (e.g. Apr–Sep)
    if fiscal:
        from pipeline.fiscal_calendar import (
            current_fiscal_year_label,
            last_fiscal_year_label,
        )

        m = re.search(r"20\d{2}-20\d{2}", question)
        if m:
            return TimeRange(start="", end="", label=m.group(0))
        if _CURRENT_FY_RE.search(question) or (
            year_phrase_means_fiscal(question) and _THIS_YEAR_RE.search(question)
        ):
            return TimeRange(
                start="",
                end="",
                label=current_fiscal_year_label(),
            )
        if _LAST_FY_RE.search(question) or (
            year_phrase_means_fiscal(question) and _LAST_YEAR_RE.search(question)
        ):
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

    # Calendar year only when fiscal mode off or explicit calendar exception without FY phrasing
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
            "Bare 'year' means fiscal year (Jul–Jun), not calendar year. "
            + fiscal_calendar_prompt_block()
        )
    if tr.start and tr.end and tr.label and re.match(r"20\d{2}-20\d{2}", tr.label or ""):
        return (
            f"Use dates {tr.start} through {tr.end} inclusive (FY {tr.label}, FY-YTD if end is today)."
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
