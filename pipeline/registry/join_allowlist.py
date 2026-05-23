"""Load and validate SQL against approved join patterns."""

from __future__ import annotations

from pathlib import Path

import yaml

from pipeline.config import JOIN_ALLOWLIST_PATH, bq_dataset, gcp_project_id, load_config


class JoinAllowlist:
    def __init__(self, path: Path | None = None) -> None:
        with (path or JOIN_ALLOWLIST_PATH).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.dataset = data["dataset"]
        self.patterns = {p["id"]: p for p in data["query_patterns"]}
        self.single_table_allowed = bool(data.get("single_table_queries", True))
        self.auxiliary_scalar_tables: set[str] = set()
        for short in data.get("auxiliary_scalar_tables") or []:
            self.auxiliary_scalar_tables.add(self._fq(short))
        cfg = load_config()
        self._all_table_ids: set[str] = set()
        for key in ("primary_fact_tables", "dimension_tables", "staging_tables"):
            self._all_table_ids.update(cfg["agent_routing"].get(key, []))

    def pattern_ids(self) -> list[str]:
        return list(self.patterns.keys())

    def _fq(self, table_short: str) -> str:
        return f"{gcp_project_id()}.{bq_dataset()}.{table_short}"

    def allowed_tables_for_pattern(self, pattern_id: str) -> set[str]:
        p = self.patterns[pattern_id]
        tables = {self._fq(p["primary_table"])}
        for j in p.get("allowed_joins") or []:
            tables.add(self._fq(j["table"]))
        return tables

    def allowed_tables_for_sql_tables(self, referenced: set[str]) -> set[str] | None:
        """Return allowlist if references match a pattern; None if single-table ok."""
        if len(referenced) == 1 and self.single_table_allowed:
            tid = next(iter(referenced))
            if tid in self._all_table_ids:
                return referenced
        for pattern_id, p in self.patterns.items():
            allowed = self.allowed_tables_for_pattern(pattern_id)
            primary = self._fq(p["primary_table"])
            if referenced <= allowed and referenced:
                if primary in referenced:
                    return allowed
            # Fact + dims + auxiliary scalar tables (e.g. stg_total_working_days subquery)
            if self.auxiliary_scalar_tables and primary in referenced:
                extra = referenced - allowed
                if extra and extra <= self.auxiliary_scalar_tables:
                    return allowed | extra
        return None

    def pattern_for_primary(self, table_id: str) -> str | None:
        short = table_id.split(".")[-1]
        for pid, p in self.patterns.items():
            if p["primary_table"] == short:
                return pid
        return None
