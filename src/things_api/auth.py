"""Bearer token authentication."""

import hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_scheme = HTTPBearer(auto_error=False)


def require_token(expected_token: str):
    """Return a FastAPI dependency that validates a Bearer token."""

    async def _verify(
        credentials: HTTPAuthorizationCredentials | None = Depends(_scheme),
    ) -> None:
        if credentials is None or not hmac.compare_digest(
            credentials.credentials, expected_token
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return Depends(_verify)
