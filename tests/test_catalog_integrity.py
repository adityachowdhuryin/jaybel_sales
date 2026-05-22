"""Catalog integrity — no DB required."""

from __future__ import annotations

from backend.services import question_catalog as qc


def test_starter_count_matches_qa_set():
    assert qc.starter_count() == 97


def test_categories_at_least_ten():
    cats = qc.list_categories()
    assert len(cats) >= 10
    ids = {c["id"] for c in cats}
    assert "executive_kpi" in ids
    assert "sales_rep" in ids


def test_search_filter_by_category():
    hits = qc.search_starters("", category_id="executive_kpi", limit=50)
    assert hits
    assert all(h["category_id"] == "executive_kpi" for h in hits)
