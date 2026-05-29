"""Shared env for FastAPI API tests."""

from __future__ import annotations

import os


def apply_backend_test_env(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            "postgresql://jaybel:jaybel_local_dev@127.0.0.1:15433/jaybel_sales_app",
        ),
    )
    monkeypatch.setenv(
        "AGENT_ENGINE_RESOURCE",
        os.getenv(
            "AGENT_ENGINE_RESOURCE",
            "projects/115724636423/locations/us-central1/reasoningEngines/8991351443894042624",
        ),
    )
    monkeypatch.setenv("AUTH_DISABLED", "true")
    monkeypatch.setenv(
        "DEFAULT_USER_ID", "00000000-0000-4000-8000-000000000001"
    )
    from backend.config import settings

    settings.cache_clear()
