"""Golden SQL for v1.2 patterns passes validators."""

from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.loader import Registry
from pipeline.validators.safety_check import validate_safety

RUN_RATE_SQL = """
SELECT mtd.mtd_sales,
  (SELECT CAST(Completed_days AS INT64) FROM `jaybel-dev.jaybel_sales_analytics.stg_total_working_days`
    WHERE fiscal_year = '2025-2026' AND month = 'Current' LIMIT 1) AS completed_days,
  SAFE_DIVIDE(mtd.mtd_sales, (SELECT CAST(Completed_days AS INT64) FROM `jaybel-dev.jaybel_sales_analytics.stg_total_working_days`
    WHERE fiscal_year = '2025-2026' AND month = 'Current' LIMIT 1))
    * (SELECT CAST(total_working_days AS INT64) FROM `jaybel-dev.jaybel_sales_analytics.stg_total_working_days`
    WHERE fiscal_year = '2025-2026' AND month = 'Current' LIMIT 1) AS projected_month_sales
FROM (
  SELECT SUM(f.line_sales_ex_gst) AS mtd_sales
  FROM `jaybel-dev.jaybel_sales_analytics.fact_sales_report` AS f
  JOIN `jaybel-dev.jaybel_sales_analytics.dim_date` AS d ON f.date_key = d.date_key
  WHERE d.date >= DATE_TRUNC(CURRENT_DATE('Australia/Sydney'), MONTH)
) AS mtd
LIMIT 1000
"""

TARGET_SQL = """
SELECT SUM(f.line_sales_ex_gst) AS actual_sales, 6067292.04 AS target_sales
FROM `jaybel-dev.jaybel_sales_analytics.fact_sales_report` AS f
JOIN `jaybel-dev.jaybel_sales_analytics.dim_date` AS d ON f.date_key = d.date_key
WHERE d.fy = '2025-2026'
LIMIT 1000
"""


def test_safety_accepts_run_rate_subquery():
    al = JoinAllowlist()
    r = validate_safety(RUN_RATE_SQL, al)
    assert r.passed, r.message


def test_safety_accepts_target_variance_sql():
    al = JoinAllowlist()
    r = validate_safety(TARGET_SQL, al)
    assert r.passed, r.message


def test_column_check_target_sql():
    from pipeline.validators.column_check import validate_columns

    reg = Registry()
    al = JoinAllowlist()
    r = validate_columns(TARGET_SQL, reg, al)
    assert r.passed, r.message
