"""Phase A step 1 — registry and keyword index."""

from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.keyword_index import KeywordIndex
from pipeline.registry.loader import Registry


def test_loads_13_tables():
    reg = Registry()
    assert len(reg.tables) == 13


def test_keyword_sales_routes_to_fact():
    reg = Registry()
    idx = KeywordIndex(reg.tables)
    top = idx.top_table_ids("total sales revenue this year", top_k=3)
    assert "jaybel-dev.jaybel_sales_analytics.fact_sales_report" in top


def test_keyword_working_days():
    reg = Registry()
    idx = KeywordIndex(reg.tables)
    top = idx.top_table_ids("how many working days in July", top_k=1)
    assert top[0] == "jaybel-dev.jaybel_sales_analytics.stg_total_working_days"


def test_keyword_new_business():
    reg = Registry()
    idx = KeywordIndex(reg.tables)
    top = idx.top_table_ids("Frazer new business pipeline", top_k=2)
    assert "jaybel-dev.jaybel_sales_analytics.fact_new_business_frazer" in top


def test_join_allowlist_patterns():
    al = JoinAllowlist()
    assert "fact_sales_with_dims" in al.pattern_ids()
    allowed = al.allowed_tables_for_pattern("fact_sales_with_dims")
    assert any("fact_sales_report" in t for t in allowed)
