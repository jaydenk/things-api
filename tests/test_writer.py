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

    with pytest.raises(RuntimeError, match="Write operation failed"):
        await writer.create_todo(title="Fail")


def test_build_add_url(writer):
    url = writer._build_url("add", title="Test", when="today", tags=["a", "b"])
    assert url.startswith("things:///add?")
    assert "title=Test" in url
    assert "when=today" in url
