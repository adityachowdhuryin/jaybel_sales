"""Session CRUD — local Postgres."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from backend.config import settings
from backend.db import postgres as db
from backend.schemas import (
    SessionCreate,
    SessionOut,
    TurnFeedbackRequest,
    TurnOut,
    UserOut,
    UserProfileUpdate,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _user_id() -> str:
    return settings()["default_user_id"]


@router.get("/me", response_model=UserOut)
def get_me() -> UserOut:
    user = db.get_user(_user_id())
    return UserOut(**user)


@router.patch("/me", response_model=UserOut)
def update_me(body: UserProfileUpdate) -> UserOut:
    data = body.model_dump(exclude_unset=True)
    user = db.update_user_profile(_user_id(), **data)
    return UserOut(**user)


@router.get("", response_model=list[SessionOut])
def list_sessions(q: str | None = Query(None, min_length=0)) -> list[SessionOut]:
    rows = db.list_sessions(_user_id(), search=q)
    return [SessionOut(**r) for r in rows]


@router.post("", response_model=SessionOut, status_code=201)
def create_session(body: SessionCreate | None = None) -> SessionOut:
    title = (body.title if body else None) or "New chat"
    row = db.create_session(_user_id(), title=title)
    return SessionOut(**row)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: UUID) -> SessionOut:
    try:
        row = db.get_session(str(session_id), _user_id())
    except LookupError:
        raise HTTPException(404, "Session not found") from None
    return SessionOut(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/{session_id}/turns", response_model=list[TurnOut])
def list_turns(session_id: UUID) -> list[TurnOut]:
    try:
        db.get_session(str(session_id), _user_id())
    except LookupError:
        raise HTTPException(404, "Session not found") from None
    rows = db.list_turns(str(session_id))
    out = []
    for r in rows:
        out.append(
            TurnOut(
                id=r["id"],
                query_id=r["query_id"],
                question=r["question"],
                intent=r.get("intent"),
                table_id=r.get("table_id"),
                join_pattern=r.get("join_pattern"),
                sql=r.get("sql"),
                answer=r.get("answer"),
                row_count=r.get("row_count") or 0,
                chart_spec=r.get("chart_spec"),
                results_sample=r.get("results_sample"),
                events=r.get("events"),
                starter_id=r.get("starter_id"),
                category_id=r.get("category_id"),
                feedback_rating=r.get("feedback_rating"),
                created_at=r["created_at"],
            )
        )
    return out


@router.post("/{session_id}/turns/{turn_id}/feedback", status_code=204)
def turn_feedback(
    session_id: UUID, turn_id: UUID, body: TurnFeedbackRequest
) -> None:
    try:
        db.get_session(str(session_id), _user_id())
        db.update_turn_feedback(str(session_id), str(turn_id), body.rating, body.comment)
    except LookupError:
        raise HTTPException(404, "Session or turn not found") from None


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: UUID) -> None:
    try:
        db.delete_session(str(session_id), _user_id())
    except LookupError:
        raise HTTPException(404, "Session not found") from None
