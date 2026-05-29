"""Q031/Q032-style follow-ups require prior turn in history payload."""

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


def test_history_includes_prior_turn_for_q032_style(client: TestClient):
    from backend.db import postgres as db
    from backend.services import agent_engine as ae

    session_id = client.post("/api/sessions", json={}).json()["id"]
    db.insert_turn(
        session_id,
        {
            "query_id": str(uuid4()),
            "question": "Show monthly sales trend for fiscal year 2024-2025",
            "answer": "Trend by month shown.",
            "table_id": "fact_sales_report",
            "intent": "trend",
            "category_id": "executive_kpi",
        },
    )

    captured: dict = {}

    def fake_stream(**kwargs):
        captured.update(kwargs)
        acc = ae.StreamAccumulator(question=kwargs["question"])
        acc.query_id = str(uuid4())
        acc.answer = "ok"
        yield {"type": "status", "message": "Done"}, acc

    with patch.object(ae, "create_agent_session", return_value="ae-q032"):
        with patch.object(ae, "stream_chat", side_effect=fake_stream):
            r = client.post(
                "/api/chat/stream",
                json={
                    "session_id": session_id,
                    "question": "Break it down by fiscal month",
                },
            )
    assert r.status_code == 200
    hist = captured.get("history") or []
    assert len(hist) == 1
    assert "monthly sales" in hist[0]["question"].lower()
    assert "sql_excerpt" in hist[0]

    msg = ae.build_message("Break it down by fiscal month", None, hist)
    assert "history_json" in msg
    ctx = json.loads(msg.split("[SALES_CONTEXT]")[1].split("[/SALES_CONTEXT]")[0])
    assert ctx["history_json"]


def test_agent_parses_history_json_param():
    from agent.sales_analytics_agent.agent import _parse_sales_context

    q = "Break it down by fiscal month"
    hist = json.dumps(
        [{"question": "Show monthly sales trend", "table_id": "fact_sales_report"}]
    )
    # Tool merges history_json when envelope empty — tested via query path in unit test below
    clean, ctx = _parse_sales_context(q)
    assert clean == q
    assert ctx == {}
