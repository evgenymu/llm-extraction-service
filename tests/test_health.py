"""Tests for the health endpoint."""

from importlib.metadata import version

from fastapi.testclient import TestClient

from llm_extraction_service.main import app

client = TestClient(app)


def test_health_returns_ok_and_the_running_version() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": version("llm-extraction-service"),
    }
