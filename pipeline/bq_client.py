"""BigQuery client singleton and dry-run / execute."""

from __future__ import annotations

from typing import Any

from google.cloud import bigquery

from pipeline.config import bytes_scanned_limit_gb, gcp_project_id, query_row_limit

_client: bigquery.Client | None = None


def get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=gcp_project_id())
    return _client


def dry_run(sql: str) -> tuple[bool, str, int | None]:
    client = get_client()
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    try:
        job = client.query(sql, job_config=job_config)
        bytes_scanned = job.total_bytes_processed
        limit = int(bytes_scanned_limit_gb() * 1e9)
        if bytes_scanned and bytes_scanned > limit:
            return True, f"Query would scan {bytes_scanned} bytes (over soft limit)", bytes_scanned
        return True, "", bytes_scanned
    except Exception as e:
        return False, str(e), None


def execute_query(sql: str, timeout_sec: int = 30) -> tuple[list[dict[str, Any]], list[str], int | None]:
    client = get_client()
    job_config = bigquery.QueryJobConfig(use_query_cache=True)
    job = client.query(sql, job_config=job_config)
    result = job.result(timeout=timeout_sec)
    rows = [dict(row.items()) for row in result]
    columns = [field.name for field in result.schema]
    bytes_scanned = job.total_bytes_processed
    return rows, columns, bytes_scanned
