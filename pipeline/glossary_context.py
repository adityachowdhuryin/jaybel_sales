"""Compact glossary slice for L2 prompts."""

from __future__ import annotations

from pipeline.column_aliases import glossary_snippet_for_l2, value_hints_snippet
from pipeline.fiscal_calendar import fiscal_calendar_prompt_block


def glossary_block_for_l2() -> str:
    """Alias map + value hints from config; kept small for token budget."""
    parts = [glossary_snippet_for_l2(), fiscal_calendar_prompt_block()]
    vh = value_hints_snippet()
    if vh and vh not in parts[0]:
        parts.append(vh)
    return "\n".join(p for p in parts if p)
