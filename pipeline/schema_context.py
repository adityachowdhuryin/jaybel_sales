"""Join-aware schema blocks for L2 SQL generation."""

from __future__ import annotations

from pipeline.models import L1Result
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.loader import Registry
from pipeline.sql_generation_config import schema_context_config


def build_l2_schema_block(
    registry: Registry,
    allowlist: JoinAllowlist,
    l1: L1Result,
    question: str = "",
) -> str:
    """Fact schema + all dimension columns from the join pattern."""
    max_chars = int(schema_context_config().get("max_chars", 12000))
    parts: list[str] = [registry.schema_block(l1.table_id)]

    if l1.join_pattern and l1.join_pattern in allowlist.patterns:
        pattern = allowlist.patterns[l1.join_pattern]
        for join in pattern.get("allowed_joins") or []:
            alias = join.get("alias", "")
            table_short = join.get("table", "")
            if not table_short:
                continue
            tid = allowlist._fq(table_short)
            if tid == l1.table_id:
                continue
            parts.append(registry.schema_block_for_alias(tid, alias, join.get("on", "")))

    body = "\n\n".join(parts)
    if len(body) <= max_chars:
        return body
    return body[: max_chars - 20] + "\n... (truncated)"
