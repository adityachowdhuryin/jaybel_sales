#!/usr/bin/env python3
"""Build content/question_catalog.yaml from docs/qa_evaluation_set.yaml."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
QA_PATH = ROOT / "docs" / "qa_evaluation_set.yaml"
OUT_PATH = ROOT / "content" / "question_catalog.yaml"

CATEGORIES = [
    {
        "id": "executive_kpi",
        "label": "Executive & KPIs",
        "description": "FY totals, GP%, daily averages, year-over-year",
        "icon": "chart-bar",
        "order": 1,
    },
    {
        "id": "sales_revenue",
        "label": "Sales & Revenue",
        "description": "Revenue, cost, quantity, territory, warehouse",
        "icon": "currency",
        "order": 2,
    },
    {
        "id": "product",
        "label": "Product & Category",
        "description": "Product groups, items, category trends",
        "icon": "cube",
        "order": 3,
    },
    {
        "id": "customer",
        "label": "Customers & Accounts",
        "description": "Top customers, account lookup, inactive accounts",
        "icon": "users",
        "order": 4,
    },
    {
        "id": "retention",
        "label": "Customer Retention",
        "description": "Month-over-month changes, churn patterns",
        "icon": "arrow-path",
        "order": 5,
    },
    {
        "id": "new_business",
        "label": "New Business (Frazer)",
        "description": "Frazer new business pipeline metrics",
        "icon": "sparkles",
        "order": 6,
    },
    {
        "id": "sales_rep",
        "label": "My Performance",
        "description": "Rep-scoped sales and GP (set rep code in sidebar)",
        "icon": "user",
        "order": 7,
        "requires_rep_code": True,
    },
    {
        "id": "targets",
        "label": "Targets & Goals",
        "description": "FY targets from config — compared to BigQuery actuals",
        "icon": "flag",
        "order": 8,
    },
    {
        "id": "projections",
        "label": "Projections & Forecasting",
        "description": "Run-rate estimates — not exact Power BI forecasts",
        "icon": "trending-up",
        "order": 9,
    },
    {
        "id": "orders",
        "label": "Orders & Line Items",
        "description": "Invoices, item codes, recent orders",
        "icon": "document",
        "order": 10,
    },
    {
        "id": "time_calendar",
        "label": "Time & Working Days",
        "description": "Fiscal calendar, quarters, working days",
        "icon": "calendar",
        "order": 11,
    },
]

CATEGORY_REMAP = {
    "tactical": "orders",
    "rep": "sales_rep",
    "commission": "sales_rep",
}


def infer_category(case: dict) -> str:
    if case.get("category"):
        return CATEGORY_REMAP.get(case["category"], case["category"])
    table = case.get("expected_primary_table", "")
    q = (case.get("question") or "").lower()
    intent = case.get("intent", "")
    if "new_business" in table or "new_busin" in table:
        return "new_business"
    if "working_days" in table or table.endswith("dim_date"):
        return "time_calendar"
    if "dim_sales_rep" in table or "my " in q or " my " in q:
        return "sales_rep"
    if "dim_product" in table or "main_product" in table or "product" in q or "category" in q:
        return "product"
    if "dim_sales_customer" in table or "customer" in q or "account" in q:
        if "retention" in q or "previous month" in q or "month-over-month" in q:
            return "retention"
        return "customer"
    if "dim_department" in table:
        return "executive_kpi"
    if "stg_" in table:
        return "orders" if "sales" in table else "time_calendar"
    if intent in ("trend", "comparison") and "fact_sales" in table:
        return "executive_kpi" if "fiscal year" in q or "fy" in q or "compare" in q else "sales_revenue"
    return "sales_revenue"


def normalize_availability(case: dict) -> str:
    da = case.get("data_availability") or "full"
    legacy_map = {
        "requires_target_table": "full_with_config_target",
        "partial": "partial_run_rate",
    }
    if da in legacy_map:
        return legacy_map[da]
    allowed = {
        "full",
        "full_with_config_target",
        "partial_run_rate",
        "partial_pattern",
        "requires_rep_context",
        "not_in_bq_forecast",
    }
    if da in allowed:
        return da
    return "full"


def table_short(table: str) -> str:
    if not table:
        return ""
    return table.split(".")[-1]


def make_follow_ups(starter: dict) -> list[dict]:
    """Curated 2–3 follow-ups per starter."""
    sid = starter["id"]
    intent = starter.get("intent", "")
    table = starter.get("expected_table_id", "")
    cat = starter.get("category_id", "")
    out: list[dict] = []

    def add(fid: str, text: str, hint_intent: str | None = None):
        out.append(
            {
                "id": fid,
                "parent_starter_id": sid,
                "text": text,
                "intent": hint_intent or intent,
                "data_availability": "full",
            }
        )

    if intent == "ranking" and "customer" in cat:
        add(f"{sid}-f1", "What is total GP$ for the top customer on that list?", "aggregation")
        add(f"{sid}-f2", "Show month-over-month sales trend for the #1 customer", "trend")
    elif intent == "ranking":
        add(f"{sid}-f1", "Show the top 5 only with GP% included", "ranking")
        add(f"{sid}-f2", "Break that ranking down by fiscal quarter", "breakdown")
    elif intent == "trend":
        add(f"{sid}-f1", "Compare that trend to the prior fiscal year", "comparison")
        add(f"{sid}-f2", "Break it down by territory", "breakdown")
    elif intent == "comparison":
        add(f"{sid}-f1", "Show the same comparison for Frazer only", "comparison")
        add(f"{sid}-f2", "Break that down by fiscal month", "trend")
    elif intent == "aggregation" and "fact_sales" in table:
        add(f"{sid}-f1", "Break that down by product main group", "breakdown")
        add(f"{sid}-f2", "Show fiscal month trend for the same metric", "trend")
    elif intent == "lookup" and "dim_sales_rep" in table:
        add(f"{sid}-f1", "Show total sales for the top rep this fiscal year", "ranking")
    elif intent == "lookup":
        add(f"{sid}-f1", "Filter that to Jaybel only", "filter_followup")
        add(f"{sid}-f2", "Show the same for last fiscal year", "comparison")
    elif cat == "new_business":
        add(f"{sid}-f1", "Show new business GP by territory", "breakdown")
        add(f"{sid}-f2", "Monthly trend for new business revenue", "trend")
    elif cat == "sales_rep":
        add(f"{sid}-f1", "Which of my accounts declined month over month?", "ranking")
    elif cat == "targets":
        add(
            f"{sid}-f1",
            "Show actual Furniture GP$ this fiscal year (no target comparison)",
            "aggregation",
        )
        add(f"{sid}-f2", "Show total company GP$ FY 2025-2026", "aggregation")
    elif cat == "projections":
        add(f"{sid}-f1", "What are actual sales month to date from facts?", "aggregation")
    elif cat == "time_calendar":
        add(f"{sid}-f1", "How many working days remain this fiscal month?", "lookup")
    else:
        add(f"{sid}-f1", "Break it down by fiscal month", "trend")
        add(f"{sid}-f2", "Compare Jaybel vs Frazer for the same metric", "comparison")

    return out[:3]


def main() -> None:
    raw = yaml.safe_load(QA_PATH.read_text(encoding="utf-8"))
    cases = raw["cases"]
    starters = []
    follow_ups = []
    starter_ids_by_cat: dict[str, list[str]] = {}

    for case in cases:
        cat = infer_category(case)
        da = normalize_availability(case)
        starter = {
            "id": case["id"],
            "category_id": cat,
            "text": case["question"].strip(),
            "data_availability": da,
            "intent": case.get("intent", "aggregation"),
            "expected_table_id": table_short(case.get("expected_primary_table", "")),
            "join_pattern": case.get("expected_join_pattern"),
            "source": case.get("source", "generic"),
        }
        starters.append(starter)
        starter_ids_by_cat.setdefault(cat, []).append(case["id"])
        follow_ups.extend(make_follow_ups(starter))

    for cat in CATEGORIES:
        cat["starter_count"] = len(starter_ids_by_cat.get(cat["id"], []))

    doc = {
        "version": 1,
        "categories": CATEGORIES,
        "starters": starters,
        "follow_ups": follow_ups,
        "rules": [
            {
                "id": "after_ranking_fact_sales",
                "when": {"last_intent": "ranking", "last_table_id": "fact_sales_report"},
                "suggestions": [
                    {
                        "text": "What is total GP$ for the top result?",
                        "data_availability": "full",
                    },
                    {
                        "text": "Show fiscal month trend for the top item",
                        "data_availability": "full",
                    },
                ],
            },
            {
                "id": "after_trend",
                "when": {"last_intent": "trend"},
                "suggestions": [
                    {
                        "text": "Compare that to the prior fiscal year",
                        "data_availability": "full",
                    },
                    {"text": "Break down by territory", "data_availability": "full"},
                ],
            },
            {
                "id": "after_aggregation",
                "when": {"last_intent": "aggregation"},
                "suggestions": [
                    {
                        "text": "Break down by product category",
                        "data_availability": "full",
                    },
                    {
                        "text": "Show Jaybel vs Frazer split",
                        "data_availability": "full",
                    },
                ],
            },
            {
                "id": "after_dim_customer",
                "when": {"last_table_id": "dim_sales_customer"},
                "suggestions": [
                    {
                        "text": "Show total sales for the largest customer this year",
                        "data_availability": "full",
                    },
                ],
            },
        ],
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        yaml.dump(doc, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_PATH} — {len(starters)} starters, {len(follow_ups)} follow-ups")


def update_qa_categories() -> None:
    """Add category + data_availability to every QA case (Q001–Q097)."""
    data = yaml.safe_load(QA_PATH.read_text(encoding="utf-8"))
    for case in data.get("cases") or []:
        case["category"] = infer_category(case)
        case["data_availability"] = normalize_availability(case)
    QA_PATH.write_text(
        yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"Updated categories in {QA_PATH}")


if __name__ == "__main__":
    import sys

    if "--update-qa-only" in sys.argv:
        update_qa_categories()
    else:
        main()
        update_qa_categories()
