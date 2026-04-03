"""Area endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("")
async def list_areas(request: Request, include_items: bool = False):
    """List all areas."""
    return request.app.state.reader.areas(include_items=include_items)
