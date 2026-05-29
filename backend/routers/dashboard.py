"""Dashboard KPI endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import CurrentUser, get_current_user
from backend.schemas import DailyBusinessSummaryOut
from backend.services import daily_business_summary as dbs

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/daily-summary", response_model=DailyBusinessSummaryOut)
def get_daily_summary(
    _current_user: CurrentUser = Depends(get_current_user),
) -> DailyBusinessSummaryOut:
    try:
        data = dbs.get_daily_business_summary()
        return DailyBusinessSummaryOut(**data)
    except Exception as exc:
        logger.exception("daily summary failed")
        raise HTTPException(
            503,
            "Unable to load daily summary from BigQuery. Check GCP credentials and dataset access.",
        ) from exc
