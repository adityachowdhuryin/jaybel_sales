"""Validator A — column existence against registry for all referenced tables."""

from __future__ import annotations

from pipeline.column_aliases import suggested_replacements
from pipeline.models import TableMeta, ValidationResult
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.loader import Registry
from sqlglot import exp

from pipeline.sql_utils import extract_column_refs_by_alias, extract_table_references, parse_sql


def validate_columns(
    sql: str,
    registry: Registry,
    allowlist: JoinAllowlist,
) -> ValidationResult:
    try:
        refs = extract_table_references(sql)
        allowed = allowlist.allowed_tables_for_sql_tables(refs)
        if allowed is None:
            return ValidationResult(
                passed=False,
                validator="column_check",
                message=f"Table references not in join allowlist: {refs}",
            )

        alias_map = extract_column_refs_by_alias(sql)
        parsed = parse_sql(sql)
        alias_to_table: dict[str, str] = {}
        for table in parsed.find_all(exp.Table):
            alias = table.alias_or_name
            parts = [table.catalog, table.db, table.name]
            fq = ".".join(p for p in parts if p)
            if len(parts) == 3:
                alias_to_table[alias] = fq

        for alias, cols in alias_map.items():
            fq = alias_to_table.get(alias, alias)
            if fq not in registry.tables and "." not in fq:
                continue
            if fq not in registry.tables:
                for tid in registry.tables:
                    if tid.endswith("." + fq) or tid == fq:
                        fq = tid
                        break
            try:
                meta: TableMeta = registry.get(fq)
            except KeyError:
                return ValidationResult(
                    passed=False,
                    validator="column_check",
                    message=f"Unknown table alias {alias} -> {fq}",
                )
            valid = meta.column_names()
            bad = [c for c in cols if c not in valid and c != "*"]
            if bad:
                valid_sample = sorted(valid)[:25]
                repl = suggested_replacements(fq, bad)
                return ValidationResult(
                    passed=False,
                    validator="column_check",
                    message=f"Invalid columns on {fq}: {bad}. Valid: {valid_sample}...",
                    details={
                        "table_id": fq,
                        "alias": alias,
                        "bad_columns": bad,
                        "valid_columns_sample": valid_sample,
                        "suggested_replacements": repl,
                    },
                )
        return ValidationResult(passed=True, validator="column_check")
    except Exception as e:
        return ValidationResult(passed=False, validator="column_check", message=str(e))
