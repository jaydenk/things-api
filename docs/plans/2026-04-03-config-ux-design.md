# Config UX Improvement — Design Document

**Date:** 2026-04-03
**Status:** Approved

## Problem

Running `uvx things-api` requires a `.env` file in the current working directory. Since `uvx` can be run from anywhere, the user has to either `cd` to a specific directory or pass env vars inline every time. This is clunky — there's no stable home for the config when the tool is installed via PyPI rather than cloned.

## Solution

A layered config system with a fixed config file location, CLI flags for quick overrides, and an interactive setup wizard for first-run.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Config file location | `~/.config/things-api/config` | XDG-style, always found regardless of CWD |
| Config file format | dotenv | Compatible with existing pydantic-settings loading |
| CLI framework | `click` | Lighter than typer, well-established, minimal dependency |
| CLI flags | `--token` and `--port` only | Most common overrides; everything else via config file or env vars |
| First-run behaviour | Auto-launch init wizard | Friendliest UX — no error, just guides you through setup |
| Token generation | `secrets.token_urlsafe(24)` with `tk_` prefix | Readable, copy-pasteable, secure |
| Things auth detection | Read from Things preferences plist | Auto-detect when possible, skip gracefully if not available |

## Config Resolution Order

Highest priority wins:

```
CLI flags (--token, --port)
    ↓
Environment variables (THINGS_API_TOKEN, etc.)
    ↓
~/.config/things-api/config
    ↓
.env in CWD (backwards-compatible)
    ↓
Defaults
```

## CLI Interface

```
things-api              # Start the server (default)
things-api init         # Interactive setup wizard
things-api --token X    # Override API token
things-api --port 8080  # Override port
things-api --help       # Show help
```

## Init Wizard Flow

Triggered by `things-api init` or automatically on first run when no config exists.

```
Things API Setup
================

1. API Token
   Generate a random token? [Y/n]: Y
   ✓ Generated: tk_a7f3b9c2e1d8...

2. Things URL Scheme Auth Token
   Checking Things URL scheme... found!
   Use detected token? [Y/n]: Y
   ✓ Write operations enabled

3. Port
   Port [5225]:
   ✓ Using default port 5225

Config written to ~/.config/things-api/config
Starting server...
```

### Things Auth Token Auto-Detection

The Things URL scheme auth token is stored in the Things preferences plist at `~/Library/Group Containers/*.com.culturedcode.ThingsMac/Library/Preferences/*.com.culturedcode.ThingsMac.plist` under the `authToken` key. Read with `plistlib`. If not found or Things URLs aren't enabled, skip and tell the user how to enable it manually.

## Files Changed

| File | Change |
|------|--------|
| `config.py` | Add `~/.config/things-api/config` as higher-priority env file source |
| `app.py` | Remove `main()` entrypoint (moved to cli.py) |
| `cli.py` (new) | Click CLI group with server command and init subcommand |
| `init.py` (new) | Setup wizard: token generation, Things auth detection, config writing |
| `pyproject.toml` | Add `click` dependency, update entrypoint to `things_api.cli:cli` |
| `com.things-api.server.plist` | Simplify — no `WorkingDirectory` needed |
| Tests | New tests for CLI and init; existing app factory tests unchanged |

## Files Unchanged

`auth.py`, `ratelimit.py`, all routers, `reader.py`, `writer.py`, `models.py`, `create_app()` factory.
