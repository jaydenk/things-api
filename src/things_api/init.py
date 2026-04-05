"""Interactive setup wizard for Things API."""

from __future__ import annotations

import glob
import plistlib
import secrets
from pathlib import Path


def generate_token() -> str:
    """Generate a secure random API token with a readable prefix."""
    return f"tk_{secrets.token_urlsafe(24)}"


def detect_things_url_scheme(
    search_root: Path | None = None,
) -> bool:
    """Check if Things URL scheme is enabled by reading the preferences plist."""
    if search_root is None:
        search_root = Path.home() / "Library" / "Group Containers"
    pattern = str(search_root / "*.com.culturedcode.ThingsMac" / "Library" / "Preferences" / "*.com.culturedcode.ThingsMac.plist")
    matches = glob.glob(pattern)
    if not matches:
        return False
    try:
        with open(matches[0], "rb") as f:
            data = plistlib.load(f)
        return bool(data.get("uriSchemeEnabled", False))
    except Exception:
        return False


def write_config(
    config_file: Path,
    api_token: str,
    auth_token: str | None,
    port: int,
) -> None:
    """Write configuration to a dotenv-format file."""
    config_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"THINGS_API_TOKEN={api_token}"]
    if auth_token:
        lines.append(f"THINGS_AUTH_TOKEN={auth_token}")
    lines.append(f"THINGS_API_PORT={port}")
    config_file.write_text("\n".join(lines) + "\n")
