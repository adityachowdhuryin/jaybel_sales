"""Config alignment with local Postgres stack (Phase C prep)."""

from pipeline.config import (
    api_base_url,
    auth_provider,
    default_user_email,
    default_user_id,
    local_database_url,
)


def test_local_auth_config():
    assert auth_provider() == "local_postgres"
    assert default_user_email() == "dev@localhost"
    assert default_user_id() == "00000000-0000-4000-8000-000000000001"


def test_local_app_urls():
    assert "localhost:5432" in local_database_url()
    assert api_base_url() == "http://localhost:8000"
