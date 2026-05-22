"""Question catalog API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from backend.db import postgres as db
from backend.config import settings
from backend.schemas import (
    CategoryOut,
    FollowUpOut,
    FollowUpsRequest,
    FollowUpsResponse,
    StarterOut,
)
from backend.services import question_catalog as qc

router = APIRouter(prefix="/api/question-catalog", tags=["question-catalog"])


def _resolve_follow_ups_payload(
    *,
    starter_id: str | None,
    question: str | None,
    session_id: UUID | None,
    turn_id: UUID | None,
) -> FollowUpsResponse:
    last_turn = None
    ui_context: dict | None = None
    if session_id:
        try:
            session = db.get_session(str(session_id), settings()["default_user_id"])
            raw_ctx = session.get("ui_context")
            if isinstance(raw_ctx, dict):
                ui_context = raw_ctx
            elif raw_ctx:
                import json

                ui_context = json.loads(raw_ctx) if isinstance(raw_ctx, str) else {}
            if turn_id:
                turns = db.list_turns(str(session_id))
                for t in turns:
                    if str(t["id"]) == str(turn_id):
                        last_turn = t
                        break
        except LookupError:
            raise HTTPException(404, "Session not found") from None

    items, source = qc.resolve_follow_ups(
        starter_id=starter_id,
        question=question,
        last_turn=last_turn,
        ui_context=ui_context,
    )
    return FollowUpsResponse(
        follow_ups=[FollowUpOut(**f) for f in items],
        source=source,
    )


@router.get("/categories", response_model=list[CategoryOut])
def get_categories() -> list[CategoryOut]:
    return [CategoryOut(**c) for c in qc.list_categories()]


@router.get("/categories/{category_id}/starters", response_model=list[StarterOut])
def get_starters(category_id: str) -> list[StarterOut]:
    items = qc.starters_for_category(category_id)
    if not items and category_id not in {c["id"] for c in qc.list_categories()}:
        raise HTTPException(404, "Category not found")
    return [StarterOut(**s) for s in items]


@router.get("/search", response_model=list[StarterOut])
def search_starters(
    q: str = Query("", min_length=0),
    category_id: str | None = None,
    table_id: str | None = None,
    intent: str | None = None,
) -> list[StarterOut]:
    return [
        StarterOut(**s)
        for s in qc.search_starters(
            q, limit=30, category_id=category_id, table_id=table_id, intent=intent
        )
    ]


@router.get("/follow-ups", response_model=FollowUpsResponse)
def get_follow_ups(
    starter_id: str | None = None,
    question: str | None = None,
    session_id: UUID | None = None,
    turn_id: UUID | None = None,
) -> FollowUpsResponse:
    return _resolve_follow_ups_payload(
        starter_id=starter_id,
        question=question,
        session_id=session_id,
        turn_id=turn_id,
    )


@router.post("/follow-ups", response_model=FollowUpsResponse)
def post_follow_ups(body: FollowUpsRequest) -> FollowUpsResponse:
    return _resolve_follow_ups_payload(
        starter_id=body.starter_id,
        question=body.question,
        session_id=body.session_id,
        turn_id=body.turn_id,
    )
