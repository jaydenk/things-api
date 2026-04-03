import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    from things_api.app import create_app

    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["read"] is True
    assert data["write"] is True


def test_health_requires_auth(client):
    resp = client.get("/health")
    assert resp.status_code == 401


def test_openapi_docs_accessible(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
