"""Vertex AI Agent Engine streaming → UI SSE events."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Iterator

import vertexai
from vertexai import agent_engines

from backend.config import settings

logger = logging.getLogger(__name__)

SALES_PREFIX = "SALES_ANALYTICS_JSON:"

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        s = settings()
        vertexai.init(project=s["gcp_project"], location=s["gcp_location"])
        _engine = agent_engines.get(s["agent_engine_resource"])
    return _engine


def create_agent_session(user_id: str) -> str:
    engine = get_engine()
    session = engine.create_session(user_id=user_id)
    return session["id"]


@dataclass
class StreamAccumulator:
    """Collect turn fields while streaming for Postgres persistence."""

    question: str
    starter_id: str | None = None
    category_id: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    query_id: str | None = None
    intent: str | None = None
    table_id: str | None = None
    join_pattern: str | None = None
    sql: str | None = None
    answer: str | None = None
    row_count: int = 0
    chart_spec: dict[str, Any] | None = None
    results_sample: list[dict[str, Any]] | None = None
    agent_text: str = ""

    def absorb_tool_payload(self, payload: dict[str, Any]) -> None:
        self.query_id = payload.get("query_id") or self.query_id
        self.intent = payload.get("intent") or self.intent
        self.table_id = payload.get("table_id") or self.table_id
        self.join_pattern = payload.get("join_pattern") or self.join_pattern
        self.sql = payload.get("sql") or self.sql
        self.answer = payload.get("answer") or self.answer
        self.row_count = payload.get("row_count") or self.row_count
        self.chart_spec = payload.get("chart_spec") or self.chart_spec
        self.results_sample = payload.get("rows_sample") or self.results_sample

    def to_turn_record(self) -> dict[str, Any]:
        answer = self.answer or self.agent_text.strip() or None
        return {
            "query_id": self.query_id or "",
            "question": self.question,
            "starter_id": self.starter_id,
            "category_id": self.category_id,
            "intent": self.intent,
            "table_id": self.table_id,
            "join_pattern": self.join_pattern,
            "sql": self.sql,
            "answer": answer,
            "row_count": self.row_count,
            "chart_spec": self.chart_spec,
            "results_sample": self.results_sample,
            "events": self.events,
        }


def _extract_parts(raw: dict[str, Any]) -> list[dict[str, Any]]:
    content = raw.get("content") or {}
    parts = content.get("parts") or []
    return [p for p in parts if isinstance(p, dict)]


def _parse_sales_json(result: str) -> dict[str, Any] | None:
    if not isinstance(result, str) or not result.startswith(SALES_PREFIX):
        return None
    try:
        return json.loads(result[len(SALES_PREFIX) :])
    except json.JSONDecodeError:
        logger.warning("Failed to parse tool JSON payload")
        return None


def raw_event_to_ui_events(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Map one Agent Engine stream chunk to zero or more UI events."""
    out: list[dict[str, Any]] = []
    for part in _extract_parts(raw):
        if "function_response" in part:
            fr = part["function_response"]
            resp = fr.get("response") or {}
            result = resp.get("result") if isinstance(resp, dict) else resp
            payload = _parse_sales_json(result) if isinstance(result, str) else None
            if payload:
                for ev in payload.get("events") or []:
                    if isinstance(ev, dict) and ev.get("type"):
                        out.append(ev)
        text = part.get("text")
        if text and isinstance(text, str) and text.strip():
            out.append({"type": "token", "text": text})
    return out


def build_message(
    question: str,
    sales_rep_code: str | None,
    history: list[dict[str, Any]] | None = None,
    *,
    starter_id: str | None = None,
    category_id: str | None = None,
) -> str:
    ctx: dict[str, Any] = {}
    if history:
        ctx["history"] = history
        ctx["history_json"] = json.dumps(history, ensure_ascii=False)
    if sales_rep_code:
        ctx["sales_rep_code"] = sales_rep_code
    if starter_id:
        ctx["starter_id"] = starter_id
    if category_id:
        ctx["category_id"] = category_id
    prefix = ""
    if ctx:
        prefix = f"[SALES_CONTEXT]{json.dumps(ctx, ensure_ascii=False)}[/SALES_CONTEXT]\n\n"
    return f"{prefix}{question}"


def stream_chat(
    *,
    user_id: str,
    agent_session_id: str,
    question: str,
    sales_rep_code: str | None = None,
    history: list[dict[str, Any]] | None = None,
    starter_id: str | None = None,
    category_id: str | None = None,
) -> Iterator[tuple[dict[str, Any], StreamAccumulator]]:
    """
    Yield (ui_event, accumulator) for each mapped event.
    Accumulator is the same object across yields; mutate until stream ends.
    """
    engine = get_engine()
    acc = StreamAccumulator(
        question=question,
        starter_id=starter_id,
        category_id=category_id,
    )
    message = build_message(
        question,
        sales_rep_code,
        history,
        starter_id=starter_id,
        category_id=category_id,
    )

    for raw in engine.stream_query(
        user_id=user_id,
        session_id=agent_session_id,
        message=message,
    ):
        if not isinstance(raw, dict):
            continue
        for part in _extract_parts(raw):
            if "function_response" in part:
                fr = part["function_response"]
                resp = fr.get("response") or {}
                result = resp.get("result") if isinstance(resp, dict) else resp
                payload = _parse_sales_json(result) if isinstance(result, str) else None
                if payload:
                    acc.absorb_tool_payload(payload)
            text = part.get("text")
            if text and isinstance(text, str):
                acc.agent_text += text

        ui_events = raw_event_to_ui_events(raw)
        for ev in ui_events:
            acc.events.append(ev)
            yield ev, acc

    if not any(e.get("type") == "done" for e in acc.events):
        done_ev = {
            "type": "done",
            "session_id": agent_session_id,
            "query_id": acc.query_id or "",
        }
        acc.events.append(done_ev)
        yield done_ev, acc
