"""Validator C — read-only safety and allowlisted tables."""

from __future__ import annotations

from pipeline.models import ValidationResult
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.sql_utils import extract_table_references, has_dml, has_from_clause


def validate_safety(sql: str, allowlist: JoinAllowlist) -> ValidationResult:
    try:
        if has_dml(sql):
            return ValidationResult(
                passed=False,
                validator="safety_check",
                message="DML/DDL statements are not allowed",
            )
        if not has_from_clause(sql):
            return ValidationResult(
                passed=False,
                validator="safety_check",
                message="SQL must include a FROM clause",
            )
        refs = extract_table_references(sql)
        if allowlist.allowed_tables_for_sql_tables(refs) is None:
            return ValidationResult(
                passed=False,
                validator="safety_check",
                message=f"Disallowed table references: {refs}",
            )
        return ValidationResult(passed=True, validator="safety_check")
    except Exception as e:
        return ValidationResult(passed=False, validator="safety_check", message=str(e))
