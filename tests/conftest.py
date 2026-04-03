"""Shared test fixtures."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_things():
    """Patch things.py module with common return values."""
    with patch("things_api.services.reader.things") as mock:
        mock.todos.return_value = [
            {"uuid": "t1", "title": "Buy milk", "status": "incomplete"}
        ]
        mock.get.return_value = {
            "uuid": "t1", "title": "Buy milk", "status": "incomplete"
        }
        mock.projects.return_value = [
            {"uuid": "p1", "title": "Project A", "status": "incomplete"}
        ]
        mock.inbox.return_value = [
            {"uuid": "i1", "title": "Inbox item", "status": "incomplete"}
        ]
        mock.today.return_value = [
            {"uuid": "td1", "title": "Today item", "status": "incomplete"}
        ]
        mock.upcoming.return_value = []
        mock.anytime.return_value = []
        mock.someday.return_value = []
        mock.logbook.return_value = [
            {"uuid": "l1", "title": "Done item", "status": "completed"}
        ]
        mock.tags.return_value = [{"title": "errand"}]
        mock.areas.return_value = [{"uuid": "a1", "title": "Work"}]
        mock.search.return_value = [
            {"uuid": "s1", "title": "Match", "status": "incomplete"}
        ]
        yield mock


@pytest.fixture
def auth_env(monkeypatch):
    """Set standard auth environment variables."""
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")


@pytest.fixture
def app_client(auth_env, mock_things):
    """Create a TestClient with mocked things.py and auth configured."""
    from things_api.app import create_app

    app = create_app()
    return TestClient(app)


AUTH_HEADERS = {"Authorization": "Bearer test-token"}
