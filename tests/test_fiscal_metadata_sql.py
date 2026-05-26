"""Deterministic FY boundary SQL."""

from pipeline.fiscal_calendar import current_fiscal_year_label, last_fiscal_year_label
from pipeline.fiscal_metadata_sql import try_deterministic_fy_sql
from pipeline.models import L1Result


def test_deterministic_last_fy_sql():
    l1 = L1Result(
        intent="lookup",
        table_id="jaybel-dev.jaybel_sales_analytics.dim_date",
        join_pattern=None,
        confidence=0.9,
        entities=[],
        time_range=None,
        plan=[],
    )
    q = "What's the last FY and start month and end month?"
    sql = try_deterministic_fy_sql(q, l1)
    assert sql
    assert f"fy = '{last_fiscal_year_label()}'" in sql
    assert "ORDER BY fy DESC" not in sql


def test_deterministic_latest_fy_sql():
    l1 = L1Result(
        intent="lookup",
        table_id="jaybel-dev.jaybel_sales_analytics.dim_date",
        join_pattern=None,
        confidence=0.9,
        entities=[],
        time_range=None,
        plan=[],
    )
    q = "What's the latest FY and start month and end month?"
    sql = try_deterministic_fy_sql(q, l1)
    assert sql
    assert f"fy = '{current_fiscal_year_label()}'" in sql
