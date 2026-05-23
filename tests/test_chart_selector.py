"""Chart selector rules — intent and row shape."""

from pipeline.chart_selector import select_chart
from pipeline.models import L1Result, QueryResult


def _l1(intent: str) -> L1Result:
    return L1Result(
        intent=intent,
        table_id="jaybel-dev.jaybel_sales_analytics.fact_sales_report",
        join_pattern="fact_sales_with_dims",
        confidence=0.9,
        entities=[],
        time_range=None,
        plan=["Aggregate and compare"],
    )


def test_single_row_no_chart():
    qr = QueryResult(
        rows=[{"total_sales": 1000000}],
        columns=["total_sales"],
        row_count=1,
        empty_result=False,
    )
    assert select_chart("Total sales FY", _l1("aggregation"), qr) is None


def test_trend_line_chart():
    qr = QueryResult(
        rows=[
            {"fiscal_month": "July", "sales": 100},
            {"fiscal_month": "August", "sales": 120},
            {"fiscal_month": "September", "sales": 90},
        ],
        columns=["fiscal_month", "sales"],
        row_count=3,
        empty_result=False,
    )
    spec = select_chart("Month trend", _l1("trend"), qr)
    assert spec is not None
    assert spec["chart_type"] == "line"
    assert spec["x"] == "fiscal_month"


def test_ranking_horizontal_bar():
    qr = QueryResult(
        rows=[
            {"account_name": "Very Long Customer Name Pty Ltd", "total_sales": 50000},
            {"account_name": "Another Long Account Name Here", "total_sales": 40000},
        ],
        columns=["account_name", "total_sales"],
        row_count=2,
        empty_result=False,
    )
    spec = select_chart("Top customers", _l1("ranking"), qr)
    assert spec is not None
    assert spec["chart_type"] == "bar"
    assert spec.get("orientation") == "horizontal"


def test_pie_breakdown():
    qr = QueryResult(
        rows=[
            {"territory": "North", "sales": 40},
            {"territory": "South", "sales": 35},
            {"territory": "East", "sales": 25},
        ],
        columns=["territory", "sales"],
        row_count=3,
        empty_result=False,
    )
    spec = select_chart("Revenue share breakdown by territory", _l1("comparison"), qr)
    assert spec is not None
    assert spec["chart_type"] == "pie"


def test_paired_bar_actual_target():
    qr = QueryResult(
        rows=[{"actual_sales": 5_000_000, "target_sales": 6_067_292.04}],
        columns=["actual_sales", "target_sales"],
        row_count=1,
        empty_result=False,
    )
    spec = select_chart("Overall business target variance", _l1("comparison"), qr)
    assert spec is not None
    assert spec["chart_type"] == "paired_bar"
    assert len(spec["series"]) == 2


def test_grouped_bar_actual_target():
    qr = QueryResult(
        rows=[
            {"main_group_name": "Office Supplies", "actual_gp": 100, "target_gp": 120},
            {"main_group_name": "Furniture", "actual_gp": 200, "target_gp": 250},
        ],
        columns=["main_group_name", "actual_gp", "target_gp"],
        row_count=2,
        empty_result=False,
    )
    spec = select_chart("GP by category vs target", _l1("comparison"), qr)
    assert spec is not None
    assert spec["chart_type"] == "grouped_bar"


def test_lookup_no_chart():
    qr = QueryResult(
        rows=[{"a": 1, "b": 2, "c": 3}] * 5,
        columns=["a", "b", "c"],
        row_count=5,
        empty_result=False,
    )
    assert select_chart("List orders", _l1("lookup"), qr) is None
