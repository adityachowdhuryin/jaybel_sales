"""Deterministic clarification copy for routing and vague questions."""

from __future__ import annotations

from pipeline.models import ClarificationOption, ClarificationPayload
from pipeline.registry.loader import Registry


def table_clarification(
    registry: Registry,
    table_ids: list[str],
    *,
    message: str | None = None,
) -> ClarificationPayload:
    options: list[ClarificationOption] = []
    for i, tid in enumerate(table_ids[:3]):
        try:
            display = registry.get(tid).display_name
        except KeyError:
            display = tid.split(".")[-1]
        short = tid.split(".")[-1]
        options.append(
            ClarificationOption(
                id=f"table_{i}",
                label=display,
                send_text=f"Use {display} ({short}) for this question.",
            )
        )
    return ClarificationPayload(
        code="ambiguous_table",
        message=message
        or "More than one dataset could answer this. Which should I use?",
        options=options,
    )


def vague_question_clarification() -> ClarificationPayload:
    return ClarificationPayload(
        code="vague_question",
        message=(
            "I need a bit more detail to query Jaybel sales data. "
            "What metric, time period, and scope should I use?"
        ),
        options=[
            ClarificationOption(
                id="metric_sales",
                label="Total sales for a fiscal year",
                send_text="Show total sales for fiscal year 2025-2026.",
            ),
            ClarificationOption(
                id="metric_gp",
                label="GP by category",
                send_text="Show gross profit by product category for fiscal year 2025-2026.",
            ),
            ClarificationOption(
                id="metric_trend",
                label="Monthly trend",
                send_text="Show monthly sales trend for fiscal year 2025-2026.",
            ),
        ],
    )
