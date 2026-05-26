"""Guard QA runner — scope checks only (no Vertex/sqlglot)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from pipeline.config import PROJECT_ROOT
from pipeline.scope_guard import ScopeGuard
from pipeline.user_context import UserContext

QA_PATH = PROJECT_ROOT / "docs" / "qa_evaluation_set.yaml"


@dataclass
class GuardCaseResult:
    case_id: str
    question: str
    expected_stop_reason: str
    actual_reason: str | None
    match: bool
    error: str | None = None


def load_guard_cases(
    *,
    case_filter: str | None = None,
    source: str | None = None,
) -> list[dict[str, Any]]:
    raw = yaml.safe_load(QA_PATH.read_text(encoding="utf-8"))
    cases = [c for c in (raw.get("cases") or []) if c.get("expected_stop_reason")]
    if source:
        cases = [c for c in cases if c.get("source") == source]
    if case_filter and case_filter.startswith("G"):
        if "-" in case_filter:
            lo, hi = case_filter.split("-")
            cases = [c for c in cases if lo <= c.get("id", "") <= hi]
        else:
            ids = {x.strip() for x in case_filter.split(",")}
            cases = [c for c in cases if c.get("id") in ids]
    return cases


def run_guard_checks(cases: list[dict[str, Any]]) -> list[GuardCaseResult]:
    guard = ScopeGuard()
    out: list[GuardCaseResult] = []
    for case in cases:
        q = case.get("question") or ""
        expected = case.get("expected_stop_reason") or ""
        rep = case.get("sales_rep_code")
        ctx = UserContext(sales_rep_code=rep) if rep else UserContext()
        try:
            scope = guard.evaluate(q, ctx, case.get("history"))
            if not scope.blocked:
                actual = "ok"
            elif scope.reason_code:
                actual = scope.reason_code
            elif scope.clarification:
                actual = scope.clarification.code
            else:
                actual = "blocked"
            match = actual == expected
            out.append(
                GuardCaseResult(
                    case_id=case.get("id", ""),
                    question=q,
                    expected_stop_reason=expected,
                    actual_reason=actual,
                    match=match,
                )
            )
        except Exception as exc:
            out.append(
                GuardCaseResult(
                    case_id=case.get("id", ""),
                    question=q,
                    expected_stop_reason=expected,
                    actual_reason=None,
                    match=False,
                    error=str(exc),
                )
            )
    return out


def summarize_guard(results: list[GuardCaseResult]) -> dict[str, Any]:
    total = len(results)
    matched = sum(1 for r in results if r.match)
    return {
        "total": total,
        "guard_match": matched,
        "guard_match_pct": round(100 * matched / total, 1) if total else 0,
        "failures": [
            {
                "id": r.case_id,
                "expected": r.expected_stop_reason,
                "actual": r.actual_reason,
                "error": r.error,
            }
            for r in results
            if not r.match
        ],
    }
