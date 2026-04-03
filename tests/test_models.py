import pytest
from pydantic import ValidationError

from things_api.models import (
    CreateTodoRequest,
    UpdateTodoRequest,
    CreateProjectRequest,
    DeleteAction,
    DeleteRequest,
    TodoResponse,
    ProjectResponse,
    HealthResponse,
)


def test_create_todo_minimal():
    req = CreateTodoRequest(title="Buy milk")
    assert req.title == "Buy milk"
    assert req.when is None
    assert req.tags is None


def test_create_todo_full():
    req = CreateTodoRequest(
        title="Buy milk",
        notes="Low fat",
        when="today",
        deadline="2026-04-10",
        tags=["errand"],
        checklist_items=["Whole milk", "Skim milk"],
        list_id="proj-uuid",
        heading="Groceries",
    )
    assert req.tags == ["errand"]
    assert len(req.checklist_items) == 2


def test_create_todo_requires_title():
    with pytest.raises(ValidationError):
        CreateTodoRequest()


def test_update_todo_all_optional():
    req = UpdateTodoRequest()
    assert req.title is None


def test_update_todo_append_notes():
    req = UpdateTodoRequest(append_notes="Added later")
    assert req.append_notes == "Added later"


def test_create_project_minimal():
    req = CreateProjectRequest(title="New Project")
    assert req.title == "New Project"


def test_delete_request_defaults_to_complete():
    req = DeleteRequest()
    assert req.action == DeleteAction.COMPLETE


def test_delete_request_cancel():
    req = DeleteRequest(action="cancel")
    assert req.action == DeleteAction.CANCEL


def test_todo_response():
    resp = TodoResponse(uuid="abc", title="Test", status="incomplete")
    assert resp.uuid == "abc"


def test_health_response():
    resp = HealthResponse(status="healthy", read=True, write=False)
    assert resp.write is False
