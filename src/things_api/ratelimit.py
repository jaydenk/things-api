"""In-memory rate limiter for failed authentication attempts."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class AuthRateLimiter(BaseHTTPMiddleware):
    """Tracks 401 responses per client IP and blocks after too many failures.

    Uses a sliding window: only failures within the last `window` seconds count.
    Once `max_failures` is reached, subsequent requests from that IP receive
    429 Too Many Requests until the window expires.
    """

    def __init__(self, app, max_failures: int = 10, window: int = 60) -> None:
        super().__init__(app)
        self._max_failures = max_failures
        self._window = window
        self._failures: dict[str, list[float]] = defaultdict(list)

    def _client_ip(self, request: Request) -> str:
        return request.client.host if request.client else "unknown"

    def _prune(self, ip: str) -> None:
        """Remove entries older than the window."""
        cutoff = time.monotonic() - self._window
        self._failures[ip] = [t for t in self._failures[ip] if t > cutoff]
        if not self._failures[ip]:
            del self._failures[ip]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        ip = self._client_ip(request)
        self._prune(ip)

        if len(self._failures.get(ip, [])) >= self._max_failures:
            return Response(
                content='{"detail":"Too many failed attempts. Try again later."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self._window)},
            )

        response = await call_next(request)

        if response.status_code == 401:
            self._failures[ip].append(time.monotonic())

        return response
