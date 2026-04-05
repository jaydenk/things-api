# Things API

REST API for [Things 3](https://culturedcode.com/things/) — expose your tasks over HTTP.

Things API reads directly from the Things SQLite database via [things.py](https://github.com/thingsapi/things.py) and writes back through the [Things URL scheme](https://culturedcode.com/things/support/articles/2803573/). It runs as a lightweight FastAPI service on any Mac where Things is installed, giving you full programmatic access to your tasks from tools like [n8n](https://n8n.io/), [curl](https://curl.se/), or any HTTP client.

## Getting started

**Requirements:** macOS with [Things 3](https://culturedcode.com/things/) installed and Python 3.12+.

### 1. Install

Run directly with [`uvx`](https://docs.astral.sh/uv/) (no install needed):

```sh
uvx things-api
```

Or install with pip:

```sh
pip install things-api
```

Or clone the repo for development:

```sh
git clone https://github.com/jaydenk/things-api.git
cd things-api
uv venv && uv pip install -e .
```

### 2. Configure

Run the setup wizard:

```sh
things-api init
```

This generates an API token, checks your Things URL scheme settings, and writes the config to `~/.config/things-api/config`. If you skip this step, the wizard runs automatically on first launch.

See [docs/configuration.md](docs/configuration.md) for all configuration options.

### 3. Run

```sh
things-api
```

Override settings on the fly:

```sh
things-api --token my-token --port 8080
```

The server starts on `http://localhost:5225` by default.

### 4. Try it

```sh
# Health check
curl http://localhost:5225/health \
  -H "Authorization: Bearer YOUR_TOKEN"

# List today's tasks
curl http://localhost:5225/today \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create a todo (requires THINGS_AUTH_TOKEN)
curl -X POST http://localhost:5225/todos \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "when": "today"}'
```

To run the server persistently (auto-start at login, auto-restart on crash), see the [deployment guide](docs/deployment.md).

## Endpoints overview

Every endpoint requires a valid `Authorization: Bearer <token>` header.

| Resource | Endpoints | Description |
|---|---|---|
| **Todos** | `GET` `POST` `PUT` `DELETE` `/todos` | Full CRUD for todos |
| **Projects** | `GET` `POST` `PUT` `DELETE` `/projects` | Full CRUD for projects |
| **Smart lists** | `GET` `/inbox` `/today` `/upcoming` `/anytime` `/someday` `/logbook` | Read-only access to Things smart lists |
| **Tags** | `GET` `/tags` | List tags and items by tag |
| **Areas** | `GET` `/areas` | List areas |
| **Search** | `GET` `/search` `/search/advanced` | Full-text and filtered search |
| **Health** | `GET` `/health` | Service status and database connectivity |

> **Note:** `DELETE` on todos and projects is **irreversible** — it completes or cancels the item. Things 3 does not support true deletion.

See [docs/api-reference.md](docs/api-reference.md) for full endpoint details, request/response schemas, and query parameters.

## Limitations

- **macOS only** — Things 3 is a Mac app. The API must run on the same machine.
- **GUI session required for writes** — Write operations invoke the Things URL scheme, which requires an active GUI session.
- **No true deletion** — `DELETE` endpoints complete or cancel items instead.

## Further documentation

- [Configuration reference](docs/configuration.md) — All environment variables and their defaults
- [API reference](docs/api-reference.md) — Full endpoint documentation with request/response details
- [Deployment guide](docs/deployment.md) — Running as a launchd service, n8n integration
- [Development guide](docs/development.md) — Setting up a dev environment, running tests
- [Changelog](CHANGELOG.md) — Version history

## Licence

[MIT](./LICENSE)
