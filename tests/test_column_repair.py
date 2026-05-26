"""Deterministic column repair tests."""

from pipeline.column_aliases import apply_column_aliases, resolve_alias
from pipeline.column_repair import repair_sql_from_validation
from pipeline.models import ValidationResult


def test_resolve_alias_global():
    assert resolve_alias(None, "customer_name") == "account_name"
    assert resolve_alias(None, "fiscal_q") == "fiscal_quarter"


def test_apply_column_aliases():
    sql = "SELECT c.customer_name, d.fiscal_q FROM t"
    fixed = apply_column_aliases(sql)
    assert "account_name" in fixed
    assert "fiscal_quarter" in fixed
    assert "customer_name" not in fixed


def test_repair_from_validation_details():
    fail = ValidationResult(
        passed=False,
        validator="column_check",
        message="Invalid columns",
        details={
            "table_id": "jaybel-dev.jaybel_sales_analytics.dim_sales_customer",
            "bad_columns": ["customer_name"],
            "suggested_replacements": {"customer_name": "account_name"},
        },
    )
    sql = "SELECT c.customer_name FROM `p.d.dim_sales_customer` c"
    repaired, changed = repair_sql_from_validation(sql, fail)
    assert changed
    assert "account_name" in repaired
