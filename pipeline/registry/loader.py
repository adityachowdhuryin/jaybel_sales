"""Load schema_registry/tables/*.yaml into memory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pipeline.config import SCHEMA_REGISTRY_DIR
from pipeline.models import ColumnMeta, FewShotExample, TableMeta


def _parse_table(data: dict) -> TableMeta:
    columns = [
        ColumnMeta(
            name=c["name"],
            type=c["type"],
            description=c.get("description", ""),
            nullable=bool(c.get("nullable", True)),
            sample_values=list(c.get("sample_values") or []),
        )
        for c in data.get("columns") or []
    ]
    few_shots = [
        FewShotExample(question=ex["question"], sql=ex["sql"].strip())
        for ex in data.get("few_shot_examples") or []
    ]
    return TableMeta(
        table_id=data["table_id"],
        display_name=data["display_name"],
        layer=data.get("layer", ""),
        agent_default=bool(data.get("agent_default", True)),
        routing_priority=data.get("routing_priority", ""),
        description=data.get("description", ""),
        business_tags=list(data.get("business_tags") or []),
        grain=data.get("grain", ""),
        columns=columns,
        relationships=list(data.get("relationships") or []),
        common_filters=list(data.get("common_filters") or []),
        common_aggregations=list(data.get("common_aggregations") or []),
        time_columns=list(data.get("time_columns") or []),
        few_shot_examples=few_shots,
    )


class Registry:
    def __init__(self, tables_dir: Path | None = None) -> None:
        self._tables_dir = tables_dir or SCHEMA_REGISTRY_DIR
        self.tables: dict[str, TableMeta] = {}
        self.load()

    def load(self) -> None:
        self.tables.clear()
        for path in sorted(self._tables_dir.glob("*.yaml")):
            with path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
            table = _parse_table(data)
            self.tables[table.table_id] = table

    def get(self, table_id: str) -> TableMeta:
        if table_id not in self.tables:
            raise KeyError(f"Unknown table_id: {table_id}")
        return self.tables[table_id]

    def table_ids(self) -> list[str]:
        return list(self.tables.keys())

    def compact_catalog(self) -> str:
        lines = []
        for t in self.tables.values():
            lines.append(t.routing_summary())
        return "\n".join(lines)

    def schema_block(self, table_id: str) -> str:
        t = self.get(table_id)
        parts = [
            f"table_id: {t.table_id}",
            f"grain: {t.grain}",
            "columns:",
        ]
        for c in t.columns:
            parts.append(f"  - {c.name} ({c.type}): {c.description}")
        return "\n".join(parts)

    def schema_block_for_alias(
        self,
        table_id: str,
        alias: str,
        join_on: str = "",
    ) -> str:
        t = self.get(table_id)
        parts = [f"{alias} → {t.table_id}"]
        if join_on:
            parts.append(f"join on: {join_on}")
        parts.extend([f"grain: {t.grain}", "columns:"])
        for c in t.columns:
            parts.append(f"  - {alias}.{c.name} ({c.type}): {c.description}")
        return "\n".join(parts)

    def joined_schemas_block(
        self,
        pattern_id: str,
        allowlist: Any,
    ) -> str:
        """All dimension schemas for a join pattern (fact uses schema_block separately)."""
        from pipeline.registry.join_allowlist import JoinAllowlist

        al: JoinAllowlist = allowlist
        if pattern_id not in al.patterns:
            return ""
        pattern = al.patterns[pattern_id]
        parts: list[str] = []
        for join in pattern.get("allowed_joins") or []:
            alias = join.get("alias", "")
            table_short = join.get("table", "")
            if not table_short:
                continue
            tid = al._fq(table_short)
            parts.append(
                self.schema_block_for_alias(tid, alias, join.get("on", ""))
            )
        return "\n\n".join(parts)
