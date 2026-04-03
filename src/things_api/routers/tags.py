"""Tag endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
async def list_tags(request: Request, include_items: bool = False):
    """List all tags."""
    return request.app.state.reader.tags(include_items=include_items)


@router.get("/{tag}/items")
async def tag_items(request: Request, tag: str):
    """Get items with a specific tag."""
    return request.app.state.reader.tags_for_item(tag_title=tag)
