"""L1 + keyword fan-in and clarification triggers (A1)."""

from __future__ import annotations

from pipeline.clarification import table_clarification
from pipeline.models import L1Result, RoutingOutcome
from pipeline.query_understanding_config import routing_config
from pipeline.registry.loader import Registry


class RoutingDecision:
    def __init__(self, registry: Registry) -> None:
        self.registry = registry
        cfg = routing_config()
        self.confidence_proceed = float(cfg.get("confidence_proceed", 0.85))
        self.confidence_agree_min = float(cfg.get("confidence_agree_min", 0.70))
        self.keyword_score_min_gap = int(cfg.get("keyword_score_min_gap", 1))

    def evaluate(
        self,
        l1: L1Result,
        keyword_ranked: list[tuple[str, int]],
        question: str,
        *,
        is_follow_up: bool = False,
    ) -> RoutingOutcome:
        if is_follow_up and l1.confidence >= self.confidence_agree_min:
            return RoutingOutcome(proceed=True)

        keyword_top = keyword_ranked[0][0] if keyword_ranked else None
        keyword_second_score = (
            keyword_ranked[1][1] if len(keyword_ranked) > 1 else 0
        )
        keyword_top_score = keyword_ranked[0][1] if keyword_ranked else 0
        ambiguous_pair = (
            len(keyword_ranked) > 1
            and keyword_top_score > 0
            and (keyword_top_score - keyword_second_score) <= self.keyword_score_min_gap
        )

        agree = keyword_top is not None and keyword_top == l1.table_id
        if l1.confidence >= self.confidence_proceed:
            return RoutingOutcome(proceed=True)
        if agree and l1.confidence >= self.confidence_agree_min:
            return RoutingOutcome(proceed=True)

        disagree = keyword_top is not None and keyword_top != l1.table_id
        if l1.confidence < self.confidence_proceed and (disagree or ambiguous_pair):
            candidates: list[str] = []
            if keyword_top:
                candidates.append(keyword_top)
            if l1.table_id in self.registry.tables and l1.table_id not in candidates:
                candidates.append(l1.table_id)
            if len(keyword_ranked) > 1:
                second = keyword_ranked[1][0]
                if second not in candidates:
                    candidates.append(second)
            if not candidates and l1.table_id:
                candidates = [l1.table_id]
            clarification = table_clarification(self.registry, candidates)
            return RoutingOutcome(proceed=False, clarification=clarification)

        return RoutingOutcome(proceed=True)
