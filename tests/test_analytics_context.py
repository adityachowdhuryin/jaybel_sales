"""v1.2 analytics context — targets, archetypes, prompts."""

from pipeline.analytics_context import (
    detect_archetypes,
    load_sales_targets,
    prompt_block,
    target_by_id,
)


def test_load_sales_targets():
    cfg = load_sales_targets()
    assert cfg.get("version") == 1
    ids = {t["id"] for t in cfg.get("targets") or []}
    assert "overall_business_sales" in ids
    assert "furniture_gp" in ids


def test_detect_target_archetype():
    arch = detect_archetypes(
        "How far behind are we on our Overall Business Target of $6M?"
    )
    assert arch.target
    assert "overall_business_sales" in arch.matched_target_ids or arch.matched_target_ids


def test_detect_run_rate():
    arch = detect_archetypes("What are our Projected Monthly Sales compared to MTD?")
    assert arch.run_rate


def test_detect_bi_forecast():
    arch = detect_archetypes(
        "Why is the Projected Furniture GP$ showing a negative variance of -$1,695,009.72?"
    )
    assert arch.bi_forecast_only


def test_prompt_block_includes_target():
    block = prompt_block("Variance against Furniture Target of $387K")
    assert "387173" in block or "387" in block
    assert "config/sales_targets" in block


def test_target_by_id():
    t = target_by_id("furniture_gp")
    assert t is not None
    assert float(t["amount"]) == 387173.20
