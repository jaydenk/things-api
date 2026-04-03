import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.todos.return_value = [
            {"uuid": "t1", "title": "Buy milk", "status": "incomplete"}
        ]
        mock_things.get.return_value = {
            "uuid": "t1", "title": "Buy milk", "status": "incomplete"
        }
        mock_things.inbox.return_value = []

        from things_api.app import create_app

        app = create_app()
        yield TestClient(app)


def test_list_todos(client):
    resp = client.get("/todos", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["title"] == "Buy milk"


def test_get_todo_by_id(client):
    resp = client.get("/todos/t1", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["uuid"] == "t1"


def test_create_todo(client):
    with patch.object(
        client.app.state.writer, "create_todo", new_callable=AsyncMock
    ):
        resp = client.post(
            "/todos",
            json={"title": "New task"},
            headers=AUTH,
        )
        assert resp.status_code == 202
        assert resp.json()["status"] == "accepted"


def test_create_todo_requires_title(client):
    resp = client.post("/todos", json={}, headers=AUTH)
    assert resp.status_code == 422
