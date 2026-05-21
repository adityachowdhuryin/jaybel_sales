import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests that call live GCP (BigQuery / Vertex)",
    )
