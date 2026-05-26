"""L2 follow-up SQL context formatting."""

from pipeline.followup_context import FollowUpContext
from pipeline.followup_sql_context import (
    extract_filter_summary,
    extract_metric_from_sql,
    format_l2_followup_block,
)


def test_extract_metric_gp():
    sql = "SELECT SUM(f.line_gp_dollar) AS gp FROM fact f"
    assert extract_metric_from_sql(sql) == "line_gp_dollar (GP)"


def test_extract_filter_summary():
    sql = (
        "SELECT 1 FROM f JOIN d WHERE d.fy = '2025-2026' AND f.territory_code = 'FRA' "
        "GROUP BY 1 LIMIT 10"
    )
    summary = extract_filter_summary(sql)
    assert summary
    assert "territory_code" in summary
    assert "2025-2026" in summary


def test_format_l2_followup_block():
    ctx = FollowUpContext(
        is_follow_up=True,
        prior_question="Top customers by GP",
        prior_metric="line_gp_dollar (GP)",
        prior_filters="d.fiscal_quarter = 'Q1'",
        prior_join_pattern="fact_sales_with_dims",
        prior_sql_excerpt="SELECT SUM(f.line_gp_dollar)",
    )
    block = format_l2_followup_block(ctx)
    assert "Prior metric" in block
    assert "line_gp_dollar" in block
    assert "territory_code" in block
    assert "APAC" in block
