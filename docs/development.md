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
uv run things-api init              # First-time setup
uv run things-api                   # Start the server
uv run things-api --token dev-token # Override token for testing
```

The server starts on `http://localhost:5225`.

## Project structure

```
src/things_api/
├── app.py              # FastAPI app factory
├── auth.py             # Bearer token authentication
├── cli.py              # Click CLI (entrypoint)
├── config.py           # Settings and config file path constants
├── init.py             # Setup wizard (token generation, Things detection)
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
