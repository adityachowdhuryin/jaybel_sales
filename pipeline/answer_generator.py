"""Layer 5 — natural language answer (markdown) + chart from chart_selector."""

from __future__ import annotations

import json
import re
from typing import Any

from pipeline.analytics_context import detect_archetypes
from pipeline.models import AnswerResult, L1Result, QueryResult
from pipeline.vertex_llm import generate_text

L5_SYSTEM = """You are a business analyst summarizing query results for Jaybel sales analytics.

Output MUST be GitHub-flavored Markdown with these sections (omit empty sections):

## Summary
One or two sentences with the main finding and headline number(s).

## Key figures
Use bullet lines with bold labels, e.g.:
- **Total sales (FY 2025-2026):** $1,234,567.89
- **Variance vs target:** -$10,000 (1.2%)

## Notes
Optional bullets for context (period, filters, rep scope).

## Caveats
Only when disclaimers apply (run-rate estimate, config target, pattern match, BI forecast unavailable).

Rules:
- Only use numbers and facts present in the JSON data — never invent metrics.
- Format currency with $ and commas; percentages with one decimal and % sign.
- Do not include CHART_JSON or chart configuration — charts are handled separately.
- Under 200 words unless the user asked for a detailed breakdown.
- Do not expose SQL unless the user asked how the query was built.
"""


class AnswerGenerator:
    def generate(
        self,
        question: str,
        l1: L1Result,
        sql: str,
        query_result: QueryResult,
    ) -> AnswerResult:
        data_sample = query_result.rows[:100]
        arch = detect_archetypes(question)
        disclaimers: list[str] = []
        if arch.run_rate:
            disclaimers.append(
                "Projection is a **run-rate estimate** using working days — not the "
                "Power BI Projected Monthly Sales/GP measure."
            )
        if arch.target:
            disclaimers.append(
                "Target amounts are from **config/sales_targets.yaml** (Office Supplies BI PDF), "
                "not a BigQuery budget table."
            )
        if arch.closed_account:
            disclaimers.append(
                "Closed status is inferred from **account_name** patterns; "
                "there is no dedicated account_status column."
            )
        if arch.embroidery:
            disclaimers.append(
                "Embroidery/custom print rows matched **keyword rules** on staging description."
            )
        if arch.bi_forecast_only:
            disclaimers.append(
                "The BI forecast variance cannot be reproduced from BigQuery; "
                "compare actuals and config targets instead."
            )
        disc_block = "\n".join(f"- {d}" for d in disclaimers)
        user = f"""Question: {question}
Intent: {l1.intent}
Plan: {l1.plan}

Rows returned: {query_result.row_count}
Columns: {query_result.columns}

Mandatory Caveats section content (merge into ## Caveats if non-empty):
{disc_block or "(none)"}

Data JSON:
{json.dumps(data_sample, default=str)[:120000]}
"""
        raw = generate_text(L5_SYSTEM, user, temperature=0.2)
        text = _strip_legacy_chart_json(raw)
        text = _normalize_markdown_answer(
            text,
            query_result.rows[:5],
            query_result.columns,
            disclaimers,
        )
        return AnswerResult(text=text, chart_spec=None)


def _strip_legacy_chart_json(raw: str) -> str:
    m = re.search(r"CHART_JSON:\s*\{.*?\}", raw, re.DOTALL)
    if m:
        return raw[: m.start()].strip()
    return raw.strip()


def _humanize_col(name: str) -> str:
    return name.replace("_", " ").strip().title()


def _format_metric_value(value: Any, col: str) -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    cn = col.lower()
    if "percent" in cn or "pct" in cn or cn.endswith("_pct"):
        pct = n * 100 if abs(n) <= 1 and n != 0 else n
        return f"{pct:,.1f}%"
    if any(
        x in cn
        for x in ("sales", "revenue", "gp", "cost", "variance", "target", "actual", "amount")
    ):
        return f"${n:,.2f}"
    return f"{n:,.2f}"


def _fallback_key_figures(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "- _(No figures in result set)_"
    row = rows[0]
    cols = columns or list(row.keys())
    lines: list[str] = []
    for col in cols:
        v = row.get(col)
        if v is None:
            continue
        try:
            float(v)
        except (TypeError, ValueError):
            continue
        lines.append(f"- **{_humanize_col(col)}:** {_format_metric_value(v, col)}")
        if len(lines) >= 6:
            break
    return "\n".join(lines) if lines else "- _(See table below)_"


def _normalize_markdown_sections(
    text: str,
    sample_rows: list[dict[str, Any]],
    columns: list[str],
    disclaimers: list[str],
) -> str:
    """Ensure standard sections; fill Key figures / Caveats when the model omits them."""
    body = text.strip()
    if "## Summary" not in body:
        body = f"## Summary\n\n{body}\n" if body else "## Summary\n\n_No summary generated._\n"
    if "## Key figures" not in body:
        body = f"{body.rstrip()}\n\n## Key figures\n\n{_fallback_key_figures(sample_rows, columns)}\n"
    if disclaimers and "## Caveats" not in body:
        bullets = "\n".join(f"- {d}" for d in disclaimers)
        body = f"{body.rstrip()}\n\n## Caveats\n\n{bullets}\n"
    if "## Notes" not in body and disclaimers:
        pass
    return body
