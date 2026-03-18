"""Tests for LocalProcessManager."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ariatuc.core.local_process_manager import (
    LocalProcessManager,
    ProcessError,
    ProcessState,
)


@pytest.mark.asyncio
async def test_process_manager_initialization():
    """Test LocalProcessManager initialization."""
    manager = LocalProcessManager()
    assert manager._processes == {}
    assert manager._monitoring_tasks == {}


@pytest.mark.asyncio
async def test_start_process_success():
    """Test starting a process successfully."""
    manager = LocalProcessManager()

    mock_process = MagicMock()
    mock_process.pid = 12345
    mock_process.returncode = None

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_process

        success = await manager.start_process(
            server_name="test",
            aria2c_path="aria2c",
            rpc_port=6800,
            rpc_secret="secret",
            session_file=Path("/tmp/test.session"),
            options={"max-concurrent-downloads": 5},
        )

        assert success is True
        assert "test" in manager._processes
        assert manager._processes["test"].state == ProcessState.RUNNING
        assert manager._processes["test"].pid == 12345


@pytest.mark.asyncio
async def test_start_process_already_running():
    """Test starting a process that's already running."""
    manager = LocalProcessManager()

    # Set up existing process
    manager._processes["test"] = MagicMock()
    manager._processes["test"].state = ProcessState.RUNNING

    success = await manager.start_process(
        server_name="test",
        aria2c_path="aria2c",
        rpc_port=6800,
        rpc_secret=None,
        session_file=Path("/tmp/test.session"),
    )

    assert success is False


@pytest.mark.asyncio
async def test_start_process_immediate_exit():
    """Test starting a process that exits immediately."""
    manager = LocalProcessManager()

    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"error message"))

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_process

        success = await manager.start_process(
            server_name="test",
            aria2c_path="aria2c",
            rpc_port=6800,
            rpc_secret=None,
            session_file=Path("/tmp/test.session"),
        )

        assert success is False
        assert manager._processes["test"].state == ProcessState.ERROR


@pytest.mark.asyncio
async def test_stop_process_graceful():
    """Test stopping a process gracefully."""
    manager = LocalProcessManager()

    mock_process = MagicMock()
    mock_process.terminate = MagicMock()
    mock_process.wait = AsyncMock()

    manager._processes["test"] = MagicMock()
    manager._processes["test"].state = ProcessState.RUNNING
    manager._processes["test"].process = mock_process

    success = await manager.stop_process("test", force=False, timeout=10)

    assert success is True
    mock_process.terminate.assert_called_once()
    assert manager._processes["test"].state == ProcessState.STOPPED


@pytest.mark.asyncio
async def test_stop_process_force():
    """Test force stopping a process."""
    manager = LocalProcessManager()

    mock_process = MagicMock()
    mock_process.kill = MagicMock()
    mock_process.wait = AsyncMock()

    manager._processes["test"] = MagicMock()
    manager._processes["test"].state = ProcessState.RUNNING
    manager._processes["test"].process = mock_process

    success = await manager.stop_process("test", force=True, timeout=10)

    assert success is True
    mock_process.kill.assert_called_once()
    assert manager._processes["test"].state == ProcessState.STOPPED


@pytest.mark.asyncio
async def test_stop_process_not_running():
    """Test stopping a process that's not running."""
    manager = LocalProcessManager()

    manager._processes["test"] = MagicMock()
    manager._processes["test"].state = ProcessState.STOPPED

    success = await manager.stop_process("test")

    assert success is False


@pytest.mark.asyncio
async def test_restart_process():
    """Test restarting a process."""
    manager = LocalProcessManager()

    # Setup existing process
    mock_process = MagicMock()
    mock_process.terminate = MagicMock()
    mock_process.wait = AsyncMock()

    manager._processes["test"] = MagicMock()
    manager._processes["test"].state = ProcessState.RUNNING
    manager._processes["test"].process = mock_process

    # Mock the start
    new_mock_process = MagicMock()
    new_mock_process.pid = 99999
    new_mock_process.returncode = None

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = new_mock_process

        success = await manager.restart_process(
            server_name="test",
            aria2c_path="aria2c",
            rpc_port=6800,
            rpc_secret=None,
            session_file=Path("/tmp/test.session"),
        )

        assert success is True


@pytest.mark.asyncio
async def test_is_running():
    """Test checking if a process is running."""
    manager = LocalProcessManager()

    manager._processes["test"] = MagicMock()
    manager._processes["test"].state = ProcessState.RUNNING

    assert manager.is_running("test") is True
    assert manager.is_running("nonexistent") is False


@pytest.mark.asyncio
async def test_get_process_info():
    """Test getting process info."""
    manager = LocalProcessManager()

    manager._processes["test"] = MagicMock()
    manager._processes["test"].pid = 12345
    manager._processes["test"].state = ProcessState.RUNNING

    info = manager.get_process_info("test")
    assert info is not None
    assert info.pid == 12345

    info = manager.get_process_info("nonexistent")
    assert info is None


@pytest.mark.asyncio
async def test_build_command():
    """Test building aria2c command line."""
    manager = LocalProcessManager()

    cmd = manager._build_command(
        aria2c_path="aria2c",
        rpc_port=6800,
        rpc_secret="test-secret",
        session_file=Path("/tmp/session.txt"),
        options={"max-concurrent-downloads": 5, "max-connection-per-server": 4},
    )

    assert cmd[0] == "aria2c"
    assert "--enable-rpc=true" in cmd
    assert "--rpc-listen-port=6800" in cmd
    assert "--rpc-secret=test-secret" in cmd
    assert "--save-session=/tmp/session.txt" in cmd
    assert "--input-file=/tmp/session.txt" in cmd
    assert "--daemon=false" in cmd
    assert "--max-concurrent-downloads=5" in cmd
    assert "--max-connection-per-server=4" in cmd


@pytest.mark.asyncio
async def test_cleanup():
    """Test cleanup of all processes."""
    manager = LocalProcessManager()

    # Setup multiple processes
    for name in ["test1", "test2"]:
        mock_process = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.wait = AsyncMock()

        manager._processes[name] = MagicMock()
        manager._processes[name].state = ProcessState.RUNNING
        manager._processes[name].process = mock_process

    await manager.cleanup()

    # All processes should be stopped
    for name in ["test1", "test2"]:
        assert manager._processes[name].state == ProcessState.STOPPED
