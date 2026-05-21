"""Layer 4 — execute validated SQL."""

from __future__ import annotations

from pipeline.bq_client import execute_query
from pipeline.models import QueryResult


class BQExecutor:
    def run(self, sql: str, timeout_sec: int = 30) -> QueryResult:
        rows, columns, bytes_scanned = execute_query(sql, timeout_sec=timeout_sec)
        return QueryResult(
            rows=rows,
            columns=columns,
            row_count=len(rows),
            empty_result=len(rows) == 0,
            bytes_scanned=bytes_scanned,
        )
