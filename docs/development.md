# Development

## Setup

Clone the repository and install dependencies:

```sh
git clone https://github.com/jaydenk/things-api.git
cd things-api
uv venv
uv pip install -e ".[test]"
```

## Running tests

```sh
uv run pytest -v
```

Tests mock the `things.py` library and subprocess calls — you don't need Things 3 installed to run them.

## Running locally

```sh
THINGS_API_TOKEN=dev-token uv run things-api
```

The server starts on `http://localhost:5225`.

## Project structure

```
src/things_api/
├── app.py              # FastAPI app factory and CLI entrypoint
├── auth.py             # Bearer token authentication
├── config.py           # Settings (pydantic-settings)
├── models.py           # Pydantic request/response schemas
├── ratelimit.py        # Auth rate limiting middleware
├── routers/
│   ├── todos.py        # CRUD for todos
│   ├── projects.py     # CRUD for projects
│   ├── lists.py        # Inbox, today, upcoming, anytime, someday, logbook
│   ├── tags.py         # Tag endpoints
│   ├── areas.py        # Area endpoints
│   └── search.py       # Search endpoints
└── services/
    ├── reader.py       # things.py wrapper (reads from SQLite)
    └── writer.py       # URL scheme subprocess (writes via Things app)
```
