"""Pre-L1 scope, off-topic, vague, and rep gates (A2, A3, A5, A6)."""

from __future__ import annotations

import json
import re
from typing import Any

from pipeline.analytics_context import (
    Archetypes,
    detect_archetypes,
    detect_external_concepts,
    out_of_dataset_guidance,
)
from pipeline.clarification import vague_question_clarification
from pipeline.models import ScopeOutcome
from pipeline.query_understanding_config import (
    l0_classifier_config,
    metric_signals,
    period_signals,
    sales_keywords,
    scope_config,
)
from pipeline.user_context import UserContext, rep_gate_message, requires_rep_scope
L0_SYSTEM = """You classify whether a user question can be answered from Jaybel sales analytics in BigQuery.
Scope: revenue, GP, customers, products, sales reps, fiscal/calendar periods, Frazer new business,
working days, embroidery/custom printing staging, targets/run-rate (with disclaimers).
Return ONLY JSON: {"in_scope": bool, "reason_code": "ok"|"off_topic"|"out_of_dataset"|"vague", "confidence": 0-1}
- off_topic: not about business sales analytics
- out_of_dataset: business question but needs CRM, marketing, weather, stock prices, etc.
- vague: too short to pick metric and period (unless clearly a follow-up)
- ok: in scope
"""

_CATALOG_SCOPE = (
    "Jaybel BigQuery: fact_sales_report, fact_new_business_frazer, dimensions "
    "(date, customer, product, rep, department), staging for embroidery/working days."
)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _has_sales_signal(question: str) -> bool:
    q = question.lower()
    for kw in sales_keywords():
        if kw in q:
            return True
    return False


def _has_metric_or_period(question: str) -> bool:
    q = question.lower()
    for m in metric_signals():
        if m in q:
            return True
    for p in period_signals():
        if p in q:
            return True
    return False


def _is_vague(question: str, history: list[dict[str, Any]] | None, ctx_follow_up: bool) -> bool:
    if ctx_follow_up:
        return False
    cfg = scope_config()
    min_tokens = int(cfg.get("min_tokens", 3))
    tokens = _tokenize(question)
    if len(tokens) < min_tokens:
        return True
    if cfg.get("vague_requires_metric_or_period", True) and not _has_metric_or_period(question):
        if len(tokens) <= 4:
            return True
    return False


def _run_l0_classifier(question: str, hint: str) -> dict[str, Any]:
    from pipeline.vertex_llm import generate_text, parse_json_response

    user = f"Question: {question}\nCatalog: {_CATALOG_SCOPE}\nHeuristic hint: {hint}"
    raw = generate_text(L0_SYSTEM, user, json_mode=True, temperature=0.0)
    try:
        return parse_json_response(raw)
    except (json.JSONDecodeError, TypeError):
        return {"in_scope": True, "reason_code": "ok", "confidence": 0.5}


class ScopeGuard:
    def evaluate(
        self,
        question: str,
        user_context: UserContext | None,
        history: list[dict[str, Any]] | None,
        *,
        is_follow_up: bool = False,
    ) -> ScopeOutcome:
        ctx = user_context or UserContext()
        arch = detect_archetypes(question)

        if requires_rep_scope(question) and not ctx.sales_rep_code:
            return ScopeOutcome(
                blocked=True,
                reason_code="rep_context_required",
                message=rep_gate_message(),
                suggestions=[
                    "Open Settings in the sidebar and enter your sales rep code.",
                    "Or rephrase without “my” (e.g. total sales by rep).",
                ],
            )

        ood = out_of_dataset_guidance(question, arch)
        if ood and (arch.bi_forecast_only or detect_external_concepts(question)):
            return ScopeOutcome(
                blocked=True,
                reason_code="out_of_dataset",
                message=ood,
                suggestions=[
                    "Ask for actual sales or GP from BigQuery.",
                    "Ask for target variance using configured FY targets.",
                    "Ask for a run-rate projection with disclaimer.",
                ],
            )

        if _is_vague(question, history, is_follow_up):
            return ScopeOutcome(
                blocked=True,
                reason_code="vague",
                clarification=vague_question_clarification(),
            )

        uncertain = not _has_sales_signal(question) and not is_follow_up
        cfg = l0_classifier_config()
        if uncertain and cfg.get("enabled", True) and cfg.get("trigger") == "uncertain_only":
            l0 = _run_l0_classifier(question, "no_sales_keywords")
            reason = str(l0.get("reason_code", "ok"))
            conf = float(l0.get("confidence", 0))
            min_conf = float(cfg.get("min_confidence", 0.75))
            if not l0.get("in_scope", True) and conf >= min_conf:
                if reason == "off_topic":
                    return ScopeOutcome(
                        blocked=True,
                        reason_code="off_topic",
                        message=(
                            "I can only answer questions about Jaybel sales and analytics "
                            "from BigQuery (sales, GP, customers, products, reps, fiscal periods, "
                            "Frazer new business, working days, embroidery)."
                        ),
                        suggestions=[
                            "Try: total sales for fiscal year 2025-2026.",
                            "Try: top customers by GP last quarter.",
                        ],
                    )
                if reason == "out_of_dataset":
                    msg = out_of_dataset_guidance(question, arch) or (
                        "That metric is not available in our BigQuery sales datasets."
                    )
                    return ScopeOutcome(
                        blocked=True,
                        reason_code="out_of_dataset",
                        message=msg,
                        suggestions=[
                            "Rephrase using sales, GP, or customer dimensions.",
                        ],
                    )
                if reason == "vague":
                    return ScopeOutcome(
                        blocked=True,
                        reason_code="vague",
                        clarification=vague_question_clarification(),
                    )

        return ScopeOutcome(blocked=False)
