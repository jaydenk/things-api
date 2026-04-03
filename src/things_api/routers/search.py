"""Search endpoints."""

from __future__ import annotations

import logging
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


class SearchStatus(str, Enum):
    INCOMPLETE = "incomplete"
    COMPLETED = "completed"
    CANCELED = "canceled"


class SearchType(str, Enum):
    TO_DO = "to-do"
    PROJECT = "project"
    HEADING = "heading"


@router.get("")
async def search(request: Request, q: str):
    """Full-text search across todos."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    return request.app.state.reader.search(q)


@router.get("/advanced")
async def advanced_search(
    request: Request,
    status: SearchStatus | None = None,
    tag: str | None = None,
    area: str | None = None,
    type: SearchType | None = None,
    start_date: str = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    deadline: str = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    last: str = Query(None, pattern=r"^\d+[dwmy]$"),
):
    """Filtered search with multiple criteria."""
    filters = {}
    if status:
        filters["status"] = status.value
    if tag:
        filters["tag"] = tag
    if area:
        filters["area"] = area
    if type:
        filters["type"] = type.value
    if start_date:
        filters["start_date"] = start_date
    if deadline:
        filters["deadline"] = deadline
    if last:
        filters["last"] = last
    return request.app.state.reader.todos(**filters)
