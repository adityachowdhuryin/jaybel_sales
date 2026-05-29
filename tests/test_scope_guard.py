"""Scope guard heuristics (A2, A3, A5, A6)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from pipeline.scope_guard import ScopeGuard
from pipeline.user_context import UserContext


class TestScopeGuard(unittest.TestCase):
    def test_my_sales_not_gated_without_code(self):
        guard = ScopeGuard()
        out = guard.evaluate("What are my sales this month?", UserContext(), None)
        self.assertNotEqual(out.reason_code, "rep_context_required")

    def test_commission_gated_without_code(self):
        guard = ScopeGuard()
        out = guard.evaluate(
            "What is my commission payout this quarter?",
            UserContext(),
            None,
        )
        self.assertTrue(out.blocked)
        self.assertEqual(out.reason_code, "rep_context_required")

    def test_rep_ok_with_code(self):
        guard = ScopeGuard()
        out = guard.evaluate(
            "What is my commission payout this quarter?",
            UserContext(sales_rep_code="REP01"),
            None,
        )
        self.assertNotEqual(out.reason_code, "rep_context_required")

    def test_vague_question_blocked(self):
        guard = ScopeGuard()
        out = guard.evaluate("help", UserContext(), None)
        self.assertTrue(out.blocked)
        self.assertEqual(out.reason_code, "vague")
        self.assertIsNotNone(out.clarification)

    def test_sales_question_not_vague(self):
        guard = ScopeGuard()
        out = guard.evaluate(
            "Total sales for fiscal year 2025-2026",
            UserContext(),
            None,
        )
        self.assertNotEqual(out.reason_code, "vague")

    def test_external_concept_out_of_dataset(self):
        guard = ScopeGuard()
        out = guard.evaluate("What is the weather in Sydney?", UserContext(), None)
        self.assertTrue(out.blocked)
        self.assertEqual(out.reason_code, "out_of_dataset")

    @patch("pipeline.scope_guard._run_l0_classifier")
    def test_l0_off_topic(self, mock_l0):
        mock_l0.return_value = {
            "in_scope": False,
            "reason_code": "off_topic",
            "confidence": 0.95,
        }
        guard = ScopeGuard()
        out = guard.evaluate("Who won the World Cup?", UserContext(), None)
        self.assertTrue(out.blocked)
        self.assertEqual(out.reason_code, "off_topic")


if __name__ == "__main__":
    unittest.main()
