"""Routing fan-in and clarification (A1)."""

from __future__ import annotations

import unittest

from pipeline.models import L1Result, TimeRange
from pipeline.registry.loader import Registry
from pipeline.routing_decision import RoutingDecision


def _l1(table_id: str, confidence: float) -> L1Result:
    return L1Result(
        intent="aggregation",
        table_id=table_id,
        join_pattern="fact_sales_with_dims",
        confidence=confidence,
        entities=[],
        time_range=TimeRange("2025-07-01", "2026-06-30", "FY 2025-2026"),
        plan=["step"],
    )


class TestRoutingDecision(unittest.TestCase):
    def test_proceed_high_confidence(self):
        reg = Registry()
        rd = RoutingDecision(reg)
        l1 = _l1("jaybel-dev.jaybel_sales_analytics.fact_sales_report", 0.9)
        out = rd.evaluate(
            l1, [("jaybel-dev.jaybel_sales_analytics.fact_sales_report", 5)], "sales"
        )
        self.assertTrue(out.proceed)
        self.assertIsNone(out.clarification)

    def test_clarify_on_disagreement(self):
        reg = Registry()
        rd = RoutingDecision(reg)
        fact = "jaybel-dev.jaybel_sales_analytics.fact_sales_report"
        frazer = "jaybel-dev.jaybel_sales_analytics.fact_new_business_frazer"
        l1 = _l1(frazer, 0.6)
        ranked = [(fact, 4), (frazer, 3)]
        out = rd.evaluate(l1, ranked, "performance last month")
        self.assertFalse(out.proceed)
        self.assertIsNotNone(out.clarification)
        self.assertGreaterEqual(len(out.clarification.options), 2)

    def test_follow_up_proceeds_with_moderate_confidence(self):
        reg = Registry()
        rd = RoutingDecision(reg)
        fact = "jaybel-dev.jaybel_sales_analytics.fact_sales_report"
        l1 = _l1(fact, 0.75)
        out = rd.evaluate(
            l1,
            [(fact, 2)],
            "Break it down by fiscal month",
            is_follow_up=True,
        )
        self.assertTrue(out.proceed)


if __name__ == "__main__":
    unittest.main()
