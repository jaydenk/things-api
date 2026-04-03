# Things API — Design Document

**Date:** 2026-04-03
**Status:** Approved

## Summary

A REST API that exposes Things 3 task management data over HTTP. Reads from the Things SQLite database via `things.py`, writes via the Things URL scheme. Runs as a standalone FastAPI service on the Mac where Things is installed, accessible locally and over Tailscale (or any network).

Open-source, published to PyPI as `things-api`.

## Architecture

```
Clients (n8n, curl, etc.)
    │
    ▼  HTTP + Bearer token
FastAPI (things-api, port 5225)
    ├── reader.py ──► things.py ──► Things SQLite DB (read-only)
    └── writer.py ──► subprocess: open "things:///..." ──► Things 3 app
```

- **Reads**: Direct SQLite queries via `things.py` library
- **Writes**: macOS `open` command invoking Things URL scheme (`things:///add`, `things:///update`, `things:///add-project`, `things:///update-project`)
- **Auth**: Bearer token required on all endpoints
- **Platform**: macOS only (Things 3 is Mac-only)

## Project Structure

```
things-api/
├── pyproject.toml
├── src/
│   └── things_api/
│       ├── __init__.py
│       ├── app.py              # FastAPI app factory
│       ├── config.py           # Settings (host, port, tokens, DB path)
│       ├── auth.py             # Bearer token middleware
│       ├── routers/
│       │   ├── todos.py        # CRUD for todos
│       │   ├── projects.py     # CRUD for projects
│       │   ├── areas.py        # Read areas
│       │   ├── tags.py         # Read tags
│       │   ├── lists.py        # Inbox, today, upcoming, anytime, someday, logbook
│       │   └── search.py       # Search endpoints
│       ├── services/
│       │   ├── reader.py       # things.py wrapper (reads)
│       │   └── writer.py       # URL scheme subprocess (writes)
│       └── models.py           # Pydantic request/response schemas
├── tests/
├── env.example
├── README.md
└── LICENSE                     # MIT
```

## API Endpoints

### Todos (full CRUD)

| Method | Endpoint | Description | Source |
|--------|----------|-------------|--------|
| `GET` | `/todos` | List incomplete todos (filter: `?project_id=`, `?area_id=`, `?tag=`, `?include_checklist=true`) | `things.todos()` |
| `GET` | `/todos/{id}` | Get a specific todo | `things.get()` |
| `POST` | `/todos` | Create a todo | URL scheme `things:///add` |
| `PUT` | `/todos/{id}` | Update a todo | URL scheme `things:///update` |
| `DELETE` | `/todos/{id}` | Complete or cancel a todo | URL scheme `things:///update` + completed/canceled flag |

### Projects (full CRUD)

| Method | Endpoint | Description | Source |
|--------|----------|-------------|--------|
| `GET` | `/projects` | List all projects | `things.projects()` |
| `GET` | `/projects/{id}` | Get a project with its todos | `things.get()` |
| `POST` | `/projects` | Create a project | URL scheme `things:///add-project` |
| `PUT` | `/projects/{id}` | Update a project | URL scheme `things:///update-project` |
| `DELETE` | `/projects/{id}` | Complete or cancel a project | URL scheme `things:///update-project` |

### Lists (read-only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/inbox` | Inbox todos |
| `GET` | `/today` | Today's todos |
| `GET` | `/upcoming` | Upcoming todos |
| `GET` | `/anytime` | Anytime todos |
| `GET` | `/someday` | Someday todos |
| `GET` | `/logbook` | Completed todos (`?period=7d&limit=50`) |

### Areas & Tags (read-only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/areas` | List areas (`?include_items=true`) |
| `GET` | `/tags` | List tags (`?include_items=true`) |
| `GET` | `/tags/{tag}/items` | Items with a specific tag |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/search?q=...` | Full-text search across todos |
| `GET` | `/search/advanced` | Filtered search (status, date range, tag, area, type) |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (DB readable, write capability) |

### DELETE Semantics

`DELETE` on todos/projects marks items as completed (default) or canceled. The request body can specify `{"action": "complete"}` or `{"action": "cancel"}`. Things URL scheme does not support actual deletion.

## Write Path & Verification

### Flow

1. Receive write request, validate with Pydantic
2. Build Things URL scheme string in `writer.py`
3. Execute `subprocess.run(["open", url])` 
4. Wait briefly (configurable, default 0.5s)
5. Query Things SQLite DB for the newly created/updated item via `reader.py`
6. If found: return `201 Created` (or `200 OK` for updates) with the full object
7. If not found within timeout: return `202 Accepted`

### Auth Token

The Things URL scheme requires an auth token for update operations. `THINGS_AUTH_TOKEN` must be configured for write endpoints. Without it, write endpoints return `503 Service Unavailable`. Read endpoints work regardless.

## Configuration

All via environment variables, loaded from `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `THINGS_API_HOST` | `0.0.0.0` | Bind address |
| `THINGS_API_PORT` | `5225` | Bind port |
| `THINGS_API_TOKEN` | *(required)* | Bearer token for API authentication |
| `THINGS_AUTH_TOKEN` | *(optional)* | Things URL scheme auth token (enables writes) |
| `THINGS_DB_PATH` | *(auto-detected)* | Override path to Things SQLite DB |
| `THINGS_VERIFY_TIMEOUT` | `0.5` | Seconds to wait for write read-back verification |

`THINGS_API_TOKEN` is the only hard requirement — server refuses to start without it.

## Deployment

### Running

```bash
# Via uvx (no install)
uvx things-api

# Or installed
pip install things-api
things-api
```

### launchd (persistent service)

A plist template is included in the repo. Key settings:
- `KeepAlive: true` — auto-restart on crash
- Logs to `~/Library/Logs/things-api.log`
- Env vars for tokens configured in the plist or sourced from `.env`

## Error Handling

| Scenario | Response |
|----------|----------|
| Missing/invalid bearer token | `401 Unauthorized` |
| Things DB not found | `503 Service Unavailable` |
| Write attempted without `THINGS_AUTH_TOKEN` | `503 Service Unavailable` |
| `open` subprocess fails | `500 Internal Server Error` |
| Todo/project not found by ID | `404 Not Found` |
| Invalid request body | `422 Unprocessable Entity` |
| Write dispatched but read-back times out | `202 Accepted` |

## Testing

- **Unit tests**: Mock `things.py` and subprocess calls. No Things 3 needed.
- **Reader tests**: Verify service layer translation from `things.py` to Pydantic models.
- **Writer tests**: Verify URL scheme construction, encoding, auth token inclusion.
- **Auth tests**: 401 without token, 403 with wrong token, pass-through with correct token.
- **Integration tests**: Optional, `@pytest.mark.integration`, run against real Things.

## Logging

- Structured logging via Python `logging`
- Request/response at INFO (method, path, status)
- Write operations at INFO with URL scheme command (token redacted)
- Errors at ERROR with full context

## Dependencies

- `fastapi` — web framework
- `uvicorn` — ASGI server
- `things.py` — Things 3 SQLite reader
- `pydantic-settings` — env/config management
- `pytest` / `pytest-asyncio` / `httpx` — testing
