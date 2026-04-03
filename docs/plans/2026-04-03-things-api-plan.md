# Things API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:executing-plans to implement this plan task-by-task.

**Goal:** Build a REST API that exposes Things 3 task management over HTTP, using `things.py` for reads and the Things URL scheme for writes.

**Architecture:** FastAPI app with router-per-resource, services layer separating read (things.py SQLite) from write (URL scheme subprocess). Bearer token auth on all endpoints.

**Tech Stack:** Python 3.12+, FastAPI 0.135.x, things.py 1.0.x, pydantic-settings 2.13.x, uvicorn, pytest + httpx for testing.

**Design doc:** `docs/plans/2026-04-03-things-api-design.md`

---

### Task 0: Project Scaffold

**Files:**
- Create: `things-api/pyproject.toml`
- Create: `things-api/src/things_api/__init__.py`
- Create: `things-api/env.example`
- Create: `things-api/.gitignore`
- Create: `things-api/LICENSE`

**Step 1: Create project directory and pyproject.toml**

```bash
mkdir -p things-api/src/things_api things-api/tests
```

```toml
# things-api/pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "things-api"
version = "0.1.0"
description = "REST API for Things 3 — expose your tasks over HTTP"
readme = "README.md"
license = "MIT"
requires-python = ">=3.12"
authors = [{ name = "Jayden Kerr" }]
keywords = ["things", "things3", "api", "rest", "tasks", "gtd"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: MacOS X",
    "Framework :: FastAPI",
    "License :: OSI Approved :: MIT License",
    "Operating System :: MacOS",
    "Programming Language :: Python :: 3.12",
    "Topic :: Office/Business :: Scheduling",
]
dependencies = [
    "fastapi>=0.135,<1",
    "uvicorn[standard]>=0.34,<1",
    "things.py>=1.0,<2",
    "pydantic-settings>=2.13,<3",
]

[project.optional-dependencies]
test = [
    "pytest>=8",
    "pytest-asyncio>=0.25",
    "httpx>=0.28",
]

[project.scripts]
things-api = "things_api.app:main"

[project.urls]
Homepage = "https://github.com/jaydenk/things-api"
Issues = "https://github.com/jaydenk/things-api/issues"
```

**Step 2: Create __init__.py**

```python
# things-api/src/things_api/__init__.py
"""REST API for Things 3."""
```

**Step 3: Create env.example**

```dotenv
# things-api/env.example
THINGS_API_HOST=0.0.0.0
THINGS_API_PORT=5225
THINGS_API_TOKEN=change-me-to-a-secure-random-string
# THINGS_AUTH_TOKEN=your-things-url-scheme-token (enables writes)
# THINGS_DB_PATH=/custom/path/to/Things.sqlite3
# THINGS_VERIFY_TIMEOUT=0.5
```

**Step 4: Create .gitignore**

```gitignore
# things-api/.gitignore
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.env
TODO.md
```

**Step 5: Create LICENSE (MIT)**

Standard MIT licence with author "Jayden Kerr" and year 2026.

**Step 6: Initialise git and commit**

```bash
cd things-api
git init
git add -A
git commit -m "chore: project scaffold with pyproject.toml and config"
```

---

### Task 1: Config and Settings

**Files:**
- Create: `things-api/src/things_api/config.py`
- Test: `things-api/tests/test_config.py`

**Step 1: Write the failing test**

```python
# things-api/tests/test_config.py
import os
import pytest


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token-123")
    monkeypatch.setenv("THINGS_API_HOST", "127.0.0.1")
    monkeypatch.setenv("THINGS_API_PORT", "9999")

    from things_api.config import Settings

    s = Settings()
    assert s.things_api_token == "test-token-123"
    assert s.things_api_host == "127.0.0.1"
    assert s.things_api_port == 9999


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    from things_api.config import Settings

    s = Settings()
    assert s.things_api_host == "0.0.0.0"
    assert s.things_api_port == 5225
    assert s.things_auth_token is None
    assert s.things_db_path is None
    assert s.things_verify_timeout == 0.5


def test_settings_requires_api_token(monkeypatch):
    monkeypatch.delenv("THINGS_API_TOKEN", raising=False)
    from things_api.config import Settings

    with pytest.raises(Exception):
        Settings()


def test_write_enabled_property(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-token")
    from things_api.config import Settings

    s = Settings()
    assert s.write_enabled is True


def test_write_disabled_without_auth_token(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.delenv("THINGS_AUTH_TOKEN", raising=False)
    from things_api.config import Settings

    s = Settings()
    assert s.write_enabled is False
```

**Step 2: Run test to verify it fails**

Run: `cd things-api && uv run pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'things_api.config'`

**Step 3: Write minimal implementation**

```python
# things-api/src/things_api/config.py
"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Things API configuration.

    All values can be set via environment variables or a .env file.
    """

    things_api_host: str = "0.0.0.0"
    things_api_port: int = 5225
    things_api_token: str
    things_auth_token: str | None = None
    things_db_path: Path | None = None
    things_verify_timeout: float = 0.5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def write_enabled(self) -> bool:
        """Whether write operations are available."""
        return self.things_auth_token is not None
```

**Step 4: Run test to verify it passes**

Run: `cd things-api && uv run pytest tests/test_config.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/things_api/config.py tests/test_config.py
git commit -m "feat: add Settings config with env loading and write_enabled property"
```

---

### Task 2: Auth Middleware

**Files:**
- Create: `things-api/src/things_api/auth.py`
- Test: `things-api/tests/test_auth.py`

**Step 1: Write the failing test**

```python
# things-api/tests/test_auth.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from things_api.auth import require_token


def _make_app(token: str) -> FastAPI:
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint(
        _: None = require_token(token),
    ):
        return {"ok": True}

    return app


def test_valid_token():
    client = TestClient(_make_app("secret"))
    resp = client.get("/test", headers={"Authorization": "Bearer secret"})
    assert resp.status_code == 200


def test_missing_token():
    client = TestClient(_make_app("secret"))
    resp = client.get("/test")
    assert resp.status_code == 401


def test_wrong_token():
    client = TestClient(_make_app("secret"))
    resp = client.get("/test", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


def test_malformed_header():
    client = TestClient(_make_app("secret"))
    resp = client.get("/test", headers={"Authorization": "Token secret"})
    assert resp.status_code == 401
```

**Step 2: Run test to verify it fails**

Run: `cd things-api && uv run pytest tests/test_auth.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# things-api/src/things_api/auth.py
"""Bearer token authentication."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_scheme = HTTPBearer(auto_error=False)


def require_token(expected_token: str):
    """Return a FastAPI dependency that validates a Bearer token."""

    async def _verify(
        credentials: HTTPAuthorizationCredentials | None = Depends(_scheme),
    ) -> None:
        if credentials is None or credentials.credentials != expected_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return Depends(_verify)
```

**Step 4: Run test to verify it passes**

Run: `cd things-api && uv run pytest tests/test_auth.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/things_api/auth.py tests/test_auth.py
git commit -m "feat: add bearer token auth dependency"
```

---

### Task 3: Reader Service

**Files:**
- Create: `things-api/src/things_api/services/__init__.py`
- Create: `things-api/src/things_api/services/reader.py`
- Test: `things-api/tests/test_reader.py`

**Step 1: Write the failing test**

```python
# things-api/tests/test_reader.py
from unittest.mock import patch
import pytest

from things_api.services.reader import ThingsReader


@pytest.fixture
def reader():
    return ThingsReader(db_path=None)


@patch("things_api.services.reader.things")
def test_get_todos(mock_things, reader):
    mock_things.todos.return_value = [
        {"uuid": "abc", "title": "Buy milk", "status": "incomplete"}
    ]
    result = reader.todos()
    assert len(result) == 1
    assert result[0]["title"] == "Buy milk"
    mock_things.todos.assert_called_once()


@patch("things_api.services.reader.things")
def test_get_todos_with_project_filter(mock_things, reader):
    mock_things.todos.return_value = []
    reader.todos(project="proj-uuid")
    mock_things.todos.assert_called_once_with(project="proj-uuid")


@patch("things_api.services.reader.things")
def test_get_by_uuid(mock_things, reader):
    mock_things.get.return_value = {"uuid": "abc", "title": "Test"}
    result = reader.get("abc")
    assert result["uuid"] == "abc"


@patch("things_api.services.reader.things")
def test_get_by_uuid_not_found(mock_things, reader):
    mock_things.get.return_value = None
    result = reader.get("nonexistent")
    assert result is None


@patch("things_api.services.reader.things")
def test_inbox(mock_things, reader):
    mock_things.inbox.return_value = [{"uuid": "x", "title": "Inbox item"}]
    result = reader.inbox()
    assert len(result) == 1


@patch("things_api.services.reader.things")
def test_today(mock_things, reader):
    mock_things.today.return_value = []
    result = reader.today()
    assert result == []


@patch("things_api.services.reader.things")
def test_projects(mock_things, reader):
    mock_things.projects.return_value = [
        {"uuid": "p1", "title": "Project A"}
    ]
    result = reader.projects()
    assert result[0]["title"] == "Project A"


@patch("things_api.services.reader.things")
def test_search(mock_things, reader):
    mock_things.search.return_value = [{"uuid": "s1", "title": "Match"}]
    result = reader.search("Match")
    assert len(result) == 1
    mock_things.search.assert_called_once_with("Match")


@patch("things_api.services.reader.things")
def test_tags(mock_things, reader):
    mock_things.tags.return_value = [{"title": "errand"}]
    result = reader.tags()
    assert result[0]["title"] == "errand"


@patch("things_api.services.reader.things")
def test_areas(mock_things, reader):
    mock_things.areas.return_value = [{"uuid": "a1", "title": "Work"}]
    result = reader.areas()
    assert result[0]["title"] == "Work"


@patch("things_api.services.reader.things")
def test_db_path_passed(mock_things):
    reader = ThingsReader(db_path="/custom/path.sqlite3")
    mock_things.todos.return_value = []
    reader.todos()
    mock_things.todos.assert_called_once_with(filepath="/custom/path.sqlite3")
```

**Step 2: Run test to verify it fails**

Run: `cd things-api && uv run pytest tests/test_reader.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# things-api/src/things_api/services/__init__.py
```

```python
# things-api/src/things_api/services/reader.py
"""Read-only access to Things 3 data via things.py."""

from __future__ import annotations

import things


class ThingsReader:
    """Wraps things.py, injecting db_path when configured."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    def _kwargs(self, **extra) -> dict:
        """Build kwargs, adding filepath if configured."""
        kw = {k: v for k, v in extra.items() if v is not None}
        if self._db_path:
            kw["filepath"] = self._db_path
        return kw

    def todos(self, **filters) -> list[dict]:
        return things.todos(**self._kwargs(**filters))

    def projects(self, **filters) -> list[dict]:
        return things.projects(**self._kwargs(**filters))

    def areas(self, include_items: bool = False) -> list[dict]:
        return things.areas(**self._kwargs(include_items=include_items))

    def tags(self, include_items: bool = False) -> list[dict]:
        return things.tags(**self._kwargs(include_items=include_items))

    def get(self, uuid: str) -> dict | None:
        return things.get(uuid, **self._kwargs())

    def search(self, query: str) -> list[dict]:
        return things.search(query, **self._kwargs())

    def inbox(self) -> list[dict]:
        return things.inbox(**self._kwargs())

    def today(self) -> list[dict]:
        return things.today(**self._kwargs())

    def upcoming(self) -> list[dict]:
        return things.upcoming(**self._kwargs())

    def anytime(self) -> list[dict]:
        return things.anytime(**self._kwargs())

    def someday(self) -> list[dict]:
        return things.someday(**self._kwargs())

    def logbook(self, **filters) -> list[dict]:
        return things.logbook(**self._kwargs(**filters))

    def completed(self, **filters) -> list[dict]:
        return things.completed(**self._kwargs(**filters))

    def canceled(self, **filters) -> list[dict]:
        return things.canceled(**self._kwargs(**filters))

    def trash(self) -> list[dict]:
        return things.trash(**self._kwargs())

    def deadlines(self) -> list[dict]:
        return things.deadlines(**self._kwargs())

    def checklist_items(self, todo_uuid: str) -> list[dict]:
        return things.checklist_items(todo_uuid, **self._kwargs())

    def tags_for_item(self, tag_title: str) -> list[dict]:
        return things.tags(title=tag_title, include_items=True, **self._kwargs())
```

**Step 4: Run test to verify it passes**

Run: `cd things-api && uv run pytest tests/test_reader.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/things_api/services/ tests/test_reader.py
git commit -m "feat: add ThingsReader service wrapping things.py"
```

---

### Task 4: Writer Service

**Files:**
- Create: `things-api/src/things_api/services/writer.py`
- Test: `things-api/tests/test_writer.py`

**Step 1: Write the failing test**

```python
# things-api/tests/test_writer.py
from unittest.mock import patch, AsyncMock
import pytest

from things_api.services.writer import ThingsWriter


@pytest.fixture
def writer():
    return ThingsWriter(auth_token="test-auth-token", verify_timeout=0.0)


@pytest.mark.asyncio
@patch("things_api.services.writer.asyncio.create_subprocess_exec")
async def test_create_todo(mock_exec, writer):
    mock_proc = AsyncMock()
    mock_proc.wait = AsyncMock(return_value=0)
    mock_exec.return_value = mock_proc

    await writer.create_todo(title="Buy milk", when="today")
    mock_exec.assert_called_once()
    call_args = mock_exec.call_args[0]
    assert call_args[0] == "open"
    assert "things:///add" in call_args[1]


@pytest.mark.asyncio
@patch("things_api.services.writer.asyncio.create_subprocess_exec")
async def test_create_todo_with_tags(mock_exec, writer):
    mock_proc = AsyncMock()
    mock_proc.wait = AsyncMock(return_value=0)
    mock_exec.return_value = mock_proc

    await writer.create_todo(title="Test", tags=["errand", "home"])
    call_args = mock_exec.call_args[0]
    assert "errand" in call_args[1]
    assert "home" in call_args[1]


@pytest.mark.asyncio
@patch("things_api.services.writer.asyncio.create_subprocess_exec")
async def test_update_todo(mock_exec, writer):
    mock_proc = AsyncMock()
    mock_proc.wait = AsyncMock(return_value=0)
    mock_exec.return_value = mock_proc

    await writer.update_todo(uuid="abc-123", title="Updated")
    call_args = mock_exec.call_args[0]
    assert "things:///update" in call_args[1]
    assert "id=abc-123" in call_args[1]
    assert "auth-token=test-auth-token" in call_args[1]


@pytest.mark.asyncio
@patch("things_api.services.writer.asyncio.create_subprocess_exec")
async def test_complete_todo(mock_exec, writer):
    mock_proc = AsyncMock()
    mock_proc.wait = AsyncMock(return_value=0)
    mock_exec.return_value = mock_proc

    await writer.complete_todo(uuid="abc-123")
    call_args = mock_exec.call_args[0]
    assert "completed=true" in call_args[1]


@pytest.mark.asyncio
@patch("things_api.services.writer.asyncio.create_subprocess_exec")
async def test_create_project(mock_exec, writer):
    mock_proc = AsyncMock()
    mock_proc.wait = AsyncMock(return_value=0)
    mock_exec.return_value = mock_proc

    await writer.create_project(title="New Project", when="someday")
    call_args = mock_exec.call_args[0]
    assert "things:///add-project" in call_args[1]


@pytest.mark.asyncio
@patch("things_api.services.writer.asyncio.create_subprocess_exec")
async def test_subprocess_failure_raises(mock_exec, writer):
    mock_proc = AsyncMock()
    mock_proc.wait = AsyncMock(return_value=1)
    mock_proc.stderr = AsyncMock()
    mock_proc.stderr.read = AsyncMock(return_value=b"error")
    mock_exec.return_value = mock_proc

    with pytest.raises(RuntimeError, match="URL scheme command failed"):
        await writer.create_todo(title="Fail")


def test_build_add_url(writer):
    url = writer._build_url("add", title="Test", when="today", tags=["a", "b"])
    assert url.startswith("things:///add?")
    assert "title=Test" in url
    assert "when=today" in url
```

**Step 2: Run test to verify it fails**

Run: `cd things-api && uv run pytest tests/test_writer.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# things-api/src/things_api/services/writer.py
"""Write to Things 3 via the URL scheme."""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import quote, urlencode

logger = logging.getLogger(__name__)


class ThingsWriter:
    """Creates and updates Things items via the URL scheme."""

    def __init__(self, auth_token: str, verify_timeout: float = 0.5) -> None:
        self._auth_token = auth_token
        self._verify_timeout = verify_timeout

    def _build_url(self, command: str, **params) -> str:
        """Build a things:/// URL with encoded parameters."""
        filtered = {}
        for key, value in params.items():
            if value is None:
                continue
            url_key = key.replace("_", "-")
            if isinstance(value, list):
                filtered[url_key] = ",".join(str(v) for v in value)
            elif isinstance(value, bool):
                filtered[url_key] = "true" if value else "false"
            else:
                filtered[url_key] = str(value)
        qs = urlencode(filtered, quote_via=quote)
        return f"things:///{command}?{qs}" if qs else f"things:///{command}"

    async def _execute(self, url: str) -> None:
        """Open a Things URL scheme command."""
        redacted = url.replace(self._auth_token, "REDACTED")
        logger.info("Executing: %s", redacted)

        proc = await asyncio.create_subprocess_exec(
            "open", url,
            stderr=asyncio.subprocess.PIPE,
        )
        returncode = await proc.wait()
        if returncode != 0:
            stderr = await proc.stderr.read() if proc.stderr else b""
            raise RuntimeError(
                f"URL scheme command failed (exit {returncode}): {stderr.decode()}"
            )

    async def create_todo(self, **params) -> None:
        url = self._build_url("add", **params)
        await self._execute(url)

    async def update_todo(self, uuid: str, **params) -> None:
        url = self._build_url(
            "update", id=uuid, auth_token=self._auth_token, **params
        )
        await self._execute(url)

    async def complete_todo(self, uuid: str) -> None:
        await self.update_todo(uuid, completed=True)

    async def cancel_todo(self, uuid: str) -> None:
        await self.update_todo(uuid, canceled=True)

    async def create_project(self, **params) -> None:
        url = self._build_url("add-project", **params)
        await self._execute(url)

    async def update_project(self, uuid: str, **params) -> None:
        url = self._build_url(
            "update-project", id=uuid, auth_token=self._auth_token, **params
        )
        await self._execute(url)

    async def complete_project(self, uuid: str) -> None:
        await self.update_project(uuid, completed=True)

    async def cancel_project(self, uuid: str) -> None:
        await self.update_project(uuid, canceled=True)
```

**Step 4: Run test to verify it passes**

Run: `cd things-api && uv run pytest tests/test_writer.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/things_api/services/writer.py tests/test_writer.py
git commit -m "feat: add ThingsWriter service using URL scheme subprocess"
```

---

### Task 5: Pydantic Models

**Files:**
- Create: `things-api/src/things_api/models.py`
- Test: `things-api/tests/test_models.py`

**Step 1: Write the failing test**

```python
# things-api/tests/test_models.py
import pytest
from pydantic import ValidationError

from things_api.models import (
    CreateTodoRequest,
    UpdateTodoRequest,
    CreateProjectRequest,
    DeleteAction,
    DeleteRequest,
    TodoResponse,
    ProjectResponse,
    HealthResponse,
)


def test_create_todo_minimal():
    req = CreateTodoRequest(title="Buy milk")
    assert req.title == "Buy milk"
    assert req.when is None
    assert req.tags is None


def test_create_todo_full():
    req = CreateTodoRequest(
        title="Buy milk",
        notes="Low fat",
        when="today",
        deadline="2026-04-10",
        tags=["errand"],
        checklist_items=["Whole milk", "Skim milk"],
        list_id="proj-uuid",
        heading="Groceries",
    )
    assert req.tags == ["errand"]
    assert len(req.checklist_items) == 2


def test_create_todo_requires_title():
    with pytest.raises(ValidationError):
        CreateTodoRequest()


def test_update_todo_all_optional():
    req = UpdateTodoRequest()
    assert req.title is None


def test_update_todo_append_notes():
    req = UpdateTodoRequest(append_notes="Added later")
    assert req.append_notes == "Added later"


def test_create_project_minimal():
    req = CreateProjectRequest(title="New Project")
    assert req.title == "New Project"


def test_delete_request_defaults_to_complete():
    req = DeleteRequest()
    assert req.action == DeleteAction.COMPLETE


def test_delete_request_cancel():
    req = DeleteRequest(action="cancel")
    assert req.action == DeleteAction.CANCEL


def test_todo_response():
    resp = TodoResponse(uuid="abc", title="Test", status="incomplete")
    assert resp.uuid == "abc"


def test_health_response():
    resp = HealthResponse(status="healthy", read=True, write=False)
    assert resp.write is False
```

**Step 2: Run test to verify it fails**

Run: `cd things-api && uv run pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# things-api/src/things_api/models.py
"""Pydantic request/response models for the Things API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


# --- Requests ---


class CreateTodoRequest(BaseModel):
    """Create a new todo."""

    title: str
    notes: str | None = None
    when: str | None = None
    deadline: str | None = None
    tags: list[str] | None = None
    checklist_items: list[str] | None = None
    list_id: str | None = None
    list_title: str | None = None
    heading: str | None = None
    heading_id: str | None = None


class UpdateTodoRequest(BaseModel):
    """Update an existing todo. All fields optional."""

    title: str | None = None
    notes: str | None = None
    prepend_notes: str | None = None
    append_notes: str | None = None
    when: str | None = None
    deadline: str | None = None
    tags: list[str] | None = None
    add_tags: list[str] | None = None
    checklist_items: list[str] | None = None
    prepend_checklist_items: list[str] | None = None
    append_checklist_items: list[str] | None = None
    list_id: str | None = None
    list_title: str | None = None
    heading: str | None = None
    heading_id: str | None = None


class CreateProjectRequest(BaseModel):
    """Create a new project."""

    title: str
    notes: str | None = None
    when: str | None = None
    deadline: str | None = None
    tags: list[str] | None = None
    area_id: str | None = None
    area_title: str | None = None
    todos: list[str] | None = None


class UpdateProjectRequest(BaseModel):
    """Update an existing project. All fields optional."""

    title: str | None = None
    notes: str | None = None
    prepend_notes: str | None = None
    append_notes: str | None = None
    when: str | None = None
    deadline: str | None = None
    tags: list[str] | None = None
    add_tags: list[str] | None = None
    area_id: str | None = None
    area_title: str | None = None


class DeleteAction(str, Enum):
    """Action when deleting (Things has no true deletion)."""

    COMPLETE = "complete"
    CANCEL = "cancel"


class DeleteRequest(BaseModel):
    """Body for DELETE endpoints."""

    action: DeleteAction = DeleteAction.COMPLETE


# --- Responses ---


class TodoResponse(BaseModel):
    """A Things todo item."""

    model_config = {"extra": "allow"}

    uuid: str
    title: str
    status: str


class ProjectResponse(BaseModel):
    """A Things project."""

    model_config = {"extra": "allow"}

    uuid: str
    title: str
    status: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    read: bool
    write: bool
```

**Step 4: Run test to verify it passes**

Run: `cd things-api && uv run pytest tests/test_models.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/things_api/models.py tests/test_models.py
git commit -m "feat: add Pydantic request/response models"
```

---

### Task 6: App Factory and Health Endpoint

**Files:**
- Create: `things-api/src/things_api/app.py`
- Test: `things-api/tests/test_app.py`

**Step 1: Write the failing test**

```python
# things-api/tests/test_app.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    from things_api.app import create_app

    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["read"] is True
    assert data["write"] is True


def test_health_requires_auth(client):
    resp = client.get("/health")
    assert resp.status_code == 401


def test_openapi_docs_accessible(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `cd things-api && uv run pytest tests/test_app.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# things-api/src/things_api/app.py
"""FastAPI application factory and entrypoint."""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from things_api.auth import require_token
from things_api.config import Settings
from things_api.models import HealthResponse
from things_api.services.reader import ThingsReader
from things_api.services.writer import ThingsWriter

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="Things API",
        description="REST API for Things 3 — expose your tasks over HTTP",
        version="0.1.0",
        dependencies=[require_token(settings.things_api_token)],
    )

    reader = ThingsReader(
        db_path=str(settings.things_db_path) if settings.things_db_path else None,
    )
    writer = (
        ThingsWriter(
            auth_token=settings.things_auth_token,
            verify_timeout=settings.things_verify_timeout,
        )
        if settings.write_enabled
        else None
    )

    app.state.settings = settings
    app.state.reader = reader
    app.state.writer = writer

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(
            status="healthy",
            read=True,
            write=settings.write_enabled,
        )

    # Routers registered here as they are built in subsequent tasks

    return app


def main() -> None:
    """CLI entrypoint."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings()
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.things_api_host,
        port=settings.things_api_port,
    )
```

**Step 4: Run test to verify it passes**

Run: `cd things-api && uv run pytest tests/test_app.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/things_api/app.py tests/test_app.py
git commit -m "feat: add app factory with health endpoint and CLI entrypoint"
```

---

### Task 7: Todos Router

**Files:**
- Create: `things-api/src/things_api/routers/__init__.py`
- Create: `things-api/src/things_api/routers/todos.py`
- Modify: `things-api/src/things_api/app.py` (register router)
- Test: `things-api/tests/test_router_todos.py`

**Step 1: Write the failing test**

```python
# things-api/tests/test_router_todos.py
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-auth")

    with patch("things_api.services.reader.things") as mock_things:
        mock_things.todos.return_value = [
            {"uuid": "t1", "title": "Buy milk", "status": "incomplete"}
        ]
        mock_things.get.return_value = {
            "uuid": "t1", "title": "Buy milk", "status": "incomplete"
        }

        from things_api.app import create_app

        app = create_app()
        yield TestClient(app)


def test_list_todos(client):
    resp = client.get("/todos", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["title"] == "Buy milk"


def test_get_todo_by_id(client):
    resp = client.get("/todos/t1", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["uuid"] == "t1"


def test_create_todo(client):
    with patch.object(
        client.app.state.writer, "create_todo", new_callable=AsyncMock
    ):
        resp = client.post(
            "/todos",
            json={"title": "New task"},
            headers=AUTH,
        )
        assert resp.status_code in (201, 202)


def test_create_todo_requires_title(client):
    resp = client.post("/todos", json={}, headers=AUTH)
    assert resp.status_code == 422
```

**Step 2: Run test to verify it fails**

Run: `cd things-api && uv run pytest tests/test_router_todos.py -v`
Expected: FAIL (404 — no router registered)

**Step 3: Write minimal implementation**

Create `things-api/src/things_api/routers/__init__.py` (empty).

Create `things-api/src/things_api/routers/todos.py`:

```python
# things-api/src/things_api/routers/todos.py
"""Todo CRUD endpoints."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request, status

from things_api.models import (
    CreateTodoRequest,
    DeleteAction,
    DeleteRequest,
    UpdateTodoRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("")
async def list_todos(
    request: Request,
    project_id: str | None = None,
    area_id: str | None = None,
    tag: str | None = None,
    include_checklist: bool = False,
):
    """List all incomplete todos, with optional filters."""
    reader = request.app.state.reader
    filters = {}
    if project_id:
        filters["project"] = project_id
    if area_id:
        filters["area"] = area_id
    if tag:
        filters["tag"] = tag
    if include_checklist:
        filters["include_items"] = True
    return reader.todos(**filters)


@router.get("/{todo_id}")
async def get_todo(request: Request, todo_id: str):
    """Get a specific todo by ID."""
    result = request.app.state.reader.get(todo_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_todo(request: Request, body: CreateTodoRequest):
    """Create a new todo."""
    writer = request.app.state.writer
    if writer is None:
        raise HTTPException(
            status_code=503, detail="Write operations not configured"
        )

    params = body.model_dump(exclude_none=True)
    if "checklist_items" in params:
        params["checklist_items"] = "\n".join(params["checklist_items"])

    await writer.create_todo(**params)

    await asyncio.sleep(request.app.state.settings.things_verify_timeout)
    results = request.app.state.reader.search(body.title)
    for item in results:
        if item.get("title") == body.title:
            return item

    return {"status": "accepted", "title": body.title}


@router.put("/{todo_id}")
async def update_todo(request: Request, todo_id: str, body: UpdateTodoRequest):
    """Update an existing todo."""
    writer = request.app.state.writer
    if writer is None:
        raise HTTPException(
            status_code=503, detail="Write operations not configured"
        )

    existing = request.app.state.reader.get(todo_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    params = body.model_dump(exclude_none=True)
    for list_field in (
        "checklist_items",
        "prepend_checklist_items",
        "append_checklist_items",
    ):
        if list_field in params:
            params[list_field] = "\n".join(params[list_field])

    await writer.update_todo(uuid=todo_id, **params)

    await asyncio.sleep(request.app.state.settings.things_verify_timeout)
    updated = request.app.state.reader.get(todo_id)
    return updated if updated else {"status": "accepted", "uuid": todo_id}


@router.delete("/{todo_id}")
async def delete_todo(
    request: Request, todo_id: str, body: DeleteRequest | None = None
):
    """Complete or cancel a todo."""
    writer = request.app.state.writer
    if writer is None:
        raise HTTPException(
            status_code=503, detail="Write operations not configured"
        )

    existing = request.app.state.reader.get(todo_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    action = body.action if body else DeleteAction.COMPLETE
    if action == DeleteAction.CANCEL:
        await writer.cancel_todo(uuid=todo_id)
    else:
        await writer.complete_todo(uuid=todo_id)

    return {"status": action.value, "uuid": todo_id}
```

Add to `app.py` — inside `create_app()`, after the health endpoint:

```python
from things_api.routers import todos
app.include_router(todos.router)
```

**Step 4: Run test to verify it passes**

Run: `cd things-api && uv run pytest tests/test_router_todos.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/things_api/routers/ tests/test_router_todos.py src/things_api/app.py
git commit -m "feat: add todos CRUD router"
```

---

### Task 8: Projects Router

**Files:**
- Create: `things-api/src/things_api/routers/projects.py`
- Modify: `things-api/src/things_api/app.py` (register router)
- Test: `things-api/tests/test_router_projects.py`

Same pattern as Task 7 but for projects:
- `GET /projects` calls `reader.projects()`
- `GET /projects/{id}` calls `reader.get()` then verifies it's a project
- `POST /projects` calls `writer.create_project()`
- `PUT /projects/{id}` calls `writer.update_project()`
- `DELETE /projects/{id}` calls `writer.complete_project()` or `writer.cancel_project()`
- Convert `todos` list to newline-separated string for URL scheme `to_dos` parameter
- Convert `area_title` to `area` in the writer params (URL scheme uses `area` not `area-title`)

**Steps:** Write failing test, verify fail, implement, verify pass, commit.

Register in `app.py`:
```python
from things_api.routers import projects
app.include_router(projects.router)
```

**Commit message:** `feat: add projects CRUD router`

---

### Task 9: Lists Router

**Files:**
- Create: `things-api/src/things_api/routers/lists.py`
- Modify: `things-api/src/things_api/app.py` (register router)
- Test: `things-api/tests/test_router_lists.py`

Read-only endpoints, thin wrappers around reader methods:

| Endpoint | Reader call |
|----------|------------|
| `GET /inbox` | `reader.inbox()` |
| `GET /today` | `reader.today()` |
| `GET /upcoming` | `reader.upcoming()` |
| `GET /anytime` | `reader.anytime()` |
| `GET /someday` | `reader.someday()` |
| `GET /logbook?period=7d` | `reader.logbook(last=period)` |

**Steps:** Write failing test, verify fail, implement, verify pass, commit.

**Commit message:** `feat: add list endpoints (inbox, today, upcoming, etc.)`

---

### Task 10: Tags and Areas Routers

**Files:**
- Create: `things-api/src/things_api/routers/tags.py`
- Create: `things-api/src/things_api/routers/areas.py`
- Modify: `things-api/src/things_api/app.py` (register routers)
- Test: `things-api/tests/test_router_tags.py`
- Test: `things-api/tests/test_router_areas.py`

Read-only:

| Endpoint | Reader call |
|----------|------------|
| `GET /tags?include_items=true` | `reader.tags(include_items=True)` |
| `GET /tags/{tag}/items` | `reader.tags_for_item(tag_title=tag)` |
| `GET /areas?include_items=true` | `reader.areas(include_items=True)` |

**Steps:** Write failing tests, verify fail, implement, verify pass, commit.

**Commit message:** `feat: add tags and areas read-only routers`

---

### Task 11: Search Router

**Files:**
- Create: `things-api/src/things_api/routers/search.py`
- Modify: `things-api/src/things_api/app.py` (register router)
- Test: `things-api/tests/test_router_search.py`

| Endpoint | Reader call |
|----------|------------|
| `GET /search?q=...` | `reader.search(query=q)` |
| `GET /search/advanced?status=&tag=&area=&type=&start_date=&deadline=&last=` | `reader.todos(**filters)` |

The advanced search maps query parameters directly to `things.py` kwargs.

**Steps:** Write failing tests, verify fail, implement, verify pass, commit.

**Commit message:** `feat: add search and advanced search endpoints`

---

### Task 12: README and Documentation

**Files:**
- Create: `things-api/README.md`

Structure (following `fantastical-mcp` conventions):

1. **What it does** — one-paragraph summary
2. **Installation** — `uvx things-api`, `pip install things-api`
3. **Configuration** — env var table from design doc
4. **Quick start** — curl examples for health, list todos, create todo
5. **API Reference** — full endpoint table
6. **Running as a service** — launchd plist instructions
7. **n8n integration** — HTTP Request node config example with bearer token
8. **Limitations** — macOS only, GUI session required for writes, no true deletion, 250-item/10s URL scheme rate limit
9. **Development** — clone, `uv venv`, `uv pip install -e ".[test]"`, run tests
10. **Licence** — MIT

**Commit message:** `docs: add README with installation, configuration, and API reference`

---

### Task 13: launchd Plist Template

**Files:**
- Create: `things-api/com.things-api.server.plist`

Ready-to-use launchd agent plist:
- `ProgramArguments`: path to `uvx` with `things-api`
- `KeepAlive: true`
- `StandardOutPath` / `StandardErrorPath`: `~/Library/Logs/things-api.log`
- `EnvironmentVariables`: `THINGS_API_TOKEN`, `THINGS_AUTH_TOKEN` placeholders
- Document `launchctl bootstrap`/`bootout` in README

**Commit message:** `chore: add launchd plist template for persistent service`

---

### Task 14: Final Integration and Smoke Test

**Steps:**

1. Run full test suite:
   ```bash
   cd things-api && uv run pytest -v
   ```
   Expected: All tests pass

2. Start the server:
   ```bash
   THINGS_API_TOKEN=test123 uv run things-api
   ```

3. Smoke test with curl (in another terminal):
   ```bash
   curl -s -H "Authorization: Bearer test123" http://localhost:5225/health | python3 -m json.tool
   curl -s -H "Authorization: Bearer test123" http://localhost:5225/today | python3 -m json.tool
   curl -s -H "Authorization: Bearer test123" http://localhost:5225/todos | python3 -m json.tool
   ```

4. Test write (requires THINGS_AUTH_TOKEN):
   ```bash
   curl -s -X POST -H "Authorization: Bearer test123" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test from Things API","when":"today"}' \
     http://localhost:5225/todos | python3 -m json.tool
   ```

5. Verify task appeared in Things 3

6. Final commit if any fixes needed

**Commit message:** `chore: integration smoke test pass`
