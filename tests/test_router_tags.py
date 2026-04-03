import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.tags.return_value = [{"title": "errand"}]

        from things_api.app import create_app

        app = create_app()
        yield TestClient(app)


def test_list_tags(client):
    resp = client.get("/tags", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "errand"


def test_tag_items(client):
    resp = client.get("/tags/errand/items", headers=AUTH)
    assert resp.status_code == 200


def test_tags_requires_auth(client):
    resp = client.get("/tags")
    assert resp.status_code == 401
