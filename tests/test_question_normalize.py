"""Company-wide possessive normalization."""

from pipeline.user_context import (
    is_rep_scoped_my_phrase,
    normalize_company_possessive,
    requires_rep_scope,
)


def test_my_sales_becomes_our():
    assert normalize_company_possessive("What are my sales this month?") == (
        "What are our sales this month?"
    )


def test_my_commission_unchanged():
    q = "What is my commission payout this quarter?"
    assert normalize_company_possessive(q) == q
    assert requires_rep_scope(q)
    assert is_rep_scoped_my_phrase(q)


def test_my_sales_no_rep_gate():
    assert not requires_rep_scope("What are our sales this month?")


def test_mine_to_ours():
    assert "ours" in normalize_company_possessive("The GP is mine").lower()
