"""Bare 'year' resolves to Jaybel fiscal year (July–June)."""

from pipeline.fiscal_calendar import current_fiscal_year_label, last_fiscal_year_label
from pipeline.time_range import (
    is_calendar_year_exception,
    is_fiscal_phrase,
    resolve_time_range,
    year_phrase_means_fiscal,
)


def test_this_year_is_fiscal():
    assert year_phrase_means_fiscal("Total sales this year")
    tr = resolve_time_range("Total sales this year")
    assert tr is not None
    assert tr.label == current_fiscal_year_label()


def test_last_year_is_prior_fy():
    tr = resolve_time_range("Compare to last year")
    assert tr is not None
    assert tr.label == last_fiscal_year_label()


def test_ytd_is_fy_ytd():
    tr = resolve_time_range("Sales year to date")
    assert tr is not None
    assert tr.start
    assert tr.end
    assert tr.label == current_fiscal_year_label()


def test_calendar_year_exception():
    assert is_calendar_year_exception("Average GP in calendar year 2025")
    assert not year_phrase_means_fiscal("Average GP in calendar year 2025")


def test_fiscal_year_phrase_still_works():
    assert is_fiscal_phrase("sales in fiscal year 2025-2026")
    tr = resolve_time_range("total sales fiscal year 2025-2026")
    assert tr and tr.label == "2025-2026"
