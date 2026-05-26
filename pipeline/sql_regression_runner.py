"""Batch SQL regression — L2 + repair + validators without BigQuery execute."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from pipeline.config import PROJECT_ROOT
from pipeline.followup_context import FollowUpContext
from pipeline.intent_router import IntentRouter
from pipeline.models import ValidationResult
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.keyword_index import KeywordIndex
from pipeline.registry.loader import Registry
from pipeline.routing_decision import RoutingDecision
from pipeline.scope_guard import ScopeGuard
from pipeline.user_context import UserContext

QA_PATH = PROJECT_ROOT / "docs" / "qa_evaluation_set.yaml"


@dataclass
class SqlRegressionResult:
    case_id: str
    question: str
    expected_table: str
    actual_table: str | None
    table_match: bool
    validation_passed: bool
    sql: str | None = None
    error: str | None = None
    validators: list[str] = field(default_factory=list)


def load_sql_regression_cases(
    *,
    case_filter: str | None = None,
    source: str | None = None,
) -> list[dict[str, Any]]:
    raw = yaml.safe_load(QA_PATH.read_text(encoding="utf-8"))
    cases = [
        c
        for c in (raw.get("cases") or [])
        if c.get("source") == "sql_hardening_regression"
    ]
    if source and source != "sql_hardening_regression":
        cases = [c for c in cases if c.get("source") == source]
    if case_filter:
        if re.match(r"^S\d{3}-S\d{3}$", case_filter):
            lo, hi = case_filter.split("-")
            cases = [c for c in cases if lo <= c.get("id", "") <= hi]
        elif case_filter.startswith("S"):
            ids = {x.strip() for x in case_filter.split(",")}
            cases = [c for c in cases if c.get("id") in ids]
    return cases


def run_sql_offline(
    cases: list[dict[str, Any]],
    *,
    skip_guards: bool = False,
) -> list[SqlRegressionResult]:
    """L2 + hybrid repair + validators (Vertex for L2; no BQ execute)."""
    from pipeline.pipeline import Pipeline

    reg = Registry()
    allowlist = JoinAllowlist()
    idx = KeywordIndex(reg.tables)
    router = IntentRouter(reg, idx, allowlist)
    routing_decision = RoutingDecision(reg)
    scope_guard = ScopeGuard()
    pipe = Pipeline(reg)
    results: list[SqlRegressionResult] = []

    for case in cases:
        q = case.get("question") or ""
        expected = case.get("expected_primary_table") or ""
        history = case.get("history")
        ctx = UserContext(sales_rep_code=case.get("sales_rep_code") or None)
        try:
            if not skip_guards:
                scope = scope_guard.evaluate(
                    q, ctx, history, is_follow_up=bool(history)
                )
                if scope.blocked:
                    results.append(
                        SqlRegressionResult(
                            case_id=case.get("id", ""),
                            question=q,
                            expected_table=expected,
                            actual_table=None,
                            table_match=False,
                            validation_passed=False,
                            error=f"scope_blocked:{scope.reason_code}",
                        )
                    )
                    continue

            followup_ctx = FollowUpContext.from_history(history, q)
            hist_block = ""
            l1 = router.route(
                q,
                history=history,
                user_context=ctx,
                history_block=hist_block,
            )
            followup_ctx.apply_to_l1(l1, set(reg.tables.keys()))
            keyword_ranked = idx.lookup(q, top_k=3)
            routing = routing_decision.evaluate(
                l1,
                keyword_ranked,
                q,
                is_follow_up=followup_ctx.is_follow_up,
            )
            if not routing.proceed:
                results.append(
                    SqlRegressionResult(
                        case_id=case.get("id", ""),
                        question=q,
                        expected_table=expected,
                        actual_table=l1.table_id,
                        table_match=l1.table_id == expected,
                        validation_passed=False,
                        error="routing_clarification",
                    )
                )
                continue

            sql, validation, fail = pipe._generate_validated_sql(
                q, l1, ctx, followup_ctx
            )
            passed = sql is not None and all(v.passed for v in validation)
            results.append(
                SqlRegressionResult(
                    case_id=case.get("id", ""),
                    question=q,
                    expected_table=expected,
                    actual_table=l1.table_id,
                    table_match=l1.table_id == expected,
                    validation_passed=passed,
                    sql=sql,
                    error=fail.message if fail and not passed else None,
                    validators=[v.validator for v in validation if not v.passed],
                )
            )
        except Exception as exc:
            results.append(
                SqlRegressionResult(
                    case_id=case.get("id", ""),
                    question=q,
                    expected_table=expected,
                    actual_table=None,
                    table_match=False,
                    validation_passed=False,
                    error=str(exc),
                )
            )
    return results


def run_sql_e2e(cases: list[dict[str, Any]]) -> list[SqlRegressionResult]:
    """Full pipeline including BigQuery execute (integration)."""
    from pipeline.pipeline import Pipeline

    pipe = Pipeline()
    results: list[SqlRegressionResult] = []
    for case in cases:
        q = case.get("question") or ""
        expected = case.get("expected_primary_table") or ""
        try:
            result = pipe.run(
                q,
                history=case.get("history"),
                user_context=UserContext(
                    sales_rep_code=case.get("sales_rep_code") or None
                ),
            )
            passed = result.sql is not None and result.stop_reason.value in (
                "none",
                "guidance",
            )
            validation_passed = result.sql is not None and not result.validation_detail
            results.append(
                SqlRegressionResult(
                    case_id=case.get("id", ""),
                    question=q,
                    expected_table=expected,
                    actual_table=result.l1.table_id if result.l1 else None,
                    table_match=(result.l1.table_id if result.l1 else None) == expected,
                    validation_passed=validation_passed and passed,
                    sql=result.sql,
                    error=result.validation_detail,
                )
            )
        except Exception as exc:
            results.append(
                SqlRegressionResult(
                    case_id=case.get("id", ""),
                    question=q,
                    expected_table=expected,
                    actual_table=None,
                    table_match=False,
                    validation_passed=False,
                    error=str(exc),
                )
            )
    return results


def summarize_sql_regression(results: list[SqlRegressionResult]) -> dict[str, Any]:
    total = len(results)
    table_ok = sum(1 for r in results if r.table_match)
    val_ok = sum(1 for r in results if r.validation_passed)
    return {
        "total": total,
        "table_match": table_ok,
        "validation_passed": val_ok,
        "table_match_pct": round(100 * table_ok / total, 1) if total else 0,
        "validation_pass_pct": round(100 * val_ok / total, 1) if total else 0,
        "failures": [
            {
                "id": r.case_id,
                "expected": r.expected_table,
                "actual": r.actual_table,
                "validation_passed": r.validation_passed,
                "error": r.error,
                "validators": r.validators,
            }
            for r in results
            if not r.validation_passed or not r.table_match
        ],
    }
