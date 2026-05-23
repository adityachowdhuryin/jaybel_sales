"""Office Supplies cases — archetype detection smoke tests."""

from pipeline.analytics_context import detect_archetypes
from pipeline.qa_runner import load_cases


def test_office_supplies_cases_load():
    cases = load_cases(case_filter="Q061-Q097", source="office_supplies_bi_pdf")
    assert len(cases) == 37


def test_q063_target_archetype():
    cases = {c["id"]: c for c in load_cases(case_filter="Q063")}
    arch = detect_archetypes(cases["Q063"]["question"])
    assert arch.target


def test_q093_bi_forecast():
    cases = {c["id"]: c for c in load_cases(case_filter="Q093")}
    arch = detect_archetypes(cases["Q093"]["question"])
    assert arch.bi_forecast_only


def test_q085_embroidery():
    cases = {c["id"]: c for c in load_cases(case_filter="Q085")}
    arch = detect_archetypes(cases["Q085"]["question"])
    assert arch.embroidery
