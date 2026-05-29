"""Daily business summary KPIs from BigQuery (company-wide)."""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Any

from pipeline.analytics_context import load_sales_targets
from pipeline.bq_client import execute_query
from pipeline.config import bq_dataset, gcp_project_id

_CACHE: dict[str, Any] = {"expires_at": 0.0, "payload": None}
_CACHE_TTL_SEC = 600

FACT = f"`{gcp_project_id()}.{bq_dataset()}.fact_sales_report`"
DIM_DATE = f"`{gcp_project_id()}.{bq_dataset()}.dim_date`"
WORKING_DAYS = f"`{gcp_project_id()}.{bq_dataset()}.stg_total_working_days`"

CURRENT_FY = "2025-2026"
PRIOR_FY = "2024-2025"
ANNUAL_SALES_TARGET = 6067292.04


def _summary_sql() -> str:
    return f"""
WITH as_of AS (
  SELECT MAX(d.date) AS as_of_date
  FROM {FACT} AS f
  INNER JOIN {DIM_DATE} AS d ON f.date_key = d.date_key
),
ctx AS (
  SELECT
    a.as_of_date,
    DATE_SUB(a.as_of_date, INTERVAL 1 DAY) AS yesterday_date
  FROM as_of AS a
),
as_of_dim AS (
  SELECT d.fy, d.fiscal_month_no, d.fiscal_month_name, d.fiscal_year
  FROM {DIM_DATE} AS d
  CROSS JOIN ctx
  WHERE d.date = ctx.as_of_date
  LIMIT 1
),
fy_totals AS (
  SELECT
    d.fy,
    SUM(f.line_sales_ex_gst) AS total_sales,
    SUM(f.line_gp_dollar) AS total_gp
  FROM {FACT} AS f
  INNER JOIN {DIM_DATE} AS d ON f.date_key = d.date_key
  WHERE d.fy IN ('{CURRENT_FY}', '{PRIOR_FY}')
  GROUP BY d.fy
),
mtd AS (
  SELECT
    SUM(f.line_sales_ex_gst) AS mtd_sales,
    SUM(f.line_gp_dollar) AS mtd_gp
  FROM {FACT} AS f
  INNER JOIN {DIM_DATE} AS d ON f.date_key = d.date_key
  CROSS JOIN ctx
  CROSS JOIN as_of_dim AS ad
  WHERE d.fy = ad.fy
    AND d.fiscal_month_no = ad.fiscal_month_no
    AND d.date <= ctx.as_of_date
),
yesterday AS (
  SELECT
    SUM(f.line_sales_ex_gst) AS sales,
    SUM(f.line_gp_dollar) AS gp_dollar,
    SAFE_DIVIDE(SUM(f.line_gp_dollar), SUM(f.line_sales_ex_gst)) * 100 AS gp_pct
  FROM {FACT} AS f
  INNER JOIN {DIM_DATE} AS d ON f.date_key = d.date_key
  CROSS JOIN ctx
  WHERE d.date = ctx.yesterday_date
),
working_days AS (
  SELECT
    SAFE_CAST(w.Completed_days AS INT64) AS completed_days,
    SAFE_CAST(w.total_working_days AS INT64) AS month_working_days,
    SAFE_CAST(w.YearlyTotalWorkingDays AS INT64) AS yearly_working_days
  FROM {WORKING_DAYS} AS w
  CROSS JOIN as_of_dim AS ad
  WHERE w.fiscal_year = ad.fy
    AND w.month = ad.fiscal_month_name
  LIMIT 1
)
SELECT
  ctx.as_of_date,
  ctx.yesterday_date,
  ad.fy AS current_fy,
  ad.fiscal_month_name,
  (SELECT total_sales FROM fy_totals WHERE fy = '{CURRENT_FY}') AS current_fy_sales,
  (SELECT total_sales FROM fy_totals WHERE fy = '{PRIOR_FY}') AS prior_fy_sales,
  (SELECT total_gp FROM fy_totals WHERE fy = '{CURRENT_FY}') AS current_fy_gp,
  (SELECT total_gp FROM fy_totals WHERE fy = '{PRIOR_FY}') AS prior_fy_gp,
  mtd.mtd_sales,
  mtd.mtd_gp,
  yesterday.sales AS yesterday_sales,
  yesterday.gp_dollar AS yesterday_gp,
  yesterday.gp_pct AS yesterday_gp_pct,
  wd.completed_days,
  wd.month_working_days,
  wd.yearly_working_days
FROM ctx
CROSS JOIN as_of_dim AS ad
CROSS JOIN mtd
CROSS JOIN yesterday
LEFT JOIN working_days AS wd ON TRUE
LIMIT 1
"""


def _num(v: Any) -> float:
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _gp_pct(gp: float, sales: float) -> float:
    if sales <= 0:
        return 0.0
    return (gp / sales) * 100.0


def _format_disclaimer(as_of: date) -> str:
    label = f"{as_of.day} {as_of.strftime('%B')} {as_of.year}"
    return f"Latest data available till {label}"


def _build_payload(row: dict[str, Any]) -> dict[str, Any]:
    as_of_raw = row.get("as_of_date")
    if isinstance(as_of_raw, datetime):
        as_of = as_of_raw.date()
    elif isinstance(as_of_raw, date):
        as_of = as_of_raw
    else:
        as_of = date.today()

    yesterday_raw = row.get("yesterday_date")
    if isinstance(yesterday_raw, datetime):
        yesterday_date = yesterday_raw.date()
    elif isinstance(yesterday_raw, date):
        yesterday_date = yesterday_raw
    else:
        yesterday_date = as_of - timedelta(days=1)

    current_sales = _num(row.get("current_fy_sales"))
    prior_sales = _num(row.get("prior_fy_sales"))
    current_gp = _num(row.get("current_fy_gp"))
    prior_gp = _num(row.get("prior_fy_gp"))
    yoy_pct = ((current_sales - prior_sales) / prior_sales * 100.0) if prior_sales else 0.0

    current_gp_pct = _gp_pct(current_gp, current_sales)
    prior_gp_pct = _gp_pct(prior_gp, prior_sales)
    gp_variance = current_gp - prior_gp

    mtd_sales = _num(row.get("mtd_sales"))
    completed = int(_num(row.get("completed_days"))) or 1
    month_wd = int(_num(row.get("month_working_days"))) or 20
    yearly_wd = int(_num(row.get("yearly_working_days"))) or 250
    days_remaining = max(month_wd - completed, 0)

    annual_target = ANNUAL_SALES_TARGET
    for t in load_sales_targets().get("targets") or []:
        if t.get("id") == "overall_business_sales":
            annual_target = float(t.get("amount") or annual_target)
            break

    month_target = annual_target * (month_wd / yearly_wd) if yearly_wd else annual_target / 12.0
    daily_avg_mtd = mtd_sales / completed if completed else 0.0
    daily_avg_needed = (month_target - mtd_sales) / days_remaining if days_remaining else 0.0
    projected_close = (mtd_sales / completed) * month_wd if completed else mtd_sales
    closed_mtd_pct = (mtd_sales / month_target * 100.0) if month_target else 0.0
    projected_pct = (projected_close / month_target * 100.0) if month_target else 0.0

    yesterday_sales = _num(row.get("yesterday_sales"))
    yesterday_gp = _num(row.get("yesterday_gp"))
    yesterday_gp_pct = _num(row.get("yesterday_gp_pct"))
    fy_avg_gp_pct = current_gp_pct

    # Sales Good if yesterday >= MTD daily average; GP Below Average if under FY GP%.
    sales_status = "Good" if yesterday_sales >= daily_avg_mtd else "Below Average"
    gp_status = "Below Average" if yesterday_gp_pct < fy_avg_gp_pct else "Good"

    return {
        "as_of_date": as_of.isoformat(),
        "yesterday_date": yesterday_date.isoformat(),
        "disclaimer": _format_disclaimer(as_of),
        "sales_performance": {
            "current_fy": CURRENT_FY,
            "prior_fy": PRIOR_FY,
            "current_sales": current_sales,
            "prior_sales": prior_sales,
            "yoy_pct": yoy_pct,
        },
        "gross_profit": {
            "current_gp": current_gp,
            "prior_gp": prior_gp,
            "current_gp_pct": current_gp_pct,
            "prior_gp_pct": prior_gp_pct,
            "gp_variance_dollars": gp_variance,
        },
        "monthly_on_track": {
            "daily_avg_mtd": daily_avg_mtd,
            "days_completed": completed,
            "daily_avg_needed": daily_avg_needed,
            "days_remaining": days_remaining,
            "monthly_target": month_target,
            "closed_mtd": mtd_sales,
            "closed_mtd_pct": closed_mtd_pct,
            "projected_close": projected_close,
            "projected_pct": projected_pct,
        },
        "yesterday": {
            "sales": yesterday_sales,
            "gp_dollar": yesterday_gp,
            "gp_pct": yesterday_gp_pct,
            "fy_avg_gp_pct": fy_avg_gp_pct,
            "sales_status": sales_status,
            "gp_status": gp_status,
        },
    }


def get_daily_business_summary(*, use_cache: bool = True) -> dict[str, Any]:
    now = time.time()
    if use_cache and _CACHE["payload"] and _CACHE["expires_at"] > now:
        return _CACHE["payload"]

    rows, _cols, _bytes = execute_query(_summary_sql(), timeout_sec=45)
    if not rows:
        raise RuntimeError("No summary data returned from BigQuery")

    payload = _build_payload(rows[0])
    _CACHE["payload"] = payload
    _CACHE["expires_at"] = now + _CACHE_TTL_SEC
    return payload
