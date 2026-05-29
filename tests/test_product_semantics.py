"""Product name (description) vs product group (main_group_name)."""

from pipeline.column_aliases import glossary_snippet_for_l2, product_semantics_snippet
from pipeline.registry.loader import Registry


def test_fact_registry_has_description_column():
    reg = Registry()
    table = reg.get("jaybel-dev.jaybel_sales_analytics.fact_sales_report")
    names = {c.name for c in table.columns}
    assert "description" in names


def test_product_semantics_snippet_mentions_description():
    block = product_semantics_snippet()
    assert "fact_sales_report.description" in block
    assert "main_group_name" in block
    assert "Office Supplies" in block or "product group" in block.lower()


def test_glossary_includes_product_semantics():
    block = glossary_snippet_for_l2()
    assert "Product vs product group" in block


def test_few_shot_best_product_groups_by_description():
    reg = Registry()
    table = reg.get("jaybel-dev.jaybel_sales_analytics.fact_sales_report")
    questions = [ex.question.lower() for ex in table.few_shot_examples]
    assert any("performing best" in q or "best-selling products" in q for q in questions)
    sqls = [ex.sql for ex in table.few_shot_examples]
    assert any("f.description" in s and "main_group_name" in s for s in sqls)
