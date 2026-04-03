# Things API

REST API for [Things 3](https://culturedcode.com/things/) — expose your tasks over HTTP. Things API reads data directly from the Things SQLite database via [things.py](https://github.com/thingsapi/things.py) and writes back through the [Things URL scheme](https://culturedcode.com/things/support/articles/2803573/). It runs as a lightweight FastAPI service on any Mac where Things is installed.

## Installation

No install required — run directly with [`uvx`](https://docs.astral.sh/uv/):

```sh
uvx things-api
```

Or install with pip:

```sh
pip install things-api
```

## Configuration

All settings are read from environment variables or a `.env` file in the working directory. Copy `env.example` to `.env` and adjust as needed.

| Variable | Required | Default | Description |
|---|---|---|---|
| `THINGS_API_HOST` | No | `0.0.0.0` | Address the server binds to |
| `THINGS_API_PORT` | No | `5225` | Port the server listens on |
| `THINGS_API_TOKEN` | **Yes** | — | Bearer token used to authenticate every request |
| `THINGS_AUTH_TOKEN` | No | — | Things URL scheme auth token — enables write operations (create, update, complete, cancel) |
| `THINGS_DB_PATH` | No | Auto-detected | Custom path to the Things SQLite database |
| `THINGS_VERIFY_TIMEOUT` | No | `0.5` | Seconds to wait after a write before reading back the result |

> **Note:** Without `THINGS_AUTH_TOKEN`, the API operates in read-only mode. Write endpoints (`POST`, `PUT`, `DELETE`) return `503 Service Unavailable`. To obtain an auth token, open **Things > Settings > General > Enable Things URLs** and copy the token.

## Quick start

Start the server:

```sh
export THINGS_API_TOKEN="my-secret-token"
things-api
```

Health check:

```sh
curl http://localhost:5225/health \
  -H "Authorization: Bearer my-secret-token"
```

List today's tasks:

```sh
curl http://localhost:5225/today \
  -H "Authorization: Bearer my-secret-token"
```

Create a new todo (requires `THINGS_AUTH_TOKEN`):

```sh
curl -X POST http://localhost:5225/todos \
  -H "Authorization: Bearer my-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "when": "today", "tags": ["errands"]}'
```

## API reference

Every endpoint requires a valid `Authorization: Bearer <token>` header.

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns service status and whether read/write are available |

### Todos

| Method | Path | Description |
|---|---|---|
| `GET` | `/todos` | List all incomplete todos. Supports query params: `project_id`, `area_id`, `tag`, `include_checklist` |
| `GET` | `/todos/{id}` | Get a specific todo by UUID |
| `POST` | `/todos` | Create a new todo (returns `202 Accepted`). Body fields: `title` (required), `notes`, `when`, `deadline`, `tags`, `checklist_items`, `list_id`, `list_title`, `heading`, `heading_id` |
| `PUT` | `/todos/{id}` | Update an existing todo. Body fields: `title`, `notes`, `prepend_notes`, `append_notes`, `when`, `deadline`, `tags`, `add_tags`, `checklist_items`, `prepend_checklist_items`, `append_checklist_items`, `list_id`, `list_title`, `heading`, `heading_id` |
| `DELETE` | `/todos/{id}` | **Irreversible.** Complete or cancel a todo. Optional body: `{"action": "complete"}` (default) or `{"action": "cancel"}` |

### Projects

| Method | Path | Description |
|---|---|---|
| `GET` | `/projects` | List all projects |
| `GET` | `/projects/{id}` | Get a project by UUID |
| `POST` | `/projects` | Create a new project (returns `202 Accepted`). Body fields: `title` (required), `notes`, `when`, `deadline`, `tags`, `area_id`, `area_title`, `todos` |
| `PUT` | `/projects/{id}` | Update an existing project. Body fields: `title`, `notes`, `prepend_notes`, `append_notes`, `when`, `deadline`, `tags`, `add_tags`, `area_id`, `area_title` |
| `DELETE` | `/projects/{id}` | **Irreversible.** Complete or cancel a project. Optional body: `{"action": "complete"}` or `{"action": "cancel"}` |

### Smart lists

| Method | Path | Description |
|---|---|---|
| `GET` | `/inbox` | Inbox todos |
| `GET` | `/today` | Today's todos |
| `GET` | `/upcoming` | Upcoming todos |
| `GET` | `/anytime` | Anytime todos |
| `GET` | `/someday` | Someday todos |
| `GET` | `/logbook` | Completed todos. Supports query params: `period` (e.g. `3d`, `1w`), `limit` |

### Areas

| Method | Path | Description |
|---|---|---|
| `GET` | `/areas` | List all areas. Supports query param: `include_items` |

### Tags

| Method | Path | Description |
|---|---|---|
| `GET` | `/tags` | List all tags. Supports query param: `include_items` |
| `GET` | `/tags/{tag}/items` | Get all items with a specific tag |

### Search

| Method | Path | Description |
|---|---|---|
| `GET` | `/search?q=` | Full-text search across todos |
| `GET` | `/search/advanced` | Filtered search. Supports query params: `status`, `tag`, `area`, `type`, `start_date`, `deadline`, `last` |

## Running as a service

Create a launchd agent so Things API starts automatically at login.

**1. Create the plist file:**

```sh
mkdir -p ~/Library/LaunchAgents
```

Save the following as `~/Library/LaunchAgents/com.jaydenk.things-api.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jaydenk.things-api</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/sh</string>
        <string>-c</string>
        <string>uvx things-api</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>THINGS_API_TOKEN</key>
        <string>YOUR_TOKEN_HERE</string>
        <!-- uncomment to enable writes -->
        <!-- <key>THINGS_AUTH_TOKEN</key>
        <string>YOUR_THINGS_AUTH_TOKEN</string> -->
    </dict>

    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/things-api.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/things-api.err</string>
</dict>
</plist>
```

**2. Load the agent:**

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jaydenk.things-api.plist
```

**3. Stop and unload:**

```sh
launchctl bootout gui/$(id -u)/com.jaydenk.things-api
```

## n8n integration

Things API works well as a backend for [n8n](https://n8n.io/) workflows. Use an **HTTP Request** node with the following configuration:

| Setting | Value |
|---|---|
| Method | `GET` / `POST` / `PUT` / `DELETE` |
| URL | `http://<host>:5225/today` (or any endpoint) |
| Authentication | Header Auth |
| Header Name | `Authorization` |
| Header Value | `Bearer YOUR_TOKEN_HERE` |
| Response Format | JSON |

For write operations, set the body content type to JSON and pass the relevant fields (e.g. `{"title": "New task", "when": "today"}`).

## Limitations

- **macOS only** — Things 3 is a Mac/iOS app and the SQLite database lives on macOS. The API must run on the same machine.
- **GUI session required for writes** — Write operations use `open things:///...` to invoke the URL scheme, which requires an active GUI session. Writes will fail over a headless SSH connection.
- **No true deletion** — Things does not expose a delete operation. The `DELETE` endpoints complete or cancel items instead.
- **URL scheme rate limits** — Rapid successive writes may be throttled or dropped by Things. The `THINGS_VERIFY_TIMEOUT` setting controls how long the API waits before reading back results, but high-throughput writes are not recommended.

## Development

Clone the repository and set up a virtual environment:

```sh
git clone https://github.com/jaydenk/things-api.git
cd things-api
uv venv
uv pip install -e ".[test]"
```

Run the test suite:

```sh
uv run pytest -v
```

## Licence

[MIT](./LICENSE)
