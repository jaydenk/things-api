"""Project CRUD endpoints."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request, status

from things_api.models import (
    CreateProjectRequest,
    DeleteAction,
    DeleteRequest,
    UpdateProjectRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
async def list_projects(request: Request):
    """List all projects."""
    return request.app.state.reader.projects()


@router.get("/{project_id}")
async def get_project(request: Request, project_id: str):
    """Get a project with its todos."""
    result = request.app.state.reader.get(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(request: Request, body: CreateProjectRequest):
    """Create a new project."""
    writer = request.app.state.writer
    if writer is None:
        raise HTTPException(
            status_code=503, detail="Write operations not configured"
        )

    params = body.model_dump(exclude_none=True)
    if "todos" in params:
        params["todos"] = "\n".join(params["todos"])

    await writer.create_project(**params)

    await asyncio.sleep(request.app.state.settings.things_verify_timeout)
    results = request.app.state.reader.projects()
    for item in results:
        if item.get("title") == body.title:
            return item

    return {"status": "accepted", "title": body.title}


@router.put("/{project_id}")
async def update_project(
    request: Request, project_id: str, body: UpdateProjectRequest
):
    """Update an existing project."""
    writer = request.app.state.writer
    if writer is None:
        raise HTTPException(
            status_code=503, detail="Write operations not configured"
        )

    existing = request.app.state.reader.get(project_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Project not found")

    params = body.model_dump(exclude_none=True)
    await writer.update_project(uuid=project_id, **params)

    await asyncio.sleep(request.app.state.settings.things_verify_timeout)
    updated = request.app.state.reader.get(project_id)
    return updated if updated else {"status": "accepted", "uuid": project_id}


@router.delete("/{project_id}")
async def delete_project(
    request: Request, project_id: str, body: DeleteRequest | None = None
):
    """Complete or cancel a project."""
    writer = request.app.state.writer
    if writer is None:
        raise HTTPException(
            status_code=503, detail="Write operations not configured"
        )

    existing = request.app.state.reader.get(project_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Project not found")

    action = body.action if body else DeleteAction.COMPLETE
    if action == DeleteAction.CANCEL:
        await writer.cancel_project(uuid=project_id)
    else:
        await writer.complete_project(uuid=project_id)

    return {"status": action.value, "uuid": project_id}
