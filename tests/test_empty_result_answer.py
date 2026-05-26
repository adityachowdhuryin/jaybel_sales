"""Empty result markdown (A4)."""

import unittest

from pipeline.empty_result_answer import (
    build_empty_result_markdown,
    empty_result_guidance_suggestions,
)
from pipeline.models import L1Result, QueryResult, TimeRange


class TestEmptyResultAnswer(unittest.TestCase):
    def test_empty_markdown_sections(self):
        l1 = L1Result(
            intent="aggregation",
            table_id="jaybel-dev.jaybel_sales_analytics.fact_sales_report",
            join_pattern=None,
            confidence=0.9,
            entities=["Frazer"],
            time_range=TimeRange("2025-07-01", "2026-06-30", "FY 2025-2026"),
            plan=[],
        )
        qr = QueryResult(rows=[], columns=[], row_count=0, empty_result=True)
        md = build_empty_result_markdown(
            "Sales for Frazer only",
            l1,
            "SELECT 1",
            qr,
            "Sales Report",
        )
        self.assertIn("## Summary", md)
        self.assertIn("No rows", md)
        self.assertIn("## Suggestions", md)

    def test_empty_guidance_suggestions(self):
        l1 = L1Result(
            intent="aggregation",
            table_id="t",
            join_pattern=None,
            confidence=0.9,
            entities=["X"],
            time_range=None,
            plan=[],
        )
        s = empty_result_guidance_suggestions(l1)
        self.assertGreaterEqual(len(s), 1)


if __name__ == "__main__":
    unittest.main()
