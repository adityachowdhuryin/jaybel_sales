"""Layer 1 — intent, table routing, join pattern, plan."""

from __future__ import annotations

import json
from typing import Any

from pipeline.models import L1Result, TableMeta
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.keyword_index import KeywordIndex
from pipeline.registry.loader import Registry
from pipeline.analytics_context import l1_routing_hints, prompt_block as analytics_prompt_block
from pipeline.time_range import resolve_time_range
from pipeline.user_context import UserContext
from pipeline.vertex_llm import generate_text, parse_json_response

L1_SYSTEM = """You are a BigQuery analytics router for Jaybel sales data.
Return ONLY valid JSON with keys:
intent (aggregation|trend|comparison|lookup|ranking|anomaly|breakdown|filter_followup),
table_id (exact id from catalog),
join_pattern (fact_sales_with_dims | fact_new_business_frazer_with_dims | null for single-table),
confidence (0-1),
entities (string array of dimension values mentioned, e.g. Frazer, Furniture, APAC),
time_range ({start,end,label} ISO dates or fy label, or null),
plan (3-5 plain-English SQL steps, no SQL syntax).

Rules:
- Prefer fact_sales_report for sales/revenue/GP; fact_new_business_frazer for Frazer new business.
- Use stg_total_working_days for working days OR scalar subqueries in run-rate projection SQL.
- Use stg_sales_report for embroidery/custom printing line descriptions (STRING columns).
- Use staging tables only if user asks for raw/source data or embroidery jobs.
- join_pattern required when querying a fact table with dimensions.
- FY targets come from config prompts, not a BigQuery target table.
- Jaybel fiscal year: July (fiscal_month_no=1) through June (fiscal_month_no=12); label YYYY-YYYY (e.g. 2025-2026). Never April–September as full FY.
- Bare "year", "this year", "last year", and YTD mean fiscal year (not calendar Jan–Dec) unless the user says "calendar year".
- "My" / "our" (company-wide) questions are not rep-scoped unless the user asks about commission, payout, or personal closed deals.
- Product-level questions use fact_sales_report.description; product group/category questions use dim_product.main_group_name.
"""


class IntentRouter:
    def __init__(
        self,
        registry: Registry,
        keyword_index: KeywordIndex,
        allowlist: JoinAllowlist,
    ) -> None:
        self.registry = registry
        self.keyword_index = keyword_index
        self.allowlist = allowlist

    def route(
        self,
        question: str,
        history: list[dict[str, Any]] | None = None,
        user_context: UserContext | None = None,
        history_block: str | None = None,
    ) -> L1Result:
        keyword_hits = self.keyword_index.top_table_ids(question, top_k=2)
        catalog = self.registry.compact_catalog()
        hist = history_block or ""
        if not hist and history:
            hist = "Prior turns (use for follow-up filters and table context):\n" + json.dumps(
                history[-5:], indent=2
            )

        user = f"""Question: {question}

Keyword index top candidates: {keyword_hits}

Table catalog:
{catalog}

Allowed join patterns: {self.allowlist.pattern_ids()}
Routing hints: {l1_routing_hints(question)}
{analytics_prompt_block(question)}
{hist}{(user_context or UserContext()).prompt_block()}
"""
        raw = generate_text(L1_SYSTEM, user, json_mode=True)
        data = parse_json_response(raw)
        result = L1Result.from_dict(data)

        if result.table_id not in self.registry.tables:
            if keyword_hits:
                result.table_id = keyword_hits[0]
            result.confidence = min(result.confidence, 0.5)

        if result.table_id in self.registry.tables and not result.join_pattern:
            jp = self.allowlist.pattern_for_primary(result.table_id)
            if jp:
                result.join_pattern = jp

        result.time_range = resolve_time_range(question, result.time_range)
        return result

    def display_name(self, table_id: str) -> str:
        return self.registry.get(table_id).display_name
