"""Run validators A, B, C in parallel."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from pipeline.models import ValidationResult
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.loader import Registry
from pipeline.validators.column_check import validate_columns
from pipeline.validators.dry_run import validate_dry_run
from pipeline.validators.safety_check import validate_safety


class ValidationOrchestrator:
    def __init__(self, registry: Registry, allowlist: JoinAllowlist) -> None:
        self.registry = registry
        self.allowlist = allowlist

    def validate_all(self, sql: str) -> list[ValidationResult]:
        tasks = {
            "A": lambda: validate_columns(sql, self.registry, self.allowlist),
            "C": lambda: validate_safety(sql, self.allowlist),
            "B": lambda: validate_dry_run(sql),
        }
        results: list[ValidationResult] = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(fn): name for name, fn in tasks.items()}
            for fut in as_completed(futures):
                results.append(fut.result())
        return results

    def all_passed(self, results: list[ValidationResult]) -> bool:
        return all(r.passed for r in results)

    def first_failure(self, results: list[ValidationResult]) -> ValidationResult | None:
        for r in results:
            if not r.passed:
                return r
        return None

    def safety_failed(self, results: list[ValidationResult]) -> bool:
        for r in results:
            if r.validator == "safety_check" and not r.passed:
                return True
        return False
