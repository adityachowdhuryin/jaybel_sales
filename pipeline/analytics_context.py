"""Office Supplies v1.2 — targets, run-rate, closed accounts, embroidery archetypes."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from pipeline.config import PROJECT_ROOT

CONFIG_DIR = PROJECT_ROOT / "config"

RUN_RATE_FORMULAS = """
Run-rate projection (estimate — NOT Power BI forecast):
  projected_month_sales = (mtd_sales / completed_working_days) * total_working_days_in_month
  projected_month_gp = (mtd_gp / completed_working_days) * total_working_days_in_month
Use scalar subqueries to stg_total_working_days for completed_days and total_working_days.
Filter MTD facts with dim_date in Australia/Sydney calendar month unless user says fiscal month.
Always state this is a run-rate estimate, not the BI "Projected Monthly Sales/GP" measure.
"""

COMMISSION_NOTE = """
Closed-won / closed deals / payout proxy: use fact_sales_report invoiced lines for the
authenticated sales_rep_code in the requested period (month or fiscal quarter).
There is no CRM deal_stage column — invoiced revenue and line_gp_dollar are the v1.2 definition.
"""


@dataclass
class Archetypes:
    target: bool = False
    run_rate: bool = False
    closed_account: bool = False
    embroidery: bool = False
    commission: bool = False
    bi_forecast_only: bool = False
    matched_target_ids: list[str] = field(default_factory=list)


def _load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_sales_targets() -> dict[str, Any]:
    return _load_yaml("sales_targets.yaml")


@lru_cache(maxsize=1)
def load_account_patterns() -> dict[str, Any]:
    return _load_yaml("account_patterns.yaml")


@lru_cache(maxsize=1)
def load_embroidery_patterns() -> dict[str, Any]:
    return _load_yaml("embroidery_patterns.yaml")


def _tokenize(q: str) -> str:
    return q.lower()


def detect_archetypes(question: str) -> Archetypes:
    q = _tokenize(question)
    arch = Archetypes()
    targets_cfg = load_sales_targets()
    for t in targets_cfg.get("targets") or []:
        tid = t.get("id") or ""
        if tid == "projected_furniture_gp_variance_reference":
            continue
        labels = [str(t.get("label", "")).lower()] + [str(a).lower() for a in t.get("aliases") or []]
        if any(lbl and lbl in q for lbl in labels):
            arch.target = True
            arch.matched_target_ids.append(tid)
        if "target" in q or "variance" in q or "behind" in q or "on track" in q:
            if t.get("scope") == "company" and ("business" in q or "6m" in q or "6 m" in q or "6067" in q):
                if "overall_business_sales" not in arch.matched_target_ids:
                    arch.target = True
                    arch.matched_target_ids.append("overall_business_sales")
            if "furniture" in q and ("gp" in q or "387" in q):
                if "furniture_gp" not in arch.matched_target_ids:
                    arch.target = True
                    arch.matched_target_ids.append("furniture_gp")
            if "bts" in q or "back to school" in q:
                if "bts_sales" not in arch.matched_target_ids:
                    arch.target = True
                    arch.matched_target_ids.append("bts_sales")

    if re.search(r"projected|projection|forecast|run[- ]?rate|month to date|mtd", q):
        arch.run_rate = True
    if "working day" in q or "completed day" in q:
        arch.run_rate = True
    if "daily average" in q and ("projected" in q or "on track" in q):
        arch.run_rate = True

    if "closed" in q and ("account" in q or "status" in q or "lost" in q):
        arch.closed_account = True
    if "*** account closed ***" in q or "account closed" in q:
        arch.closed_account = True

    if "embroid" in q or "custom print" in q or "custom printing" in q:
        arch.embroidery = True

    if any(x in q for x in ("closed-won", "closed won", "closed deal", "payout", "commission")):
        arch.commission = True
    if "my " in q and ("closed" in q or "payout" in q):
        arch.commission = True

    if "why" in q and "negative variance" in q and "projected" in q and "furniture" in q:
        arch.bi_forecast_only = True
    if "-1695009" in q.replace(",", "") or "1695009" in q.replace(",", ""):
        arch.bi_forecast_only = True

    return arch


def target_by_id(target_id: str) -> dict[str, Any] | None:
    for t in load_sales_targets().get("targets") or []:
        if t.get("id") == target_id:
            return t
    return None


def targets_prompt_block(arch: Archetypes) -> str:
    if not arch.target:
        return ""
    lines = [
        "\nConfigured FY targets (from config/sales_targets.yaml — apply as SQL literals, do NOT query a target table):"
    ]
    seen: set[str] = set()
    for tid in arch.matched_target_ids:
        if tid in seen:
            continue
        seen.add(tid)
        t = target_by_id(tid)
        if not t:
            continue
        amt = t.get("amount")
        cat = t.get("category_main_group")
        metric = t.get("metric")
        fy = t.get("fiscal_year", "2025-2026")
        lines.append(
            f"- {t.get('label')}: target_amount={amt}, metric={metric}, "
            f"fiscal_year={fy}, category_main_group={cat!r}"
        )
        if metric == "sales_ex_gst":
            lines.append(
                "  SQL: SUM(f.line_sales_ex_gst) AS actual; "
                f"({amt} - actual) AS gap_to_target OR (actual - {amt}) AS variance"
            )
        elif metric == "gp_dollar":
            lines.append(
                "  SQL: SUM(f.line_gp_dollar) AS actual; filter dim_product.main_group_name when category set"
            )
        if tid == "bts_sales" and not cat:
            lines.append(
                "  WARNING: BTS category_main_group not configured — report actuals and "
                "state BTS product filter is pending business confirmation."
            )
    lines.append(
        "Include pct_difference = (actual - target) / target * 100 when user asks percentage."
    )
    return "\n".join(lines) + "\n"


def run_rate_prompt_block(arch: Archetypes) -> str:
    if not arch.run_rate:
        return ""
    return f"\n{RUN_RATE_FORMULAS}\n"


def closed_account_prompt_block(arch: Archetypes) -> str:
    if not arch.closed_account:
        return ""
    patterns = load_account_patterns().get("closed_status_patterns") or []
    return (
        "\nClosed accounts: no account_status column. Filter dim_sales_customer.account_name "
        f"with UPPER(account_name) LIKE patterns (case-insensitive): {patterns}. "
        "Join to fact_sales_report for historical revenue.\n"
    )


def embroidery_prompt_block(arch: Archetypes) -> str:
    if not arch.embroidery:
        return ""
    emb = load_embroidery_patterns()
    kws = emb.get("description_keywords") or []
    prefixes = emb.get("item_code_prefixes") or []
    return (
        "\nEmbroidery/custom printing: prefer table stg_sales_report (line description is STRING). "
        f"Filter LOWER(description) LIKE any of: {kws}. "
        f"Item code prefixes: {prefixes or 'none configured'}. "
        "This week = Australia/Sydney calendar week. trans_date is STRING — use "
        "COALESCE(SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', trans_date), "
        "SAFE.PARSE_TIMESTAMP('%Y-%m-%d', trans_date)) for mixed formats.\n"
    )


def bi_forecast_prompt_block(arch: Archetypes) -> str:
    if not arch.bi_forecast_only:
        return ""
    ref = target_by_id("projected_furniture_gp_variance_reference")
    amt = ref.get("amount") if ref else -1695009.72
    return (
        f"\nBI forecast variance ({amt}) is NOT reproducible from BigQuery facts. "
        "Explain that projected Furniture GP$ comes from the Power BI model. "
        "Offer: actual Furniture GP$ FY 2025-2026, Furniture GP target variance from config, "
        "or run-rate GP estimate with disclaimer.\n"
    )


def commission_prompt_block(arch: Archetypes) -> str:
    if not arch.commission:
        return ""
    return f"\n{COMMISSION_NOTE}\n"


def prompt_block(question: str) -> str:
    arch = detect_archetypes(question)
    parts = [
        targets_prompt_block(arch),
        run_rate_prompt_block(arch),
        closed_account_prompt_block(arch),
        embroidery_prompt_block(arch),
        commission_prompt_block(arch),
        bi_forecast_prompt_block(arch),
    ]
    return "".join(p for p in parts if p)


def detect_external_concepts(question: str) -> list[str]:
    """Keywords suggesting data outside Jaybel BQ sales analytics."""
    q = _tokenize(question)
    from pipeline.query_understanding_config import external_concepts

    matched: list[str] = []
    for concept in external_concepts():
        if concept.lower() in q:
            matched.append(concept)
    return matched


def out_of_dataset_guidance(question: str, arch: Archetypes | None = None) -> str | None:
    arch = arch or detect_archetypes(question)
    externals = detect_external_concepts(question)
    if arch.bi_forecast_only:
        return (
            "The Power BI projected variance (e.g. Furniture GP forecast gap) is not stored "
            "in BigQuery. I can show actual Furniture GP$, config target variance, or a "
            "run-rate estimate with a clear disclaimer."
        )
    if externals:
        return (
            f"This assistant only answers from Jaybel sales analytics in BigQuery "
            f"(revenue, GP, customers, products, reps, fiscal periods, Frazer new business, "
            f"working days, embroidery staging). Your question mentions concepts we do not "
            f"have here ({', '.join(externals[:3])}). Try rephrasing using sales, GP, or customer metrics."
        )
    return None


def l1_routing_hints(question: str) -> str:
    arch = detect_archetypes(question)
    hints: list[str] = []
    if arch.embroidery:
        hints.append(
            "Route to stg_sales_report for embroidery/custom printing (raw line description)."
        )
    if arch.run_rate and not arch.embroidery:
        hints.append(
            "Primary fact_sales_report; use scalar subquery to stg_total_working_days for working days."
        )
    if arch.bi_forecast_only:
        hints.append("Primary fact_sales_report for actuals; do not invent BI forecast logic.")
    return " ".join(hints)
