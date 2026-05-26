"""Fiscal calendar label resolution."""

from datetime import date

from pipeline.fiscal_calendar import (
    current_fiscal_year_label,
    fiscal_year_label_for_date,
    last_fiscal_year_label,
)
from pipeline.time_range import is_fiscal_phrase, resolve_time_range


def test_fiscal_year_label_july_start():
  # August 2025 -> FY 2025-2026
    assert fiscal_year_label_for_date(date(2025, 8, 1)) == "2025-2026"
    # May 2026 -> still FY 2025-2026
    assert fiscal_year_label_for_date(date(2026, 5, 15)) == "2025-2026"
    # July 2026 -> FY 2026-2027
    assert fiscal_year_label_for_date(date(2026, 7, 1)) == "2026-2027"


def test_current_fy_resolution():
    tr = resolve_time_range("what's the current FY and start month and end month?")
    assert tr is not None
    assert tr.label == current_fiscal_year_label()
    assert tr.start == ""


def test_last_fy_resolution():
    tr = resolve_time_range("what's the last FY and start month and end month?")
    assert tr is not None
    assert tr.label == last_fiscal_year_label()


def test_explicit_fy_still_works():
    tr = resolve_time_range("start month of FY 2024-2025")
    assert tr and tr.label == "2024-2025"


def test_latest_fy_resolves_to_current():
    tr = resolve_time_range("What's the latest FY and start month and end month?")
    assert tr is not None
    assert tr.label == current_fiscal_year_label()


def test_last_fy_not_max_in_dimension():
    tr = resolve_time_range("What's the last FY and start month and end month?")
    assert tr.label == last_fiscal_year_label()
    assert tr.label != "2028-2029"
    assert tr.label != "2029-2030"
