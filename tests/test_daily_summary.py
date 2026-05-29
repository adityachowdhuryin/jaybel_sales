"""Daily business summary service tests (mocked BigQuery)."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from backend.services import daily_business_summary as dbs


@pytest.fixture(autouse=True)
def clear_cache():
    dbs._CACHE["payload"] = None
    dbs._CACHE["expires_at"] = 0.0
    yield


def test_build_payload_from_bq_row():
    row = {
        "as_of_date": date(2026, 5, 19),
        "yesterday_date": date(2026, 5, 18),
        "current_fy_sales": 16_270_000.0,
        "prior_fy_sales": 17_810_000.0,
        "current_fy_gp": 4_800_000.0,
        "prior_fy_gp": 5_520_000.0,
        "mtd_sales": 861_531.0,
        "completed_days": 13,
        "month_working_days": 20,
        "yearly_working_days": 250,
        "yesterday_sales": 102_094.67,
        "yesterday_gp": 27_601.14,
        "yesterday_gp_pct": 27.03,
    }
    payload = dbs._build_payload(row)
    assert payload["as_of_date"] == "2026-05-19"
    assert payload["yesterday_date"] == "2026-05-18"
    assert "19 May 2026" in payload["disclaimer"]
    assert payload["sales_performance"]["current_sales"] == 16_270_000.0
    assert payload["yesterday"]["sales"] == 102_094.67
    assert payload["monthly_on_track"]["days_completed"] == 13


@patch("backend.services.daily_business_summary.execute_query")
def test_get_daily_summary_cached(mock_execute):
    mock_execute.return_value = (
        [
            {
                "as_of_date": date(2026, 5, 19),
                "yesterday_date": date(2026, 5, 18),
                "current_fy_sales": 1.0,
                "prior_fy_sales": 1.0,
                "current_fy_gp": 1.0,
                "prior_fy_gp": 1.0,
                "mtd_sales": 100.0,
                "completed_days": 10,
                "month_working_days": 20,
                "yearly_working_days": 200,
                "yesterday_sales": 50.0,
                "yesterday_gp": 10.0,
                "yesterday_gp_pct": 20.0,
            }
        ],
        [],
        0,
    )
    first = dbs.get_daily_business_summary()
    second = dbs.get_daily_business_summary()
    assert first["as_of_date"] == second["as_of_date"]
    assert mock_execute.call_count == 1
