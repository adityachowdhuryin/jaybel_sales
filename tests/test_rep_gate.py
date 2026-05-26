"""Rep scope detection (A6)."""

import unittest

from pipeline.user_context import requires_rep_scope, rep_gate_message


class TestRepGate(unittest.TestCase):
    def test_requires_rep_my_sales(self):
        self.assertTrue(requires_rep_scope("Show my sales this month"))

    def test_requires_rep_commission(self):
        self.assertTrue(requires_rep_scope("What is my commission payout?"))

    def test_not_rep_generic(self):
        self.assertFalse(requires_rep_scope("Total sales FY 2025-2026"))

    def test_rep_gate_message_nonempty(self):
        self.assertIn("rep code", rep_gate_message().lower())


if __name__ == "__main__":
    unittest.main()
