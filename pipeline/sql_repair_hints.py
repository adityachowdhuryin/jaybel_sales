"""Structured repair hints for L2 LLM retries."""

from __future__ import annotations

from pipeline.models import ValidationResult


def structured_repair_hint(fail: ValidationResult) -> str:
    if fail.validator == "column_check":
        details = fail.details or {}
        bad = details.get("bad_columns") or []
        repl = details.get("suggested_replacements") or {}
        valid = details.get("valid_columns_sample") or []
        table = details.get("table_id") or "unknown table"
        lines = [
            f"column_check failed on {table}.",
            f"Invalid columns: {bad}",
        ]
        if repl:
            lines.append("Use these replacements:")
            for src, dst in repl.items():
                lines.append(f"  - {src} → {dst}")
        if valid:
            lines.append(f"Valid columns (sample): {valid[:25]}")
        lines.append("Fix ONLY the reported column issues. Keep filters and metric unchanged.")
        return "\n".join(lines)
    return f"{fail.validator}: {fail.message}"


def friendly_validation_message(fail: ValidationResult) -> tuple[str, list[str]]:
    if fail.validator == "column_check":
        return (
            "Couldn't build a valid query — one or more column names don't match the schema.",
            [
                "Try rephrasing using terms from the business glossary (e.g. account name, fiscal quarter).",
                "For territories use territory_code values like JAY or FRA, not APAC.",
                "Check the fiscal year and quarter in your question.",
            ],
        )
    if fail.validator == "safety_check":
        return (
            "This query couldn't be run safely (only approved read-only joins are allowed).",
            ["Try a simpler question on sales or GP for a fiscal period."],
        )
    if fail.validator == "dry_run":
        return (
            "BigQuery rejected the generated SQL.",
            ["Try narrowing the date range or simplifying filters."],
        )
    return (
        "The query could not be validated.",
        ["Rephrase your question with a clear metric and time period."],
    )
