"""Write to Things 3 via the URL scheme."""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import quote, urlencode

logger = logging.getLogger(__name__)


class ThingsWriter:
    """Creates and updates Things items via the URL scheme."""

    def __init__(self, auth_token: str, verify_timeout: float = 0.5) -> None:
        self._auth_token = auth_token
        self._verify_timeout = verify_timeout

    def _build_url(self, command: str, **params) -> str:
        """Build a things:/// URL with encoded parameters."""
        filtered = {}
        for key, value in params.items():
            if value is None:
                continue
            url_key = key.replace("_", "-")
            if isinstance(value, list):
                filtered[url_key] = ",".join(str(v) for v in value)
            elif isinstance(value, bool):
                filtered[url_key] = "true" if value else "false"
            else:
                filtered[url_key] = str(value)
        qs = urlencode(filtered, quote_via=quote)
        return f"things:///{command}?{qs}" if qs else f"things:///{command}"

    async def _execute(self, url: str) -> None:
        """Open a Things URL scheme command."""
        redacted = url.replace(self._auth_token, "REDACTED")
        redacted = redacted.replace(
            quote(self._auth_token, safe=""), "REDACTED"
        )
        logger.info("Executing: %s", redacted)

        proc = await asyncio.create_subprocess_exec(
            "open", url,
            stderr=asyncio.subprocess.PIPE,
        )
        returncode = await proc.wait()
        if returncode != 0:
            stderr = await proc.stderr.read() if proc.stderr else b""
            logger.error(
                "URL scheme command failed (exit %d): %s",
                returncode, stderr.decode(),
            )
            raise RuntimeError("Write operation failed")

    async def create_todo(self, **params) -> None:
        url = self._build_url("add", **params)
        await self._execute(url)

    async def update_todo(self, uuid: str, **params) -> None:
        url = self._build_url(
            "update", id=uuid, auth_token=self._auth_token, **params
        )
        await self._execute(url)

    async def complete_todo(self, uuid: str) -> None:
        await self.update_todo(uuid, completed=True)

    async def cancel_todo(self, uuid: str) -> None:
        await self.update_todo(uuid, canceled=True)

    async def create_project(self, **params) -> None:
        url = self._build_url("add-project", **params)
        await self._execute(url)

    async def update_project(self, uuid: str, **params) -> None:
        url = self._build_url(
            "update-project", id=uuid, auth_token=self._auth_token, **params
        )
        await self._execute(url)

    async def complete_project(self, uuid: str) -> None:
        await self.update_project(uuid, completed=True)

    async def cancel_project(self, uuid: str) -> None:
        await self.update_project(uuid, canceled=True)
