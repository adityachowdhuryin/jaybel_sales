"""Validator B — BigQuery dry run."""

from __future__ import annotations

from pipeline.bq_client import dry_run
from pipeline.models import ValidationResult


def validate_dry_run(sql: str) -> ValidationResult:
    ok, msg, bytes_scanned = dry_run(sql)
    return ValidationResult(
        passed=ok,
        validator="dry_run",
        message=msg,
        bytes_scanned=bytes_scanned,
    )
