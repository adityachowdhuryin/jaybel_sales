"""PostgreSQL access for sessions and turns."""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator

import psycopg
from psycopg.rows import dict_row

from backend.config import settings


@contextmanager
def get_conn() -> Generator[psycopg.Connection, None, None]:
    with psycopg.connect(settings()["database_url"], row_factory=dict_row) as conn:
        yield conn


def update_user_profile(user_id: str, **fields: Any) -> dict[str, Any]:
    allowed = {"sales_rep_code", "display_name", "email"}
    sets: list[str] = []
    params: list[Any] = []
    for key, val in fields.items():
        if key not in allowed:
            continue
        sets.append(f"{key} = %s")
        params.append(val if val != "" else (None if key == "sales_rep_code" else val))
    if not sets:
        return get_user(user_id)
    params.append(user_id)
    with get_conn() as conn:
        row = conn.execute(
            f"UPDATE users SET {', '.join(sets)} WHERE id = %s "
            "RETURNING id, email, display_name, sales_rep_code",
            params,
        ).fetchone()
        conn.commit()
    return dict(row)


def get_user(user_id: str | None = None) -> dict[str, Any]:
    uid = user_id or settings()["default_user_id"]
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, display_name, sales_rep_code FROM users WHERE id = %s",
            (uid,),
        ).fetchone()
    if not row:
        raise LookupError(f"User not found: {uid}")
    return dict(row)


def list_sessions(user_id: str, search: str | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        if search and search.strip():
            q = f"%{search.strip()}%"
            rows = conn.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM chat_sessions
                WHERE user_id = %s AND title ILIKE %s
                ORDER BY updated_at DESC
                """,
                (user_id, q),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM chat_sessions
                WHERE user_id = %s
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
    return [dict(r) for r in rows]


def create_session(user_id: str, title: str = "New chat") -> dict[str, Any]:
    sid = str(uuid.uuid4())
    with get_conn() as conn:
        row = conn.execute(
            """
            INSERT INTO chat_sessions (id, user_id, title)
            VALUES (%s, %s, %s)
            RETURNING id, title, created_at, updated_at
            """,
            (sid, user_id, title),
        ).fetchone()
        conn.commit()
    return dict(row)


def get_session(session_id: str, user_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, title, created_at, updated_at, agent_engine_session_id, ui_context
            FROM chat_sessions
            WHERE id = %s AND user_id = %s
            """,
            (session_id, user_id),
        ).fetchone()
    if not row:
        raise LookupError("Session not found")
    return dict(row)


def delete_session(session_id: str, user_id: str) -> None:
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM chat_sessions WHERE id = %s AND user_id = %s",
            (session_id, user_id),
        )
        conn.commit()
    if cur.rowcount == 0:
        raise LookupError("Session not found")


def set_agent_engine_session_id(session_id: str, ae_session_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE chat_sessions
            SET agent_engine_session_id = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (ae_session_id, session_id),
        )
        conn.commit()


def touch_session(session_id: str, title: str | None = None) -> None:
    with get_conn() as conn:
        if title:
            conn.execute(
                """
                UPDATE chat_sessions SET updated_at = NOW(), title = %s WHERE id = %s
                """,
                (title, session_id),
            )
        else:
            conn.execute(
                "UPDATE chat_sessions SET updated_at = NOW() WHERE id = %s",
                (session_id,),
            )
        conn.commit()


def list_turns(session_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, query_id, question, intent, table_id, join_pattern, sql, answer,
                   row_count, chart_spec, results_sample, events,
                   starter_id, category_id, feedback_rating, created_at
            FROM chat_turns
            WHERE session_id = %s
            ORDER BY created_at ASC
            """,
            (session_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_turn(session_id: str, turn_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, query_id, question, intent, table_id, join_pattern, sql, answer,
                   row_count, chart_spec, results_sample, events,
                   starter_id, category_id, feedback_rating, created_at
            FROM chat_turns
            WHERE session_id = %s AND id = %s
            """,
            (session_id, turn_id),
        ).fetchone()
    if not row:
        raise LookupError("Turn not found")
    return dict(row)


def update_turn_feedback(
    session_id: str, turn_id: str, rating: int, comment: str | None = None
) -> None:
    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE chat_turns
            SET feedback_rating = %s, feedback_comment = %s
            WHERE session_id = %s AND id = %s
            """,
            (rating, comment, session_id, turn_id),
        )
        conn.commit()
    if cur.rowcount == 0:
        raise LookupError("Turn not found")


def update_session_ui_context(session_id: str, context: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE chat_sessions SET ui_context = %s::jsonb, updated_at = NOW()
            WHERE id = %s
            """,
            (json.dumps(context), session_id),
        )
        conn.commit()


def build_history(session_id: str, limit: int = 5) -> list[dict[str, Any]]:
    from pipeline.followup_sql_context import extract_filter_summary, extract_metric_from_sql

    turns = list_turns(session_id)
    recent = turns[-limit:] if len(turns) > limit else turns
    history = []
    for t in recent:
        answer = t.get("answer") or ""
        sql = t.get("sql") or ""
        history.append(
            {
                "question": t["question"],
                "table_id": t.get("table_id"),
                "intent": t.get("intent"),
                "join_pattern": t.get("join_pattern"),
                "time_range_label": None,
                "sql_excerpt": sql[:400] if sql else "",
                "answer_summary": answer[:200] if answer else "",
                "row_count": t.get("row_count"),
                "category_id": t.get("category_id"),
                "metric_hint": extract_metric_from_sql(sql) if sql else None,
                "filter_summary": extract_filter_summary(sql) if sql else None,
            }
        )
    return history


def insert_turn(session_id: str, turn: dict[str, Any]) -> dict[str, Any]:
    tid = str(uuid.uuid4())
    with get_conn() as conn:
        row = conn.execute(
            """
            INSERT INTO chat_turns (
                id, session_id, query_id, question, intent, table_id, join_pattern,
                sql, answer, row_count, chart_spec, results_sample, events,
                starter_id, category_id
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id, created_at
            """,
            (
                tid,
                session_id,
                turn.get("query_id") or str(uuid.uuid4()),
                turn["question"],
                turn.get("intent"),
                turn.get("table_id"),
                turn.get("join_pattern"),
                turn.get("sql"),
                turn.get("answer"),
                turn.get("row_count", 0),
                json.dumps(turn["chart_spec"]) if turn.get("chart_spec") else None,
                json.dumps(turn.get("results_sample") or []),
                json.dumps(turn.get("events") or []),
                turn.get("starter_id"),
                turn.get("category_id"),
            ),
        ).fetchone()
        conn.commit()
    out = dict(row)
    out["session_id"] = session_id
    return out
