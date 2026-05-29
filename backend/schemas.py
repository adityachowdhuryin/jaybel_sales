"""API request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SessionOut(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class SessionCreate(BaseModel):
    title: str = "New chat"


class TurnOut(BaseModel):
    id: UUID
    query_id: str
    question: str
    intent: str | None = None
    table_id: str | None = None
    join_pattern: str | None = None
    sql: str | None = None
    answer: str | None = None
    row_count: int = 0
    chart_spec: dict[str, Any] | None = None
    results_sample: list[dict[str, Any]] | None = None
    events: list[dict[str, Any]] | None = None
    starter_id: str | None = None
    category_id: str | None = None
    feedback_rating: int | None = None
    created_at: datetime


class ChatStreamRequest(BaseModel):
    session_id: UUID
    question: str = Field(..., min_length=1, max_length=8000)
    starter_id: str | None = None
    category_id: str | None = None
    replace_turn_id: UUID | None = None


class CategoryOut(BaseModel):
    id: str
    label: str
    description: str
    icon: str
    order: int
    starter_count: int = 0
    requires_rep_code: bool = False


class StarterOut(BaseModel):
    id: str
    category_id: str
    text: str
    data_availability: str
    intent: str
    expected_table_id: str | None = None
    join_pattern: str | None = None
    source: str | None = None


class FaqCatalogOut(BaseModel):
    categories: list[CategoryOut]
    starters: list[StarterOut]


class FollowUpOut(BaseModel):
    id: str
    text: str
    data_availability: str = "full"
    intent: str | None = None


class FollowUpsResponse(BaseModel):
    follow_ups: list[FollowUpOut]
    source: str


class FollowUpsRequest(BaseModel):
    starter_id: str | None = None
    question: str | None = None
    session_id: UUID | None = None
    turn_id: UUID | None = None


class TurnFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=-1, le=1)  # -1 down, 1 up
    comment: str | None = None


class UserOut(BaseModel):
    id: UUID
    email: str | None
    display_name: str
    sales_rep_code: str | None = None


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    email: str | None = None
    sales_rep_code: str | None = None


class SalesPerformanceOut(BaseModel):
    current_fy: str
    prior_fy: str
    current_sales: float
    prior_sales: float
    yoy_pct: float


class GrossProfitSummaryOut(BaseModel):
    current_gp: float
    prior_gp: float
    current_gp_pct: float
    prior_gp_pct: float
    gp_variance_dollars: float


class MonthlyOnTrackOut(BaseModel):
    daily_avg_mtd: float
    days_completed: int
    daily_avg_needed: float
    days_remaining: int
    monthly_target: float
    closed_mtd: float
    closed_mtd_pct: float
    projected_close: float
    projected_pct: float


class YesterdaySalesOut(BaseModel):
    sales: float
    gp_dollar: float
    gp_pct: float
    fy_avg_gp_pct: float
    sales_status: str
    gp_status: str


class DailyBusinessSummaryOut(BaseModel):
    as_of_date: str
    yesterday_date: str
    disclaimer: str
    sales_performance: SalesPerformanceOut
    gross_profit: GrossProfitSummaryOut
    monthly_on_track: MonthlyOnTrackOut
    yesterday: YesterdaySalesOut
