import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.inbox.return_value = [
            {"uuid": "i1", "title": "Inbox item", "status": "incomplete"}
        ]
        mock_things.today.return_value = [
            {"uuid": "t1", "title": "Today item", "status": "incomplete"}
        ]
        mock_things.upcoming.return_value = []
        mock_things.anytime.return_value = []
        mock_things.someday.return_value = []
        mock_things.logbook.return_value = [
            {"uuid": "l1", "title": "Done item", "status": "completed"}
        ]

        from things_api.app import create_app

        app = create_app()
        yield TestClient(app)


def test_inbox(client):
    resp = client.get("/inbox", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Inbox item"


def test_today(client):
    resp = client.get("/today", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Today item"


def test_upcoming(client):
    resp = client.get("/upcoming", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == []


def test_anytime(client):
    resp = client.get("/anytime", headers=AUTH)
    assert resp.status_code == 200


def test_someday(client):
    resp = client.get("/someday", headers=AUTH)
    assert resp.status_code == 200


def test_logbook(client):
    resp = client.get("/logbook", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Done item"


def test_logbook_requires_auth(client):
    resp = client.get("/logbook")
    assert resp.status_code == 401
