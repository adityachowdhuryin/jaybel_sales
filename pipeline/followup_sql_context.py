"""Extract metric and filter context from prior SQL for L2 follow-ups."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline.followup_context import FollowUpContext

_METRIC_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bline_gp_dollar\b", "line_gp_dollar (GP)"),
    (r"\bline_sales_ex_gst\b", "line_sales_ex_gst (sales ex GST)"),
    (r"\bgp_percent\b", "gp_percent (GP %)"),
    (r"\bSUM\s*\(\s*f\.line_gp", "line_gp_dollar (GP)"),
    (r"\bSUM\s*\(\s*f\.line_sales", "line_sales_ex_gst (sales ex GST)"),
)


def extract_metric_from_sql(sql: str | None) -> str | None:
    if not sql:
        return None
    for pattern, label in _METRIC_PATTERNS:
        if re.search(pattern, sql, re.IGNORECASE):
            return label
    return None


def extract_filter_summary(sql: str | None, max_len: int = 400) -> str | None:
    if not sql:
        return None
    m = re.search(r"\bWHERE\b(.+?)(?:\bGROUP\b|\bORDER\b|\bLIMIT\b|\bHAVING\b|$)", sql, re.I | re.S)
    if not m:
        return None
    clause = " ".join(m.group(1).split())
    return clause[:max_len] if clause else None


def format_l2_followup_block(ctx: FollowUpContext) -> str:
    if not ctx.is_follow_up:
        return ""
    lines = [
        "Follow-up context (preserve unless user explicitly changes):",
    ]
    if ctx.prior_question:
        lines.append(f"Prior question: {ctx.prior_question}")
    if ctx.prior_metric:
        lines.append(f"Prior metric: {ctx.prior_metric}")
    if ctx.prior_filters:
        lines.append(f"Prior filters: {ctx.prior_filters}")
    if ctx.prior_join_pattern:
        lines.append(f"Prior join_pattern: {ctx.prior_join_pattern}")
    if ctx.prior_sql_excerpt:
        lines.append(f"Prior SQL excerpt:\n{ctx.prior_sql_excerpt[:800]}")
    lines.append(
        "Rules: keep the same metric (GP vs sales) unless the user changes it. "
        "For territory filters use territory_code (JAY, FRA, JOK, EXP, NSW) — "
        "do not invent APAC or region labels."
    )
    return "\n".join(lines)
