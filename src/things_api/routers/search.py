"""Search endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(request: Request, q: str):
    """Full-text search across todos."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    return request.app.state.reader.search(q)


@router.get("/advanced")
async def advanced_search(
    request: Request,
    status: str | None = None,
    tag: str | None = None,
    area: str | None = None,
    type: str | None = None,
    start_date: str | None = None,
    deadline: str | None = None,
    last: str | None = None,
):
    """Filtered search with multiple criteria."""
    filters = {}
    if status:
        filters["status"] = status
    if tag:
        filters["tag"] = tag
    if area:
        filters["area"] = area
    if type:
        filters["type"] = type
    if start_date:
        filters["start_date"] = start_date
    if deadline:
        filters["deadline"] = deadline
    if last:
        filters["last"] = last
    return request.app.state.reader.todos(**filters)
