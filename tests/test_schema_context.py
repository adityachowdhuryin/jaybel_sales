"""Tests for join-aware L2 schema blocks."""

from pipeline.models import L1Result
from pipeline.registry.join_allowlist import JoinAllowlist
from pipeline.registry.loader import Registry
from pipeline.schema_context import build_l2_schema_block


def test_l2_schema_includes_dim_columns():
    reg = Registry()
    allowlist = JoinAllowlist()
    l1 = L1Result(
        intent="aggregation",
        table_id="jaybel-dev.jaybel_sales_analytics.fact_sales_report",
        join_pattern="fact_sales_with_dims",
        confidence=0.9,
        entities=[],
        time_range=None,
        plan=[],
    )
    block = build_l2_schema_block(reg, allowlist, l1, "top customers by GP")
    assert "account_name" in block
    assert "fiscal_quarter" in block
    assert "fact_sales_report" in block


def test_schema_block_for_alias():
    reg = Registry()
    block = reg.schema_block_for_alias(
        "jaybel-dev.jaybel_sales_analytics.dim_sales_customer",
        "c",
        "f.customer_key = c.customer_key",
    )
    assert "c →" in block
    assert "c.account_name" in block
