"""Markdown answer normalization."""

from pipeline.answer_generator import (
    _normalize_markdown_answer,
    _normalize_markdown_sections,
)


def test_normalize_markdown_answer_alias():
    assert _normalize_markdown_answer is _normalize_markdown_sections


def test_adds_missing_sections():
    text = "Sales are up this year."
    out = _normalize_markdown_sections(
        text,
        [{"total_sales": 1000000}],
        ["total_sales"],
        ["Run-rate estimate only."],
    )
    assert "## Summary" in out
    assert "## Key figures" in out
    assert "## Caveats" in out
    assert "total_sales" in out.lower() or "Total Sales" in out
    assert "Run-rate" in out
