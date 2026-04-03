import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.inbox.return_value = []

        from things_api.app import create_app

        app = create_app()
        yield TestClient(app)


def test_rate_limiter_allows_valid_requests(client):
    for _ in range(15):
        resp = client.get("/health", headers={"Authorization": "Bearer test-token"})
        assert resp.status_code == 200


def test_rate_limiter_blocks_after_too_many_failures(client):
    for _ in range(10):
        resp = client.get("/health", headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401

    resp = client.get("/health", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
