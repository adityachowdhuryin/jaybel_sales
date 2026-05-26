"""Deterministic SQL for dim_date fiscal-year calendar lookups."""

from __future__ import annotations

import re

from pipeline.models import L1Result
from pipeline.time_range import is_fiscal_phrase, resolve_time_range

_DIM_DATE_ID = "jaybel-dev.jaybel_sales_analytics.dim_date"

_FY_CALENDAR_RE = re.compile(
    r"(start\s+month|end\s+month|start\s+and\s+end|start\s+monthand)",
    re.I,
)
_RELATIVE_FY_RE = re.compile(
    r"\b(?:current|last|latest|this|previous|prior|most\s+recent)\s+"
    r"(?:fiscal\s+)?(?:year|fy)\b|\b(?:current|last|latest)\s+fy\b",
    re.I,
)


def is_fy_calendar_lookup(question: str) -> bool:
    if not is_fiscal_phrase(question):
        return False
    if _FY_CALENDAR_RE.search(question):
        return True
    return bool(_RELATIVE_FY_RE.search(question))


def build_fy_boundary_sql(fy_label: str, table_id: str = _DIM_DATE_ID) -> str:
    return f"""SELECT
  d.fy,
  MIN(CASE WHEN d.fiscal_month_no = 1 THEN d.fiscal_month_name END) AS start_month,
  MIN(CASE WHEN d.fiscal_month_no = 1 THEN d.date END) AS start_date,
  MAX(CASE WHEN d.fiscal_month_no = 12 THEN d.fiscal_month_name END) AS end_month,
  MAX(CASE WHEN d.fiscal_month_no = 12 THEN d.date END) AS end_date
FROM `{table_id}` AS d
WHERE d.fy = '{fy_label}'
GROUP BY d.fy
LIMIT 1"""


def try_deterministic_fy_sql(question: str, l1: L1Result) -> str | None:
    """Bypass L2 when question is FY label + start/end months on dim_date."""
    if l1.table_id != _DIM_DATE_ID:
        return None
    if not is_fy_calendar_lookup(question):
        return None
    tr = resolve_time_range(question, l1.time_range)
    if not tr or not tr.label or tr.start:
        return None
    return build_fy_boundary_sql(tr.label, l1.table_id)
