from unittest.mock import patch
import pytest

from things_api.services.reader import ThingsReader


@pytest.fixture
def reader():
    return ThingsReader(db_path=None)


@patch("things_api.services.reader.things")
def test_get_todos(mock_things, reader):
    mock_things.todos.return_value = [
        {"uuid": "abc", "title": "Buy milk", "status": "incomplete"}
    ]
    result = reader.todos()
    assert len(result) == 1
    assert result[0]["title"] == "Buy milk"
    mock_things.todos.assert_called_once()


@patch("things_api.services.reader.things")
def test_get_todos_with_project_filter(mock_things, reader):
    mock_things.todos.return_value = []
    reader.todos(project="proj-uuid")
    mock_things.todos.assert_called_once_with(project="proj-uuid")


@patch("things_api.services.reader.things")
def test_get_by_uuid(mock_things, reader):
    mock_things.get.return_value = {"uuid": "abc", "title": "Test"}
    result = reader.get("abc")
    assert result["uuid"] == "abc"


@patch("things_api.services.reader.things")
def test_get_by_uuid_not_found(mock_things, reader):
    mock_things.get.return_value = None
    result = reader.get("nonexistent")
    assert result is None


@patch("things_api.services.reader.things")
def test_inbox(mock_things, reader):
    mock_things.inbox.return_value = [{"uuid": "x", "title": "Inbox item"}]
    result = reader.inbox()
    assert len(result) == 1


@patch("things_api.services.reader.things")
def test_today(mock_things, reader):
    mock_things.today.return_value = []
    result = reader.today()
    assert result == []


@patch("things_api.services.reader.things")
def test_projects(mock_things, reader):
    mock_things.projects.return_value = [
        {"uuid": "p1", "title": "Project A"}
    ]
    result = reader.projects()
    assert result[0]["title"] == "Project A"


@patch("things_api.services.reader.things")
def test_search(mock_things, reader):
    mock_things.search.return_value = [{"uuid": "s1", "title": "Match"}]
    result = reader.search("Match")
    assert len(result) == 1
    mock_things.search.assert_called_once_with("Match")


@patch("things_api.services.reader.things")
def test_tags(mock_things, reader):
    mock_things.tags.return_value = [{"title": "errand"}]
    result = reader.tags()
    assert result[0]["title"] == "errand"


@patch("things_api.services.reader.things")
def test_areas(mock_things, reader):
    mock_things.areas.return_value = [{"uuid": "a1", "title": "Work"}]
    result = reader.areas()
    assert result[0]["title"] == "Work"


@patch("things_api.services.reader.things")
def test_db_path_passed(mock_things):
    reader = ThingsReader(db_path="/custom/path.sqlite3")
    mock_things.todos.return_value = []
    reader.todos()
    mock_things.todos.assert_called_once_with(filepath="/custom/path.sqlite3")
