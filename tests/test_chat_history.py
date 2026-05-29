"""Chat stream passes conversation history to Agent Engine."""

from __future__ import annotations

import json
import os
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="Set DATABASE_URL to run API tests",
)


@pytest.fixture
def client(monkeypatch):
    from tests.conftest_backend import apply_backend_test_env

    apply_backend_test_env(monkeypatch)
    from backend.main import app

    return TestClient(app)


def test_build_message_includes_history():
    from backend.services import agent_engine as ae

    hist = [{"question": "prior?", "answer_summary": "yes"}]
    msg = ae.build_message("follow up", "REP1", hist, starter_id="Q001", category_id="sales")
    assert "[SALES_CONTEXT]" in msg
    ctx = json.loads(msg.split("[SALES_CONTEXT]")[1].split("[/SALES_CONTEXT]")[0])
    assert ctx["history"] == hist
    assert ctx["sales_rep_code"] == "REP1"
    assert ctx["starter_id"] == "Q001"
    assert "follow up" in msg


def test_chat_stream_passes_history(client: TestClient):
    from backend.db import postgres as db
    from backend.services import agent_engine as ae

    session_id = client.post("/api/sessions", json={}).json()["id"]
    db.insert_turn(
        session_id,
        {
            "query_id": str(uuid4()),
            "question": "first question",
            "answer": "first answer",
            "table_id": "fact_sales_report",
            "intent": "aggregation",
        },
    )

    captured: dict = {}

    def fake_stream(**kwargs):
        captured.update(kwargs)
        acc = ae.StreamAccumulator(
            question=kwargs["question"],
            starter_id=kwargs.get("starter_id"),
            category_id=kwargs.get("category_id"),
        )
        acc.query_id = str(uuid4())
        acc.answer = "ok"
        ev = {"type": "done", "query_id": acc.query_id, "session_id": "x"}
        acc.events.append(ev)
        yield ev, acc

    with patch.object(ae, "create_agent_session", return_value="ae-sess-hist"):
        with patch.object(ae, "stream_chat", side_effect=fake_stream):
            r = client.post(
                "/api/chat/stream",
                json={
                    "session_id": session_id,
                    "question": "second question",
                    "starter_id": "Q002",
                    "category_id": "sales_revenue",
                },
            )
    assert r.status_code == 200
    assert captured.get("history")
    assert len(captured["history"]) == 1
    assert captured["history"][0]["question"] == "first question"
    assert captured.get("starter_id") == "Q002"

    assert '"turn_id"' in r.text or "turn_id" in r.text

    turns = client.get(f"/api/sessions/{session_id}/turns").json()
    assert len(turns) == 2
    assert turns[1]["starter_id"] == "Q002"


def test_follow_ups_use_ui_context(client: TestClient):
    from backend.db import postgres as db

    session_id = client.post("/api/sessions", json={}).json()["id"]
    db.update_session_ui_context(
        session_id, {"last_starter_id": "Q061", "last_category_id": "executive_kpi"}
    )
    r = client.get(
        "/api/question-catalog/follow-ups",
        params={"session_id": session_id, "question": "unmatched free text"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["source"] in ("curated", "rules", "none")


def test_agent_parses_sales_context():
    from agent.sales_analytics_agent.agent import _parse_sales_context

    q = '[SALES_CONTEXT]{"history":[{"question":"x"}]}[/SALES_CONTEXT]\n\nWhat next?'
    clean, ctx = _parse_sales_context(q)
    assert clean == "What next?"
    assert ctx["history"][0]["question"] == "x"
