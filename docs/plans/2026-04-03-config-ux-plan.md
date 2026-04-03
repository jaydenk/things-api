# Config UX Improvement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:executing-plans to implement this plan task-by-task.

**Goal:** Replace the CWD-dependent `.env` config with a fixed `~/.config/things-api/config` file, CLI flags, and an interactive setup wizard.

**Architecture:** Click CLI wrapping the existing FastAPI app factory. Config resolution: CLI flags > env vars > `~/.config/things-api/config` > CWD `.env` > defaults. Init wizard auto-generates API token, detects if Things URL scheme is enabled, and writes the config file.

**Tech Stack:** click, plistlib (stdlib), secrets (stdlib), existing pydantic-settings.

**Design doc:** `docs/plans/2026-04-03-config-ux-design.md`

---

### Task 0: Add click dependency and update entrypoint

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add click to dependencies and update entrypoint**

In `pyproject.toml`, add `"click>=8,<9"` to `dependencies` and change the entrypoint from `things_api.app:main` to `things_api.cli:cli`.

```toml
dependencies = [
    "click>=8,<9",
    "fastapi>=0.135,<1",
    "uvicorn[standard]>=0.34,<1",
    "things.py>=1.0,<2",
    "pydantic-settings>=2.13,<3",
]

[project.scripts]
things-api = "things_api.cli:cli"
```

**Step 2: Reinstall**

Run: `uv pip install -e ".[test]"`

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add click dependency and update entrypoint"
```

---

### Task 1: Update config.py to load from ~/.config/things-api/config

**Files:**
- Modify: `src/things_api/config.py`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

Add to `tests/test_config.py`:

```python
def test_settings_loads_from_config_dir(monkeypatch, tmp_path):
    """Settings should load from ~/.config/things-api/config."""
    config_dir = tmp_path / ".config" / "things-api"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config"
    config_file.write_text("THINGS_API_TOKEN=from-config-dir\n")

    monkeypatch.delenv("THINGS_API_TOKEN", raising=False)
    monkeypatch.delenv("THINGS_AUTH_TOKEN", raising=False)

    from things_api.config import Settings

    s = Settings(_env_file=str(config_file))
    assert s.things_api_token.get_secret_value() == "from-config-dir"


def test_config_dir_path():
    from things_api.config import CONFIG_DIR, CONFIG_FILE
    assert CONFIG_DIR.name == "things-api"
    assert CONFIG_FILE.name == "config"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py::test_settings_loads_from_config_dir tests/test_config.py::test_config_dir_path -v`
Expected: FAIL with `ImportError` for `CONFIG_DIR`

**Step 3: Write implementation**

Update `src/things_api/config.py`:

```python
"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings

CONFIG_DIR = Path.home() / ".config" / "things-api"
CONFIG_FILE = CONFIG_DIR / "config"


def _env_files() -> list[Path]:
    """Return env files in priority order (last wins in pydantic-settings)."""
    files = []
    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file():
        files.append(cwd_env)
    if CONFIG_FILE.is_file():
        files.append(CONFIG_FILE)
    return files


class Settings(BaseSettings):
    """Things API configuration.

    All values can be set via environment variables or a .env file.
    """

    things_api_host: str = "0.0.0.0"
    things_api_port: int = 5225
    things_api_token: SecretStr
    things_auth_token: SecretStr | None = None
    things_db_path: Path | None = None
    things_verify_timeout: float = 0.5

    model_config = {"env_file": _env_files(), "env_file_encoding": "utf-8"}

    @property
    def write_enabled(self) -> bool:
        """Whether write operations are available."""
        return self.things_auth_token is not None and bool(
            self.things_auth_token.get_secret_value()
        )
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/things_api/config.py tests/test_config.py
git commit -m "feat: load config from ~/.config/things-api/config with CWD .env fallback"
```

---

### Task 2: Create init wizard

**Files:**
- Create: `src/things_api/init.py`
- Test: `tests/test_init.py`

**Step 1: Write the failing test**

```python
# tests/test_init.py
import plistlib
from unittest.mock import patch

from things_api.init import generate_token, detect_things_url_scheme, write_config


def test_generate_token():
    token = generate_token()
    assert token.startswith("tk_")
    assert len(token) > 20


def test_generate_token_unique():
    assert generate_token() != generate_token()


def test_detect_things_url_scheme_enabled(tmp_path):
    """Detect when Things URL scheme is enabled."""
    plist_dir = tmp_path / "Group Containers" / "JLMPQHK86H.com.culturedcode.ThingsMac" / "Library" / "Preferences"
    plist_dir.mkdir(parents=True)
    plist_file = plist_dir / "JLMPQHK86H.com.culturedcode.ThingsMac.plist"
    with open(plist_file, "wb") as f:
        plistlib.dump({"uriSchemeEnabled": True}, f)

    result = detect_things_url_scheme(
        search_root=tmp_path / "Group Containers"
    )
    assert result is True


def test_detect_things_url_scheme_disabled(tmp_path):
    """Detect when Things URL scheme is not enabled."""
    result = detect_things_url_scheme(search_root=tmp_path / "nonexistent")
    assert result is False


def test_write_config(tmp_path):
    config_file = tmp_path / "config"
    write_config(
        config_file,
        api_token="tk_test123",
        auth_token="things-auth-456",
        port=5225,
    )
    content = config_file.read_text()
    assert "THINGS_API_TOKEN=tk_test123" in content
    assert "THINGS_AUTH_TOKEN=things-auth-456" in content
    assert "THINGS_API_PORT=5225" in content


def test_write_config_without_auth_token(tmp_path):
    config_file = tmp_path / "config"
    write_config(
        config_file,
        api_token="tk_test123",
        auth_token=None,
        port=5225,
    )
    content = config_file.read_text()
    assert "THINGS_API_TOKEN=tk_test123" in content
    assert "THINGS_AUTH_TOKEN" not in content


def test_write_config_creates_parent_dirs(tmp_path):
    config_file = tmp_path / "deep" / "nested" / "config"
    write_config(config_file, api_token="tk_test", auth_token=None, port=5225)
    assert config_file.exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_init.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write implementation**

```python
# src/things_api/init.py
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
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_init.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/things_api/init.py tests/test_init.py
git commit -m "feat: add init module with token generation, Things detection, and config writer"
```

---

### Task 3: Create CLI with click

**Files:**
- Create: `src/things_api/cli.py`
- Modify: `src/things_api/app.py` (remove `main()`)
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
# tests/test_cli.py
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from things_api.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Things API" in result.output


def test_init_subcommand_creates_config(tmp_path):
    runner = CliRunner()
    config_file = tmp_path / "config"
    with patch("things_api.cli.CONFIG_FILE", config_file):
        with patch("things_api.cli.detect_things_url_scheme", return_value=False):
            result = runner.invoke(cli, ["init"], input="Y\n\n5225\n")
            assert result.exit_code == 0
            assert config_file.exists()
            content = config_file.read_text()
            assert "THINGS_API_TOKEN=tk_" in content


def test_init_detects_existing_config(tmp_path):
    runner = CliRunner()
    config_file = tmp_path / "config"
    config_file.write_text("THINGS_API_TOKEN=existing\n")
    with patch("things_api.cli.CONFIG_FILE", config_file):
        result = runner.invoke(cli, ["init"], input="n\n")
        assert result.exit_code == 0
        # Should ask about overwriting
        assert "already exists" in result.output.lower() or "overwrite" in result.output.lower()


def test_server_with_token_flag(monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("THINGS_API_TOKEN", "env-token")
    with patch("things_api.cli.uvicorn") as mock_uvicorn:
        with patch("things_api.services.reader.things"):
            result = runner.invoke(cli, ["--token", "flag-token", "--port", "9999"])
            mock_uvicorn.run.assert_called_once()
            call_kwargs = mock_uvicorn.run.call_args[1]
            assert call_kwargs["port"] == 9999


def test_first_run_triggers_init(tmp_path, monkeypatch):
    """When no config exists and no token provided, auto-trigger init."""
    runner = CliRunner()
    config_file = tmp_path / "config"
    monkeypatch.delenv("THINGS_API_TOKEN", raising=False)
    with patch("things_api.cli.CONFIG_FILE", config_file):
        with patch("things_api.cli.detect_things_url_scheme", return_value=False):
            with patch("things_api.cli.uvicorn"):
                with patch("things_api.services.reader.things"):
                    result = runner.invoke(cli, [], input="Y\n\n5225\n")
                    assert config_file.exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write implementation**

```python
# src/things_api/cli.py
"""Click CLI for Things API."""

from __future__ import annotations

import logging

import click
import uvicorn

from things_api.config import CONFIG_DIR, CONFIG_FILE, Settings
from things_api.init import detect_things_url_scheme, generate_token, write_config


def _run_init() -> None:
    """Interactive setup wizard."""
    click.echo("Things API Setup")
    click.echo("=" * 40)
    click.echo()

    # 1. API Token
    click.echo("1. API Token")
    generate = click.confirm("   Generate a random token?", default=True)
    if generate:
        api_token = generate_token()
        click.echo(f"   ✓ Generated: {api_token}")
    else:
        api_token = click.prompt("   Enter your API token")
    click.echo()

    # 2. Things URL Scheme Auth Token
    click.echo("2. Things URL Scheme Auth Token")
    url_scheme_enabled = detect_things_url_scheme()
    if url_scheme_enabled:
        click.echo("   Things URL scheme is enabled.")
        click.echo("   To find your auth token, open Things > Settings > General > Enable Things URLs.")
        auth_token = click.prompt("   Paste your Things auth token (or press Enter to skip)", default="", show_default=False)
        if auth_token:
            click.echo("   ✓ Write operations enabled")
        else:
            auth_token = None
            click.echo("   ⏭ Skipped — running in read-only mode")
    else:
        click.echo("   Things URL scheme is not enabled.")
        click.echo("   To enable writes, open Things > Settings > General > Enable Things URLs.")
        auth_token = None
        click.echo("   ⏭ Skipped — running in read-only mode")
    click.echo()

    # 3. Port
    click.echo("3. Port")
    port = click.prompt("   Port", default=5225, type=int)
    click.echo()

    # Write config
    write_config(CONFIG_FILE, api_token, auth_token, port)
    click.echo(f"Config written to {CONFIG_FILE}")


@click.group(invoke_without_command=True)
@click.option("--token", default=None, help="API bearer token (overrides config file)")
@click.option("--port", default=None, type=int, help="Port to listen on (overrides config file)")
@click.pass_context
def cli(ctx: click.Context, token: str | None, port: int | None) -> None:
    """Things API — REST API for Things 3."""
    if ctx.invoked_subcommand is not None:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Try loading settings; if missing token, trigger init
    try:
        overrides = {}
        if token:
            overrides["things_api_token"] = token
        if port:
            overrides["things_api_port"] = port
        settings = Settings(**overrides)
    except Exception:
        if not CONFIG_FILE.exists():
            click.echo("No configuration found. Let's set one up.\n")
            _run_init()
            click.echo()
            settings = Settings()
        else:
            click.echo(
                f"Error: THINGS_API_TOKEN is not set.\n"
                f"\n"
                f"Run 'things-api init' to reconfigure, or pass --token.\n"
            )
            raise SystemExit(1)

    from things_api.app import create_app

    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.things_api_host,
        port=settings.things_api_port,
    )


@cli.command()
def init() -> None:
    """Interactive setup wizard."""
    if CONFIG_FILE.exists():
        overwrite = click.confirm(
            f"Config already exists at {CONFIG_FILE}. Overwrite?",
            default=False,
        )
        if not overwrite:
            click.echo("Aborted.")
            return
    _run_init()
```

**Step 4: Remove `main()` from app.py**

Delete lines 86-110 from `src/things_api/app.py` (the entire `main()` function). The `create_app()` factory remains unchanged.

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py tests/test_app.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/things_api/cli.py src/things_api/app.py tests/test_cli.py
git commit -m "feat: add click CLI with server command, init wizard, and --token/--port flags"
```

---

### Task 4: Simplify launchd plist

**Files:**
- Modify: `com.things-api.server.plist`

**Step 1: Update the plist**

Remove `WorkingDirectory` (no longer needed — config is at a fixed path). Default to `uvx`:

```xml
<!--
  Things API launchd agent

  Prerequisites:
    1. Run 'things-api init' first to create your config at ~/.config/things-api/config
    2. Replace /path/to/uvx below with the output of: which uvx

  Install:
    cp com.things-api.server.plist ~/Library/LaunchAgents/
    launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.things-api.server.plist

  Uninstall:
    launchctl bootout gui/$(id -u)/com.things-api.server
    rm ~/Library/LaunchAgents/com.things-api.server.plist
-->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>com.things-api.server</string>
	<key>ProgramArguments</key>
	<array>
		<string>/path/to/uvx</string>
		<string>things-api</string>
	</array>
	<key>KeepAlive</key>
	<true/>
	<key>RunAtLoad</key>
	<true/>
	<key>StandardOutPath</key>
	<string>/tmp/things-api.log</string>
	<key>StandardErrorPath</key>
	<string>/tmp/things-api.log</string>
</dict>
</plist>
```

**Step 2: Commit**

```bash
git add com.things-api.server.plist
git commit -m "chore: simplify launchd plist — no WorkingDirectory needed with fixed config path"
```

---

### Task 5: Update documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/configuration.md`
- Modify: `docs/deployment.md`
- Modify: `CHANGELOG.md`

**Step 1: Update README getting started**

Replace the "Configure" section to show the new flow:

```markdown
### 2. Configure

Run the setup wizard:

\```sh
things-api init
\```

This generates an API token, detects your Things URL scheme settings, and writes the config to `~/.config/things-api/config`.

Or configure manually — see [docs/configuration.md](docs/configuration.md) for all options.
```

Replace the "Run" section:

```markdown
### 3. Run

\```sh
things-api
\```

Override settings on the fly:

\```sh
things-api --token my-token --port 8080
\```
```

**Step 2: Update docs/configuration.md**

Add a section explaining the config resolution order and the new config file location. Update the security notes about `things-api init`.

**Step 3: Update docs/deployment.md**

Simplify the launchd section — just `things-api init` first, then copy the plist. No more `WorkingDirectory` or `.env` setup.

**Step 4: Update CHANGELOG.md**

Add entry for the new version covering the config UX changes.

**Step 5: Commit**

```bash
git add README.md docs/configuration.md docs/deployment.md CHANGELOG.md
git commit -m "docs: update for new config UX with init wizard and fixed config path"
```

---

### Task 6: Full test suite and smoke test

**Steps:**

1. Run full test suite:
   ```bash
   uv run pytest -v
   ```
   Expected: All tests pass

2. Test the init wizard manually:
   ```bash
   uv run things-api init
   ```
   Verify config written to `~/.config/things-api/config`

3. Test server starts from config:
   ```bash
   uv run things-api
   ```

4. Test CLI flag override:
   ```bash
   uv run things-api --port 9999
   ```

5. Test first-run auto-init (move config aside temporarily):
   ```bash
   mv ~/.config/things-api/config ~/.config/things-api/config.bak
   uv run things-api
   # Should auto-trigger init wizard
   mv ~/.config/things-api/config.bak ~/.config/things-api/config
   ```

**Commit message:** `chore: all tests passing after config UX improvement`
