"""SQL post-process column typo fixes."""

import re
import unittest

from pipeline.sql_utils import fix_common_column_typos


class TestSqlColumnTypos(unittest.TestCase):
    def test_fiscal_q_to_quarter(self):
        sql = "SELECT d.fiscal_q FROM `p.d.dim_date` d"
        fixed = fix_common_column_typos(sql)
        self.assertIn("fiscal_quarter", fixed)
        self.assertIsNone(re.search(r"\bfiscal_q\b", fixed))

    def test_customer_name_to_account_name(self):
        sql = (
            "SELECT c.customer_name, SUM(f.line_gp_dollar) AS total_gp "
            "FROM `p.d.fact_sales_report` f "
            "JOIN `p.d.dim_sales_customer` c ON f.customer_key = c.customer_key "
            "GROUP BY c.customer_name"
        )
        fixed = fix_common_column_typos(sql)
        self.assertNotIn("customer_name", fixed)
        self.assertEqual(fixed.count("account_name"), 2)


if __name__ == "__main__":
    unittest.main()
