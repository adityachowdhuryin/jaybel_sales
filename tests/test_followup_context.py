"""Follow-up context (A7)."""

import unittest

from pipeline.followup_context import FollowUpContext, format_l1_history_block
from pipeline.models import L1Result


class TestFollowUpContext(unittest.TestCase):
    def test_detect_follow_up_short(self):
        hist = [
            {
                "question": "Monthly sales trend FY 2025-2026",
                "table_id": "jaybel-dev.jaybel_sales_analytics.fact_sales_report",
                "intent": "trend",
                "sql_excerpt": "SELECT month FROM fact",
            }
        ]
        ctx = FollowUpContext.from_history(hist, "Break it down by fiscal month")
        self.assertTrue(ctx.is_follow_up)
        self.assertEqual(ctx.prior_table_id, hist[0]["table_id"])

    def test_apply_inherits_table(self):
        hist = [
            {
                "question": "Trend",
                "table_id": "jaybel-dev.jaybel_sales_analytics.fact_sales_report",
            }
        ]
        ctx = FollowUpContext.from_history(hist, "Now filter that by Frazer only")
        l1 = L1Result(
            intent="filter_followup",
            table_id="jaybel-dev.jaybel_sales_analytics.fact_new_business_frazer",
            join_pattern=None,
            confidence=0.55,
            entities=[],
            time_range=None,
            plan=[],
        )
        ctx.apply_to_l1(
            l1, {"jaybel-dev.jaybel_sales_analytics.fact_sales_report"}
        )
        self.assertIn("fact_sales_report", l1.table_id)
        self.assertGreaterEqual(l1.confidence, 0.82)

    def test_history_block_includes_sql(self):
        hist = [
            {
                "question": "Q1",
                "table_id": "t1",
                "sql_excerpt": "SELECT 1",
                "row_count": 10,
            }
        ]
        ctx = FollowUpContext.from_history(hist, "filter")
        block = format_l1_history_block(hist, ctx)
        self.assertIn("sql_excerpt", block)
        self.assertIn("Q1", block)


if __name__ == "__main__":
    unittest.main()
