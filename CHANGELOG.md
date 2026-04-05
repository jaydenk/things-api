# Changelog

All notable changes to this project will be documented in this file.

This project follows [Semantic Versioning](https://semver.org/).

## [0.3.1] — 2026-04-05

### Fixed

- Init wizard crash: config file wasn't found by Settings after being created, because env file list was evaluated at import time. Now always includes the config path so pydantic-settings picks it up immediately after creation.

## [0.3.0] — 2026-04-05

### Added

- `things-api init` — interactive setup wizard that generates an API token, detects Things URL scheme status, and writes config to `~/.config/things-api/config`
- `--token` and `--port` CLI flags for on-the-fly overrides
- Auto-launches init wizard on first run when no config exists
- Fixed config file path at `~/.config/things-api/config` — no more CWD-dependent `.env` files
- Config resolution order: CLI flags > env vars > config file > CWD `.env` > defaults

### Changed

- CLI framework switched from raw uvicorn to Click
- Simplified launchd plist — no `WorkingDirectory` needed

## [0.2.1] — 2026-04-03

### Added

- Published to [PyPI](https://pypi.org/project/things-api/) — install with `pip install things-api` or run with `uvx things-api`
- GitHub Actions CI/CD pipeline with tag-driven PyPI publishing via trusted publishers (OIDC)

### Fixed

- Friendly error message when `THINGS_API_TOKEN` is missing instead of a Pydantic traceback

## [0.1.0] — 2026-04-03

### Added

- FastAPI REST API for Things 3 with bearer token authentication
- Full CRUD for todos and projects via Things URL scheme
- Read-only endpoints for smart lists (inbox, today, upcoming, anytime, someday, logbook)
- Tag and area listing endpoints
- Full-text and advanced filtered search
- Health endpoint with database connectivity check
- Configuration via environment variables and `.env` file
- Rate limiting on failed authentication attempts (10 per minute per IP)
- Timing-safe token comparison and `SecretStr` for token storage
- launchd plist template for running as a persistent service
- 69 unit tests covering auth, config, services, routers, and rate limiting

### Security

- Bearer tokens stored as `SecretStr` — never exposed in logs, repr, or stack traces
- Auth token redacted in log output (both raw and URL-encoded forms)
- Subprocess stderr logged server-side only — never returned to API consumers
- Swagger/ReDoc UI disabled to prevent schema reconnaissance
