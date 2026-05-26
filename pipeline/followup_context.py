"""Follow-up detection and L1 context inheritance (A7)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pipeline.models import L1Result
from pipeline.query_understanding_config import follow_up_config
from pipeline.followup_sql_context import extract_filter_summary, extract_metric_from_sql


@dataclass
class FollowUpContext:
    is_follow_up: bool = False
    prior_table_id: str | None = None
    prior_intent: str | None = None
    prior_time_range_label: str | None = None
    prior_sql_excerpt: str | None = None
    prior_question: str | None = None
    prior_row_count: int | None = None
    prior_join_pattern: str | None = None
    prior_metric: str | None = None
    prior_filters: str | None = None

    @classmethod
    def from_history(
        cls,
        history: list[dict[str, Any]] | None,
        question: str,
    ) -> FollowUpContext:
        ctx = cls()
        if not history:
            return ctx
        last = history[-1]
        ctx.prior_table_id = last.get("table_id")
        ctx.prior_intent = last.get("intent")
        ctx.prior_time_range_label = last.get("time_range_label")
        ctx.prior_sql_excerpt = (last.get("sql_excerpt") or "")[:500] or None
        ctx.prior_question = last.get("question")
        ctx.prior_join_pattern = last.get("join_pattern")
        ctx.prior_metric = last.get("metric_hint") or extract_metric_from_sql(
            last.get("sql_excerpt")
        )
        ctx.prior_filters = last.get("filter_summary") or extract_filter_summary(
            last.get("sql_excerpt")
        )
        rc = last.get("row_count")
        ctx.prior_row_count = int(rc) if rc is not None else None

        cfg = follow_up_config()
        phrases = [p.lower() for p in (cfg.get("follow_up_phrases") or [])]
        q = question.lower().strip()
        token_count = len(re.findall(r"[a-z0-9]+", q))
        phrase_hit = any(p in q for p in phrases)
        short = token_count <= 8
        has_prior = bool(ctx.prior_table_id or ctx.prior_sql_excerpt)
        ctx.is_follow_up = has_prior and (phrase_hit or short)
        return ctx

    def apply_to_l1(self, l1: L1Result, registry_table_ids: set[str]) -> None:
        if not self.is_follow_up or not self.prior_table_id:
            return
        if self.prior_table_id not in registry_table_ids:
            return
        cfg = follow_up_config()
        inherit_min = float(cfg.get("inherit_table_min_confidence", 0.70))
        boost = float(cfg.get("inherit_boost_confidence", 0.82))
        if l1.confidence < inherit_min or l1.table_id != self.prior_table_id:
            l1.table_id = self.prior_table_id
            l1.confidence = max(l1.confidence, boost)
            note = (
                f"Inherit prior table {self.prior_table_id} for follow-up; "
                "keep filters unless user changes metric or period."
            )
            if l1.plan:
                l1.plan = [note] + l1.plan[:4]
            else:
                l1.plan = [note]


def format_l1_history_block(
    history: list[dict[str, Any]] | None,
    ctx: FollowUpContext,
) -> str:
    if not history:
        return ""
    lines = ["Prior turns (use for follow-up filters and table context):"]
    for turn in history[-5:]:
        parts = [
            f"Q: {turn.get('question', '')}",
            f"table_id={turn.get('table_id')}",
            f"intent={turn.get('intent')}",
        ]
        if turn.get("time_range_label"):
            parts.append(f"time_range={turn['time_range_label']}")
        if turn.get("sql_excerpt"):
            parts.append(f"sql_excerpt={turn['sql_excerpt'][:300]}")
        if turn.get("metric_hint"):
            parts.append(f"metric={turn['metric_hint']}")
        if turn.get("filter_summary"):
            parts.append(f"filters={turn['filter_summary'][:200]}")
        if turn.get("join_pattern"):
            parts.append(f"join_pattern={turn['join_pattern']}")
        if turn.get("row_count") is not None:
            parts.append(f"row_count={turn['row_count']}")
        lines.append(" | ".join(str(p) for p in parts if p))
    if ctx.is_follow_up and ctx.prior_table_id:
        lines.append(
            f"\nActive follow-up: inherit table_id={ctx.prior_table_id} "
            f"from prior question unless user explicitly changes dataset or metric."
        )
    return "\n".join(lines) + "\n"
