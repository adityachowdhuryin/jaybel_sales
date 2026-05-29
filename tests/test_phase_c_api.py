"""Phase C API tests (Postgres required)."""

from __future__ import annotations

import os
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="Set DATABASE_URL to run Phase C API tests",
)


@pytest.fixture
def client(monkeypatch):
    from tests.conftest_backend import apply_backend_test_env

    apply_backend_test_env(monkeypatch)
    from backend.main import app

    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_sessions_crud(client: TestClient):
    r = client.post("/api/sessions", json={"title": "Test session"})
    assert r.status_code == 201
    sid = r.json()["id"]

    r = client.get("/api/sessions")
    assert r.status_code == 200
    assert any(s["id"] == sid for s in r.json())

    r = client.get(f"/api/sessions/{sid}/turns")
    assert r.status_code == 200
    assert r.json() == []

    r = client.delete(f"/api/sessions/{sid}")
    assert r.status_code == 204


def test_user_profile_patch(client: TestClient):
    r = client.patch(
        "/api/sessions/me",
        json={"sales_rep_code": "TESTREP", "display_name": "Local Developer"},
    )
    assert r.status_code == 200
    assert r.json()["sales_rep_code"] == "TESTREP"

    r = client.patch("/api/sessions/me", json={"sales_rep_code": None})
    assert r.status_code == 200
    assert r.json()["sales_rep_code"] is None


def test_chat_stream_mocked(client: TestClient):
    from backend.services import agent_engine as ae

    session_id = client.post("/api/sessions", json={}).json()["id"]

    def fake_stream(**kwargs):
        acc = ae.StreamAccumulator(question=kwargs["question"])
        acc.query_id = str(uuid4())
        acc.sql = "SELECT 1"
        acc.answer = "One row."
        acc.row_count = 1
        acc.results_sample = [{"n": 1}]
        events = [
            {"type": "status", "message": "Done"},
            {"type": "sql", "sql": "SELECT 1"},
            {
                "type": "results",
                "rows": [{"n": 1}],
                "row_count": 1,
                "columns": ["n"],
            },
            {"type": "done", "query_id": acc.query_id, "session_id": "x"},
        ]
        for ev in events:
            acc.events.append(ev)
            yield ev, acc

    with patch.object(ae, "create_agent_session", return_value="ae-sess-1"):
        with patch.object(ae, "stream_chat", side_effect=fake_stream):
            r = client.post(
                "/api/chat/stream",
                json={"session_id": session_id, "question": "test?"},
            )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers.get("content-type", "")
    assert "data:" in r.text
    assert '"type": "sql"' in r.text or '"type": "done"' in r.text

    turns = client.get(f"/api/sessions/{session_id}/turns").json()
    assert len(turns) == 1
    assert turns[0]["question"] == "test?"
