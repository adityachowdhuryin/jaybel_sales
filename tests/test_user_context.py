"""User context for rep-scoped questions (Phase C passes from Postgres)."""

from pipeline.user_context import UserContext


def test_prompt_block_with_rep():
    block = UserContext(sales_rep_code="REP01").prompt_block()
    assert "sales_rep_code=REP01" in block
    assert "my" in block.lower()


def test_prompt_block_empty():
    assert UserContext().prompt_block() == ""
