"""Phase A steps 2–3 — validators without live BQ for A/C; B optional integration."""

import pytest

from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.loader import Registry
from pipeline.validators.column_check import validate_columns
from pipeline.validators.dry_run import validate_dry_run
from pipeline.validators.safety_check import validate_safety

GOOD_SQL = """
SELECT SUM(f.line_sales_ex_gst) AS total_sales
FROM `jaybel-dev.jaybel_sales_analytics.fact_sales_report` AS f
JOIN `jaybel-dev.jaybel_sales_analytics.dim_date` AS d ON f.date_key = d.date_key
WHERE d.fy = '2025-2026'
LIMIT 1000
"""

BAD_COLUMN_SQL = """
SELECT f.not_a_real_column
FROM `jaybel-dev.jaybel_sales_analytics.fact_sales_report` AS f
LIMIT 10
"""

BAD_JOIN_SQL = """
SELECT f.line_sales_ex_gst
FROM `jaybel-dev.jaybel_sales_analytics.fact_sales_report` AS f
JOIN `jaybel-dev.jaybel_sales_analytics.stg_sales_cust` AS c ON 1=1
LIMIT 10
"""

DML_SQL = "DELETE FROM `jaybel-dev.jaybel_sales_analytics.fact_sales_report` WHERE TRUE"


def test_safety_rejects_dml():
    al = JoinAllowlist()
    r = validate_safety(DML_SQL, al)
    assert not r.passed


def test_safety_accepts_good_sql():
    al = JoinAllowlist()
    r = validate_safety(GOOD_SQL, al)
    assert r.passed


def test_column_check_good():
    reg = Registry()
    al = JoinAllowlist()
    r = validate_columns(GOOD_SQL, reg, al)
    assert r.passed


def test_column_check_bad_column():
    reg = Registry()
    al = JoinAllowlist()
    r = validate_columns(BAD_COLUMN_SQL, reg, al)
    assert not r.passed


def test_safety_bad_join():
    al = JoinAllowlist()
    r = validate_safety(BAD_JOIN_SQL, al)
    assert not r.passed


@pytest.mark.integration
def test_dry_run_good_sql():
    r = validate_dry_run(GOOD_SQL)
    assert r.passed, r.message
