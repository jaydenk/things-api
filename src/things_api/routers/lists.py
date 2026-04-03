"""Smart list endpoints — inbox, today, upcoming, anytime, someday, logbook."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["lists"])


@router.get("/inbox")
async def inbox(request: Request):
    """Get inbox todos."""
    return request.app.state.reader.inbox()


@router.get("/today")
async def today(request: Request):
    """Get today's todos."""
    return request.app.state.reader.today()


@router.get("/upcoming")
async def upcoming(request: Request):
    """Get upcoming todos."""
    return request.app.state.reader.upcoming()


@router.get("/anytime")
async def anytime(request: Request):
    """Get anytime todos."""
    return request.app.state.reader.anytime()


@router.get("/someday")
async def someday(request: Request):
    """Get someday todos."""
    return request.app.state.reader.someday()


@router.get("/logbook")
async def logbook(request: Request, period: str | None = None, limit: int | None = None):
    """Get completed todos from the logbook."""
    filters = {}
    if period:
        filters["last"] = period
    if limit:
        filters["limit"] = limit
    return request.app.state.reader.logbook(**filters)
