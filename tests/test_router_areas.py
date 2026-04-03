import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.areas.return_value = [
            {"uuid": "a1", "title": "Work"}
        ]

        from things_api.app import create_app

        app = create_app()
        yield TestClient(app)


def test_list_areas(client):
    resp = client.get("/areas", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Work"


def test_areas_requires_auth(client):
    resp = client.get("/areas")
    assert resp.status_code == 401
