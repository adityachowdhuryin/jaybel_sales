"""Layer 2 — SQL generation."""

from __future__ import annotations

from pipeline.analytics_context import prompt_block as analytics_prompt_block
from pipeline.few_shot import select_few_shots
from pipeline.models import L1Result
from pipeline.user_context import UserContext
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.loader import Registry
from pipeline.sql_utils import strip_markdown_sql
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
    ) -> str:
        table = self.registry.get(l1.table_id)
        few_shots = select_few_shots(table, question, k=2)
        fs_block = "\n\n".join(
            f"Q: {ex.question}\nSQL:\n{ex.sql}" for ex in few_shots
        )
        join_note = ""
        if l1.join_pattern and l1.join_pattern in self.allowlist.patterns:
            p = self.allowlist.patterns[l1.join_pattern]
            join_note = f"FROM pattern: {p['from']}\nAllowed joins: {p.get('allowed_joins')}"

        user = f"""Question: {question}

Plan: {l1.plan}
Time range: {format_time_range_for_prompt(l1.time_range)}
Join pattern id: {l1.join_pattern}

Schema:
{self.registry.schema_block(l1.table_id)}

{join_note}

Examples:
{fs_block}
{analytics_prompt_block(question)}
{(user_context or UserContext()).prompt_block()}
"""
        if repair_hint:
            user += f"\n\nPrevious SQL failed validation:\n{repair_hint}\nFix only the reported issue."

        raw = generate_text(L2_SYSTEM, user, json_mode=False, temperature=0.0)
        return strip_markdown_sql(raw)
