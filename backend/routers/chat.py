"""Chat SSE — proxy Agent Engine stream, persist turns."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.config import settings
from backend.db import postgres as db
from backend.schemas import ChatStreamRequest
from backend.services import agent_engine as ae

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def _sse_line(event: dict) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


def _title_from_question(question: str, max_len: int = 60) -> str:
    q = question.strip().replace("\n", " ")
    return q[:max_len] + ("…" if len(q) > max_len else "")


@router.post("/stream")
def chat_stream(body: ChatStreamRequest) -> StreamingResponse:
    user_id = settings()["default_user_id"]
    session_id = str(body.session_id)

    try:
        session = db.get_session(session_id, user_id)
        user = db.get_user(user_id)
    except LookupError:
        raise HTTPException(404, "Session not found") from None

    ae_session_id = session.get("agent_engine_session_id")
    if not ae_session_id:
        try:
            ae_session_id = ae.create_agent_session(user_id)
            db.set_agent_engine_session_id(session_id, ae_session_id)
        except Exception as exc:
            logger.exception("create_agent_session failed")
            raise HTTPException(502, f"Agent Engine unavailable: {exc}") from exc

    history = db.build_history(session_id, limit=5)

    def generate():
        acc = None
        try:
            for ev, accumulator in ae.stream_chat(
                user_id=user_id,
                agent_session_id=ae_session_id,
                question=body.question,
                sales_rep_code=user.get("sales_rep_code"),
                history=history,
                starter_id=body.starter_id,
                category_id=body.category_id,
            ):
                acc = accumulator
                if ev.get("type") != "done":
                    yield _sse_line(ev)

            if acc:
                row = db.insert_turn(session_id, acc.to_turn_record())
                if body.starter_id or body.category_id:
                    db.update_session_ui_context(
                        session_id,
                        {
                            "last_starter_id": body.starter_id,
                            "last_category_id": body.category_id,
                        },
                    )
                if session["title"] == "New chat":
                    db.touch_session(session_id, title=_title_from_question(body.question))
                else:
                    db.touch_session(session_id)
                yield _sse_line(
                    {
                        "type": "done",
                        "session_id": session_id,
                        "query_id": acc.query_id or "",
                        "turn_id": str(row["id"]),
                    }
                )
        except Exception as exc:
            logger.exception("chat stream failed")
            yield _sse_line(
                {"type": "error", "code": "stream_failed", "message": str(exc)}
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
