"""Deterministic empty-result answer (A4)."""

from __future__ import annotations

from pipeline.analytics_context import detect_archetypes
from pipeline.models import L1Result, QueryResult
from pipeline.time_range import format_time_range_for_prompt


def build_empty_result_markdown(
    question: str,
    l1: L1Result,
    sql: str,
    query_result: QueryResult,
    table_display: str,
) -> str:
    arch = detect_archetypes(question)
    period = format_time_range_for_prompt(l1.time_range)
    suggestions = [
        "Widen the date range (e.g. full fiscal year 2025-2026).",
        "Check spelling of customer, product, or category filters.",
        "Remove an extra filter (region, rep, department) that may be too narrow.",
    ]
    if arch.target:
        suggestions.append(
            "Confirm category filters (e.g. BTS) match how products are coded in dim_product."
        )
    if l1.entities:
        suggestions.append(
            f"Verify entity values: {', '.join(l1.entities[:5])}."
        )

    lines = [
        "## Summary",
        "",
        f"No rows matched your filters for **{table_display}**.",
        "",
        "## Key figures",
        "",
        "- _(No figures in result set)_",
        "",
        "## Notes",
        "",
        f"- Period: {period}",
        f"- Rows returned: {query_result.row_count}",
        "",
        "## Suggestions",
        "",
    ]
    for s in suggestions:
        lines.append(f"- {s}")

    disclaimers: list[str] = []
    if arch.run_rate:
        disclaimers.append(
            "Run-rate projections need MTD data; an empty set cannot produce a projection."
        )
    if arch.bi_forecast_only:
        disclaimers.append(
            "BI forecast variance is not in BigQuery; compare actuals and config targets instead."
        )
    if disclaimers:
        lines.extend(["", "## Caveats", ""])
        for d in disclaimers:
            lines.append(f"- {d}")

    return "\n".join(lines) + "\n"


def empty_result_guidance_suggestions(l1: L1Result) -> list[str]:
    out = ["Try a wider fiscal or calendar period."]
    if l1.entities:
        out.append(f"Check filters for: {', '.join(l1.entities[:3])}.")
    return out
