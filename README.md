# Things API

REST API for [Things 3](https://culturedcode.com/things/) — expose your tasks over HTTP.

Things API reads directly from the Things SQLite database via [things.py](https://github.com/thingsapi/things.py) and writes back through the [Things URL scheme](https://culturedcode.com/things/support/articles/2803573/). It runs as a lightweight FastAPI service on any Mac where Things is installed, giving you full programmatic access to your tasks from tools like [n8n](https://n8n.io/), [curl](https://curl.se/), or any HTTP client.

## Installation

No install required — run directly with [`uvx`](https://docs.astral.sh/uv/):

```sh
uvx things-api
```

Or install with pip:

```sh
pip install things-api
```

**Requirements:** macOS with [Things 3](https://culturedcode.com/things/) installed, Python 3.12+.

## Configuration

Copy `env.example` to `.env` and set your API token:

```sh
cp env.example .env
```

The only required setting is `THINGS_API_TOKEN` — a secret string that authenticates every request:

| Variable | Required | Default | Description |
|---|---|---|---|
| `THINGS_API_TOKEN` | **Yes** | — | Bearer token for API authentication |
| `THINGS_AUTH_TOKEN` | No | — | Things URL scheme auth token — enables write operations |
| `THINGS_API_PORT` | No | `5225` | Port the server listens on |

Without `THINGS_AUTH_TOKEN`, the API runs in **read-only mode** — write endpoints return `503`. To get a Things auth token, open **Things > Settings > General > Enable Things URLs** and copy the token.

See [docs/configuration.md](docs/configuration.md) for the full list of configuration options.

## Quick start

Start the server:

```sh
things-api
```

List today's tasks:

```sh
curl http://localhost:5225/today \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Create a todo (requires `THINGS_AUTH_TOKEN`):

```sh
curl -X POST http://localhost:5225/todos \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "when": "today"}'
```

Check the server is healthy:

```sh
curl http://localhost:5225/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

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
