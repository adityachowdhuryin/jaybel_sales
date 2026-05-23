"""Phase D QA runner — routing and optional SQL validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from pipeline.analytics_context import detect_archetypes
from pipeline.config import PROJECT_ROOT
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.loader import Registry
from pipeline.registry.keyword_index import KeywordIndex
from pipeline.sql_generator import SQLGenerator
from pipeline.validators.orchestrator import ValidationOrchestrator

QA_PATH = PROJECT_ROOT / "docs" / "qa_evaluation_set.yaml"


@dataclass
class CaseResult:
    case_id: str
    question: str
    expected_table: str
    actual_table: str | None
    table_match: bool
    archetypes: list[str] = field(default_factory=list)
    sql_generated: bool = False
    validation_passed: bool | None = None
    error: str | None = None


def load_cases(
    *,
    case_filter: str | None = None,
    source: str | None = None,
) -> list[dict[str, Any]]:
    raw = yaml.safe_load(QA_PATH.read_text(encoding="utf-8"))
    cases = raw.get("cases") or []
    if source:
        cases = [c for c in cases if c.get("source") == source]
    if case_filter:
        if re.match(r"^Q\d{3}-Q\d{3}$", case_filter):
            lo, hi = case_filter.split("-")
            cases = [c for c in cases if lo <= c.get("id", "") <= hi]
        elif case_filter.startswith("Q"):
            ids = {x.strip() for x in case_filter.split(",")}
            cases = [c for c in cases if c.get("id") in ids]
    return cases


def _archetype_labels(question: str) -> list[str]:
    a = detect_archetypes(question)
    labels = []
    if a.target:
        labels.append("target")
    if a.run_rate:
        labels.append("run_rate")
    if a.closed_account:
        labels.append("closed_account")
    if a.embroidery:
        labels.append("embroidery")
    if a.commission:
        labels.append("commission")
    if a.bi_forecast_only:
        labels.append("bi_forecast_only")
    return labels


def run_routing_keyword_only(cases: list[dict[str, Any]]) -> list[CaseResult]:
    """Zero-cost routing: keyword index only (CI-friendly)."""
    reg = Registry()
    idx = KeywordIndex(reg.tables)
    results: list[CaseResult] = []
    for case in cases:
        q = case.get("question") or ""
        expected = case.get("expected_primary_table") or ""
        hits = idx.top_table_ids(q, top_k=1)
        actual = hits[0] if hits else None
        results.append(
            CaseResult(
                case_id=case.get("id", ""),
                question=q,
                expected_table=expected,
                actual_table=actual,
                table_match=actual == expected,
                archetypes=_archetype_labels(q),
            )
        )
    return results


def run_sql_validation(
    cases: list[dict[str, Any]],
    *,
    generate_sql: bool = False,
) -> list[CaseResult]:
    """Requires Vertex for SQL generation when generate_sql=True."""
    from pipeline.intent_router import IntentRouter

    reg = Registry()
    allowlist = JoinAllowlist()
    idx = KeywordIndex(reg.tables)
    router = IntentRouter(reg, idx, allowlist)
    sql_gen = SQLGenerator(reg, allowlist)
    validator = ValidationOrchestrator(reg, allowlist)
    results: list[CaseResult] = []

    for case in cases:
        q = case.get("question") or ""
        expected = case.get("expected_primary_table") or ""
        try:
            if generate_sql:
                l1 = router.route(q)
                sql = sql_gen.generate(q, l1)
                v = validator.validate_all(sql)
                passed = validator.all_passed(v)
                results.append(
                    CaseResult(
                        case_id=case.get("id", ""),
                        question=q,
                        expected_table=expected,
                        actual_table=l1.table_id,
                        table_match=l1.table_id == expected,
                        archetypes=_archetype_labels(q),
                        sql_generated=True,
                        validation_passed=passed,
                    )
                )
            else:
                # L1 only
                l1 = router.route(q)
                results.append(
                    CaseResult(
                        case_id=case.get("id", ""),
                        question=q,
                        expected_table=expected,
                        actual_table=l1.table_id,
                        table_match=l1.table_id == expected,
                        archetypes=_archetype_labels(q),
                    )
                )
        except Exception as exc:
            results.append(
                CaseResult(
                    case_id=case.get("id", ""),
                    question=q,
                    expected_table=expected,
                    actual_table=None,
                    table_match=False,
                    archetypes=_archetype_labels(q),
                    error=str(exc),
                )
            )
    return results


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    total = len(results)
    matched = sum(1 for r in results if r.table_match)
    return {
        "total": total,
        "table_match": matched,
        "table_match_pct": round(100 * matched / total, 1) if total else 0,
        "failures": [
            {
                "id": r.case_id,
                "expected": r.expected_table,
                "actual": r.actual_table,
                "archetypes": r.archetypes,
                "error": r.error,
            }
            for r in results
            if not r.table_match
        ],
    }
