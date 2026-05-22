"""Backend settings from environment."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv()  # cwd override


@lru_cache(maxsize=1)
def settings() -> dict[str, str]:
    return {
        "database_url": os.environ["DATABASE_URL"],
        "gcp_project": os.getenv("GOOGLE_CLOUD_PROJECT", "jaybel-dev"),
        "gcp_location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        "agent_engine_resource": os.environ["AGENT_ENGINE_RESOURCE"],
        "default_user_id": os.getenv(
            "DEFAULT_USER_ID", "00000000-0000-4000-8000-000000000001"
        ),
        "api_host": os.getenv("API_HOST", "127.0.0.1"),
        "api_port": os.getenv("API_PORT", "8000"),
        "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:3000"),
    }


def cors_origin_list() -> list[str]:
    return [o.strip() for o in settings()["cors_origins"].split(",") if o.strip()]
