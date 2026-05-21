"""SQL parsing helpers (sqlglot, BigQuery dialect)."""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

DML_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
)


def parse_sql(sql: str) -> exp.Expression:
    return sqlglot.parse_one(sql, read="bigquery")


def strip_markdown_sql(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def extract_table_references(sql: str) -> set[str]:
    """Fully-qualified table IDs from FROM/JOIN."""
    parsed = parse_sql(sql)
    refs: set[str] = set()
    for table in parsed.find_all(exp.Table):
        parts = []
        if table.catalog:
            parts.append(table.catalog)
        if table.db:
            parts.append(table.db)
        if table.name:
            parts.append(table.name)
        if len(parts) == 3:
            refs.add(".".join(parts))
        elif table.name:
            refs.add(table.name)
    return refs


def extract_column_refs_by_alias(sql: str) -> dict[str, set[str]]:
    """Map alias -> column names used (unqualified columns attributed to single-table)."""
    parsed = parse_sql(sql)
    alias_to_table: dict[str, str] = {}
    for table in parsed.find_all(exp.Table):
        alias = table.alias_or_name
        parts = [table.catalog, table.db, table.name]
        fq = ".".join(p for p in parts if p)
        alias_to_table[alias] = fq

    refs: dict[str, set[str]] = {a: set() for a in alias_to_table}
    for col in parsed.find_all(exp.Column):
        col_name = col.name
        if not col_name:
            continue
        if col.table:
            alias = col.table
            refs.setdefault(alias, set()).add(col_name)
        else:
            if len(alias_to_table) == 1:
                only = next(iter(alias_to_table))
                refs.setdefault(only, set()).add(col_name)
    return refs


def has_dml(sql: str) -> bool:
    parsed = parse_sql(sql)
    return any(parsed.find(t) for t in DML_TYPES)


def has_from_clause(sql: str) -> bool:
    parsed = parse_sql(sql)
    return parsed.find(exp.From) is not None
