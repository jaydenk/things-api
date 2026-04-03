"""Pydantic request/response models for the Things API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


# --- Requests ---


class CreateTodoRequest(BaseModel):
    """Create a new todo."""

    title: str
    notes: str | None = None
    when: str | None = None
    deadline: str | None = None
    tags: list[str] | None = None
    checklist_items: list[str] | None = None
    list_id: str | None = None
    list_title: str | None = None
    heading: str | None = None
    heading_id: str | None = None


class UpdateTodoRequest(BaseModel):
    """Update an existing todo. All fields optional."""

    title: str | None = None
    notes: str | None = None
    prepend_notes: str | None = None
    append_notes: str | None = None
    when: str | None = None
    deadline: str | None = None
    tags: list[str] | None = None
    add_tags: list[str] | None = None
    checklist_items: list[str] | None = None
    prepend_checklist_items: list[str] | None = None
    append_checklist_items: list[str] | None = None
    list_id: str | None = None
    list_title: str | None = None
    heading: str | None = None
    heading_id: str | None = None


class CreateProjectRequest(BaseModel):
    """Create a new project."""

    title: str
    notes: str | None = None
    when: str | None = None
    deadline: str | None = None
    tags: list[str] | None = None
    area_id: str | None = None
    area_title: str | None = None
    todos: list[str] | None = None


class UpdateProjectRequest(BaseModel):
    """Update an existing project. All fields optional."""

    title: str | None = None
    notes: str | None = None
    prepend_notes: str | None = None
    append_notes: str | None = None
    when: str | None = None
    deadline: str | None = None
    tags: list[str] | None = None
    add_tags: list[str] | None = None
    area_id: str | None = None
    area_title: str | None = None


class DeleteAction(str, Enum):
    """Action when deleting (Things has no true deletion)."""

    COMPLETE = "complete"
    CANCEL = "cancel"


class DeleteRequest(BaseModel):
    """Body for DELETE endpoints."""

    action: DeleteAction = DeleteAction.COMPLETE


# --- Responses ---


class TodoResponse(BaseModel):
    """A Things todo item."""

    model_config = {"extra": "allow"}

    uuid: str
    title: str
    status: str


class ProjectResponse(BaseModel):
    """A Things project."""

    model_config = {"extra": "allow"}

    uuid: str
    title: str
    status: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    read: bool
    write: bool
