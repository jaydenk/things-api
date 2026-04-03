import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.search.return_value = [
            {"uuid": "s1", "title": "Match", "status": "incomplete"}
        ]
        mock_things.todos.return_value = [
            {"uuid": "t1", "title": "Tagged", "status": "incomplete"}
        ]

        from things_api.app import create_app

        app = create_app()
        yield TestClient(app)


def test_search(client):
    resp = client.get("/search?q=Match", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Match"


def test_search_empty_query(client):
    resp = client.get("/search?q=", headers=AUTH)
    assert resp.status_code == 400


def test_advanced_search(client):
    resp = client.get("/search/advanced?tag=errand", headers=AUTH)
    assert resp.status_code == 200


def test_search_requires_auth(client):
    resp = client.get("/search?q=test")
    assert resp.status_code == 401
