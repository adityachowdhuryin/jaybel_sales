from pipeline.time_range import is_fiscal_phrase, resolve_time_range


def test_last_month_calendar():
    tr = resolve_time_range("sales last month")
    assert tr is not None
    assert tr.start <= tr.end


def test_fiscal_year_phrase():
    assert is_fiscal_phrase("sales in fiscal year 2025-2026")
    tr = resolve_time_range("total sales fiscal year 2025-2026")
    assert tr and tr.label == "2025-2026"
