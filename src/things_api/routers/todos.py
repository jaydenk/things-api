"""Todo CRUD endpoints."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request, status

from things_api.models import (
    CreateTodoRequest,
    DeleteAction,
    DeleteRequest,
    UpdateTodoRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("")
async def list_todos(
    request: Request,
    project_id: str | None = None,
    area_id: str | None = None,
    tag: str | None = None,
    include_checklist: bool = False,
):
    """List all incomplete todos, with optional filters."""
    reader = request.app.state.reader
    filters = {}
    if project_id:
        filters["project"] = project_id
    if area_id:
        filters["area"] = area_id
    if tag:
        filters["tag"] = tag
    if include_checklist:
        filters["include_items"] = True
    return reader.todos(**filters)


@router.get("/{todo_id}")
async def get_todo(request: Request, todo_id: str):
    """Get a specific todo by ID."""
    result = request.app.state.reader.get(todo_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_todo(request: Request, body: CreateTodoRequest):
    """Create a new todo."""
    writer = request.app.state.writer
    if writer is None:
        raise HTTPException(
            status_code=503, detail="Write operations not configured"
        )

    params = body.model_dump(exclude_none=True)
    if "checklist_items" in params:
        params["checklist_items"] = "\n".join(params["checklist_items"])

    await writer.create_todo(**params)

    await asyncio.sleep(request.app.state.settings.things_verify_timeout)
    results = request.app.state.reader.search(body.title)
    for item in results:
        if item.get("title") == body.title:
            return item

    return {"status": "accepted", "title": body.title}


@router.put("/{todo_id}")
async def update_todo(request: Request, todo_id: str, body: UpdateTodoRequest):
    """Update an existing todo."""
    writer = request.app.state.writer
    if writer is None:
        raise HTTPException(
            status_code=503, detail="Write operations not configured"
        )

    existing = request.app.state.reader.get(todo_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    params = body.model_dump(exclude_none=True)
    for list_field in (
        "checklist_items",
        "prepend_checklist_items",
        "append_checklist_items",
    ):
        if list_field in params:
            params[list_field] = "\n".join(params[list_field])

    await writer.update_todo(uuid=todo_id, **params)

    await asyncio.sleep(request.app.state.settings.things_verify_timeout)
    updated = request.app.state.reader.get(todo_id)
    return updated if updated else {"status": "accepted", "uuid": todo_id}


@router.delete("/{todo_id}")
async def delete_todo(
    request: Request, todo_id: str, body: DeleteRequest | None = None
):
    """Complete or cancel a todo."""
    writer = request.app.state.writer
    if writer is None:
        raise HTTPException(
            status_code=503, detail="Write operations not configured"
        )

    existing = request.app.state.reader.get(todo_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    action = body.action if body else DeleteAction.COMPLETE
    if action == DeleteAction.CANCEL:
        await writer.cancel_todo(uuid=todo_id)
    else:
        await writer.complete_todo(uuid=todo_id)

    return {"status": action.value, "uuid": todo_id}
