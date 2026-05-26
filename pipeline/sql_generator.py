"""Layer 2 — SQL generation."""

from __future__ import annotations

from pipeline.analytics_context import prompt_block as analytics_prompt_block
from pipeline.few_shot import select_few_shots
from pipeline.followup_context import FollowUpContext
from pipeline.followup_sql_context import format_l2_followup_block
from pipeline.fiscal_metadata_sql import try_deterministic_fy_sql
from pipeline.glossary_context import glossary_block_for_l2
from pipeline.models import L1Result
from pipeline.schema_context import build_l2_schema_block
from pipeline.sql_generation_config import few_shot_config
from pipeline.user_context import UserContext
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.loader import Registry
from pipeline.sql_utils import fix_common_column_typos, strip_markdown_sql
from pipeline.time_range import format_time_range_for_prompt
from pipeline.vertex_llm import generate_text

L2_SYSTEM = """You are a BigQuery Standard SQL expert for Jaybel.
Hard rules:
- Use ONLY columns listed in the schema.
- Use ONLY table ids exactly as given.
- BigQuery Standard SQL only.
- Never SELECT *; list columns explicitly.
- LIMIT 1000 unless user needs fewer rows.
- Apply the provided time range exactly.
- FY target amounts in the analytics context block are literals — do not SELECT from a target table.
- stg_total_working_days may appear only in scalar subqueries when joined with fact_sales_report pattern.
- Return SQL only, no markdown or explanation.
- dim_date: use fiscal_quarter (not fiscal_q), fiscal_month_name or fiscal_month_no (not fiscal_m).
- dim_sales_customer: customer display name is account_name (not customer_name); account is the account code.
- fact_sales_report territory filter: use territory_code (values like JAY, FRA, NSW — not region labels like APAC unless in data).
- Top-N per group: use RANK() or ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) when user asks "top N ... for each".
- Follow-ups: keep the same metric (GP vs sales) unless the user explicitly changes it.
- Jaybel fiscal year runs July–June (fiscal_month_no 1–12 on dim_date). For current/last/latest FY use fy label from Time range block only — never ORDER BY fy DESC or MAX(fy) for relative phrases.
"""


class SQLGenerator:
    def __init__(self, registry: Registry, allowlist: JoinAllowlist) -> None:
        self.registry = registry
        self.allowlist = allowlist

    def generate(
        self,
        question: str,
        l1: L1Result,
        repair_hint: str | None = None,
        user_context: UserContext | None = None,
        followup_ctx: FollowUpContext | None = None,
    ) -> str:
        if not repair_hint:
            det = try_deterministic_fy_sql(question, l1)
            if det:
                return det

        table = self.registry.get(l1.table_id)
        fs_cfg = few_shot_config()
        k = int(fs_cfg.get("default_k", 3))
        few_shots = select_few_shots(
            table,
            question,
            k=k,
            join_pattern=l1.join_pattern,
        )
        fs_block = "\n\n".join(
            f"Q: {ex.question}\nSQL:\n{ex.sql}" for ex in few_shots
        )
        join_note = ""
        if l1.join_pattern and l1.join_pattern in self.allowlist.patterns:
            p = self.allowlist.patterns[l1.join_pattern]
            join_note = f"FROM pattern: {p['from']}\nAllowed joins: {p.get('allowed_joins')}"

        schema_block = build_l2_schema_block(
            self.registry, self.allowlist, l1, question
        )
        glossary = glossary_block_for_l2()
        followup_block = format_l2_followup_block(followup_ctx) if followup_ctx else ""

        user = f"""Question: {question}

Plan: {l1.plan}
Time range: {format_time_range_for_prompt(l1.time_range)}
Join pattern id: {l1.join_pattern}

Schema (fact + joined dimensions):
{schema_block}

{join_note}

Glossary:
{glossary}

{followup_block}

Examples:
{fs_block}
{analytics_prompt_block(question)}
{(user_context or UserContext()).prompt_block()}
"""
        if repair_hint:
            user += f"\n\nPrevious SQL failed validation:\n{repair_hint}\nFix only the reported issue."

        raw = generate_text(L2_SYSTEM, user, json_mode=False, temperature=0.0)
        return fix_common_column_typos(strip_markdown_sql(raw), l1.table_id)
