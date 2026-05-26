"""Jaybel fiscal calendar (July–June, label YYYY-YYYY)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from pipeline.config import load_config, timezone_name


def _tz_now() -> datetime:
    return datetime.now(ZoneInfo(timezone_name()))


def _fiscal_start_year(d: date) -> int:
    """Calendar year in which this FY begins (July)."""
    cfg = load_config()["bigquery"].get("fiscal_year") or {}
    start_month_name = (cfg.get("start_month") or "July").lower()
    # July = month 7
    start_month = 7 if start_month_name.startswith("jul") else 7
    return d.year if d.month >= start_month else d.year - 1


def fiscal_year_label_for_date(d: date) -> str:
    start = _fiscal_start_year(d)
    return f"{start}-{start + 1}"


def current_fiscal_year_label() -> str:
    return fiscal_year_label_for_date(_tz_now().date())


def last_fiscal_year_label() -> str:
    start = _fiscal_start_year(_tz_now().date())
    return f"{start - 1}-{start}"


def fiscal_calendar_prompt_block() -> str:
    cfg = load_config()["bigquery"].get("fiscal_year") or {}
    start_m = cfg.get("start_month", "July")
    end_m = cfg.get("end_month", "June")
    tz = timezone_name()
    cur = current_fiscal_year_label()
    prev = last_fiscal_year_label()
    return (
        f"Jaybel fiscal year ({tz}): always {start_m} (fiscal_month_no=1) through "
        f"{end_m} (fiscal_month_no=12). Label format YYYY-YYYY. "
        f"Q1=Jul–Sep, Q2=Oct–Dec, Q3=Jan–Mar, Q4=Apr–Jun — Q4 is NOT the full FY. "
        f"Resolved today: current_fy={cur}, last_fy={prev}. "
        f"Never use April–September as full fiscal year boundaries."
    )
