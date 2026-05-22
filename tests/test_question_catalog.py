"""Question catalog API tests."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="Set DATABASE_URL to run API tests",
)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            "postgresql://jaybel:jaybel_local_dev@127.0.0.1:15433/jaybel_sales_app",
        ),
    )
    from backend.config import settings

    settings.cache_clear()
    from backend.main import app

    return TestClient(app)


def test_categories(client: TestClient):
    r = client.get("/api/question-catalog/categories")
    assert r.status_code == 200
    cats = r.json()
    assert len(cats) >= 10
    assert any(c["id"] == "executive_kpi" for c in cats)


def test_starters_for_category(client: TestClient):
    r = client.get("/api/question-catalog/categories/executive_kpi/starters")
    assert r.status_code == 200
    starters = r.json()
    assert len(starters) >= 1
    assert starters[0]["category_id"] == "executive_kpi"


def test_search_starters(client: TestClient):
    r = client.get("/api/question-catalog/search", params={"q": "fiscal year"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_follow_ups_curated(client: TestClient):
    r = client.get("/api/question-catalog/follow-ups", params={"starter_id": "Q061"})
    assert r.status_code == 200
    body = r.json()
    assert "follow_ups" in body
    assert body["source"] in ("curated", "rules", "none")
