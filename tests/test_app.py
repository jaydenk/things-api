import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.inbox.return_value = []

        from things_api.app import create_app

        app = create_app()
        yield TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["read"] is True
    assert data["write"] is True


def test_health_degraded_when_db_fails(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.inbox.side_effect = Exception("DB not found")

        from things_api.app import create_app

        app = create_app()
        client = TestClient(app)

        resp = client.get("/health", headers={"Authorization": "Bearer test-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["read"] is False


def test_health_requires_auth(client):
    resp = client.get("/health")
    assert resp.status_code == 401


def test_docs_disabled(client):
    resp = client.get("/docs", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 404
