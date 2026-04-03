import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.projects.return_value = [
            {"uuid": "p1", "title": "Project A", "status": "incomplete"}
        ]
        mock_things.get.return_value = {
            "uuid": "p1", "title": "Project A", "status": "incomplete"
        }

        from things_api.app import create_app

        app = create_app()
        yield TestClient(app)


def test_list_projects(client):
    resp = client.get("/projects", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["title"] == "Project A"


def test_get_project_by_id(client):
    resp = client.get("/projects/p1", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["uuid"] == "p1"


def test_create_project(client):
    with patch.object(
        client.app.state.writer, "create_project", new_callable=AsyncMock
    ):
        resp = client.post(
            "/projects",
            json={"title": "New Project"},
            headers=AUTH,
        )
        assert resp.status_code in (201, 202)


def test_create_project_requires_title(client):
    resp = client.post("/projects", json={}, headers=AUTH)
    assert resp.status_code == 422
