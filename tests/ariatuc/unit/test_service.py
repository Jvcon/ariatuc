"""Unit tests for Aria2Service layer.

This test suite covers:
- Download operations (add, pause, resume, remove, add_torrent)
- Batch operations (pause_all, resume_all, purge_completed)
- State synchronization (refresh mechanisms and auto-refresh)
- Event handling (event listeners and state updates)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aria2rpc import Aria2Error, Aria2Event
from ariatuc.core import (
    Aria2Service,
    DownloadOperationError,
)


@pytest.fixture
def mock_rpc_client():
    """Create a mock RPC client."""
    client = AsyncMock()
    client.add_uri = AsyncMock(return_value="test-gid-1")
    client.add_torrent = AsyncMock(return_value="test-gid-torrent")
    client.pause = AsyncMock(return_value="test-gid-1")
    client.unpause = AsyncMock(return_value="test-gid-1")
    client.remove = AsyncMock(return_value="test-gid-1")
    client.force_remove = AsyncMock(return_value="test-gid-1")
    client.remove_download_result = AsyncMock(return_value="test-gid-1")
    client.pause_all = AsyncMock(return_value="OK")
    client.unpause_all = AsyncMock(return_value="OK")
    client.purge_download_result = AsyncMock(return_value="OK")
    client.tell_status = AsyncMock()
    client.tell_active = AsyncMock(return_value=[])
    client.tell_waiting = AsyncMock(return_value=[])
    client.tell_stopped = AsyncMock(return_value=[])
    client.get_global_stat = AsyncMock()
    client.get_version = AsyncMock()
    client.get_option = AsyncMock(return_value={})
    return client


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager."""
    with patch("ariatuc.core.service.ConfigManager") as mock_cls:
        mock_mgr = MagicMock()
        mock_mgr.load.return_value = MagicMock(
            servers=[], current_server=None, refresh_interval=1000
        )
        mock_mgr.get.return_value = MagicMock(
            servers=[], current_server=None, refresh_interval=1000
        )
        mock_cls.return_value = mock_mgr
        yield mock_mgr


@pytest.fixture
def mock_rpc_manager():
    """Create a mock RPCManager."""
    with patch("ariatuc.core.service.RPCManager") as mock_cls:
        mock_mgr = MagicMock()
        mock_mgr.add_server = MagicMock()
        mock_mgr.remove_server = MagicMock()
        mock_mgr.switch_server = MagicMock(return_value=True)
        mock_mgr.connect = AsyncMock(return_value=True)
        mock_mgr.disconnect = AsyncMock()
        mock_mgr.health_check = AsyncMock(return_value=True)
        mock_mgr.get_client = MagicMock()
        mock_mgr.get_websocket_client = MagicMock(return_value=None)
        mock_mgr.get_server_state = MagicMock()
        mock_mgr.list_servers = MagicMock(return_value=[])
        mock_mgr.current_server = None
        mock_mgr.is_websocket = MagicMock(return_value=False)
        mock_cls.return_value = mock_mgr
        yield mock_mgr


@pytest.fixture
def mock_download_manager():
    """Create a mock DownloadManager."""
    with patch("ariatuc.core.service.DownloadManager") as mock_cls:
        mock_mgr = MagicMock()
        mock_mgr.downloads = {}
        mock_mgr.update_download = MagicMock()
        mock_mgr.remove_download = MagicMock()
        mock_mgr.get_download = MagicMock(return_value=None)
        mock_mgr.get_all_downloads = MagicMock(return_value=[])
        mock_mgr.get_downloads_by_status = MagicMock(return_value=[])
        mock_cls.return_value = mock_mgr
        yield mock_mgr


@pytest.fixture
def mock_event_manager():
    """Create a mock EventManager."""
    with patch("ariatuc.core.service.EventManager") as mock_cls:
        mock_mgr = MagicMock()
        mock_mgr.set_client = MagicMock()
        mock_mgr.disable = MagicMock()
        mock_mgr.on = MagicMock()
        mock_mgr.set_notification_handler = MagicMock()
        mock_mgr.is_active = MagicMock(return_value=False)
        mock_cls.return_value = mock_mgr
        yield mock_mgr


@pytest.fixture
def service(mock_config_manager, mock_rpc_manager, mock_download_manager, mock_event_manager):
    """Create an Aria2Service instance with mocked managers.

    Note: The fixture parameters are required for test setup to ensure
    the managers are mocked when Aria2Service is initialized.
    """
    # These assertions verify the mocks are properly set up and silence unused warnings
    assert mock_config_manager is not None
    assert mock_rpc_manager is not None
    assert mock_download_manager is not None
    assert mock_event_manager is not None
    return Aria2Service()


# ==================== Test: Download Operations ====================


@pytest.mark.asyncio
async def test_add_download_success(service, mock_rpc_manager, mock_rpc_client):
    """Test successfully adding a download."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_status = MagicMock()
    mock_status.gid = "test-gid-1"
    mock_status.raw = {"gid": "test-gid-1", "status": "active"}
    mock_rpc_client.tell_status.return_value = mock_status

    # Execute
    gid = await service.add_download(["http://example.com/file.zip"])

    # Verify
    assert gid == "test-gid-1"
    mock_rpc_client.add_uri.assert_called_once_with(["http://example.com/file.zip"], options={})
    mock_rpc_client.tell_status.assert_called_once_with("test-gid-1")


@pytest.mark.asyncio
async def test_add_download_with_options(service, mock_rpc_manager, mock_rpc_client):
    """Test adding a download with custom options."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_status = MagicMock()
    mock_status.gid = "test-gid-1"
    mock_status.raw = {"gid": "test-gid-1", "status": "active"}
    mock_rpc_client.tell_status.return_value = mock_status

    options = {"dir": "/downloads", "out": "myfile.zip"}

    # Execute
    gid = await service.add_download(["http://example.com/file.zip"], options=options)

    # Verify
    assert gid == "test-gid-1"
    mock_rpc_client.add_uri.assert_called_once_with(
        ["http://example.com/file.zip"], options={"dir": "/downloads", "out": "myfile.zip"}
    )


@pytest.mark.asyncio
async def test_add_download_not_connected(service, mock_rpc_manager):
    """Test adding download when not connected to server."""
    # Setup
    mock_rpc_manager.get_client.return_value = None

    # Execute & Verify
    with pytest.raises(DownloadOperationError, match="Not connected to any server"):
        await service.add_download(["http://example.com/file.zip"])


@pytest.mark.asyncio
async def test_add_download_rpc_error(service, mock_rpc_manager, mock_rpc_client):
    """Test adding download with RPC error."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_rpc_client.add_uri.side_effect = Aria2Error("RPC failed")

    # Execute & Verify
    with pytest.raises(DownloadOperationError, match="Failed to add download"):
        await service.add_download(["http://example.com/file.zip"])


@pytest.mark.asyncio
async def test_add_torrent_success(service, mock_rpc_manager, mock_rpc_client):
    """Test successfully adding a torrent download."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_status = MagicMock()
    mock_status.gid = "test-gid-torrent"
    mock_status.raw = {"gid": "test-gid-torrent", "status": "active"}
    mock_rpc_client.tell_status.return_value = mock_status

    torrent_data = b"fake-torrent-data"

    # Execute
    gid = await service.add_torrent(torrent_data)

    # Verify
    assert gid == "test-gid-torrent"
    mock_rpc_client.add_torrent.assert_called_once_with(torrent_data, uris=[], options={})


@pytest.mark.asyncio
async def test_pause_download_success(service, mock_rpc_manager, mock_rpc_client):
    """Test successfully pausing a download."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_status = MagicMock()
    mock_status.gid = "test-gid-1"
    mock_status.raw = {"gid": "test-gid-1", "status": "paused"}
    mock_rpc_client.tell_status.return_value = mock_status

    # Execute
    result = await service.pause_download("test-gid-1")

    # Verify
    assert result is True
    mock_rpc_client.pause.assert_called_once_with("test-gid-1")


@pytest.mark.asyncio
async def test_resume_download_success(service, mock_rpc_manager, mock_rpc_client):
    """Test successfully resuming a download."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_status = MagicMock()
    mock_status.gid = "test-gid-1"
    mock_status.raw = {"gid": "test-gid-1", "status": "active"}
    mock_rpc_client.tell_status.return_value = mock_status

    # Execute
    result = await service.resume_download("test-gid-1")

    # Verify
    assert result is True
    mock_rpc_client.unpause.assert_called_once_with("test-gid-1")


@pytest.mark.asyncio
async def test_remove_download_active(service, mock_rpc_manager, mock_rpc_client):
    """Test removing an active download."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    service._active_gids.add("test-gid-1")

    # Execute
    result = await service.remove_download("test-gid-1")

    # Verify
    assert result is True
    mock_rpc_client.remove.assert_called_once_with("test-gid-1")
    assert "test-gid-1" not in service._active_gids


@pytest.mark.asyncio
async def test_remove_download_stopped(service, mock_rpc_manager, mock_rpc_client):
    """Test removing a stopped download."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    service._stopped_gids.add("test-gid-1")

    # Execute
    result = await service.remove_download("test-gid-1")

    # Verify
    assert result is True
    mock_rpc_client.remove_download_result.assert_called_once_with("test-gid-1")
    assert "test-gid-1" not in service._stopped_gids


@pytest.mark.asyncio
async def test_remove_download_force(service, mock_rpc_manager, mock_rpc_client):
    """Test force removing a download."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    service._active_gids.add("test-gid-1")

    # Execute
    result = await service.remove_download("test-gid-1", force=True)

    # Verify
    assert result is True
    mock_rpc_client.force_remove.assert_called_once_with("test-gid-1")


# ==================== Test: Batch Operations ====================


@pytest.mark.asyncio
async def test_pause_all_success(service, mock_rpc_manager, mock_rpc_client):
    """Test successfully pausing all downloads."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_rpc_client.tell_active.return_value = []
    mock_rpc_client.tell_waiting.return_value = []
    mock_rpc_client.tell_stopped.return_value = []

    # Execute
    result = await service.pause_all()

    # Verify
    assert result == ["OK"]
    mock_rpc_client.pause_all.assert_called_once()


@pytest.mark.asyncio
async def test_pause_all_not_connected(service, mock_rpc_manager):
    """Test pause_all when not connected."""
    # Setup
    mock_rpc_manager.get_client.return_value = None

    # Execute & Verify
    with pytest.raises(DownloadOperationError, match="Not connected to any server"):
        await service.pause_all()


@pytest.mark.asyncio
async def test_resume_all_success(service, mock_rpc_manager, mock_rpc_client):
    """Test successfully resuming all downloads."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_rpc_client.tell_active.return_value = []
    mock_rpc_client.tell_waiting.return_value = []
    mock_rpc_client.tell_stopped.return_value = []

    # Execute
    result = await service.resume_all()

    # Verify
    assert result == ["OK"]
    mock_rpc_client.unpause_all.assert_called_once()


@pytest.mark.asyncio
async def test_purge_completed_success(service, mock_rpc_manager, mock_rpc_client):
    """Test successfully purging completed downloads."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_rpc_client.tell_active.return_value = []
    mock_rpc_client.tell_waiting.return_value = []
    mock_rpc_client.tell_stopped.return_value = []

    # Execute
    result = await service.purge_completed()

    # Verify
    assert result is True
    mock_rpc_client.purge_download_result.assert_called_once()


@pytest.mark.asyncio
async def test_purge_completed_rpc_error(service, mock_rpc_manager, mock_rpc_client):
    """Test purge_completed with RPC error."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_rpc_client.purge_download_result.side_effect = Aria2Error("Purge failed")

    # Execute & Verify
    with pytest.raises(DownloadOperationError, match="Failed to purge"):
        await service.purge_completed()


# ==================== Test: State Synchronization ====================


@pytest.mark.asyncio
async def test_refresh_downloads(service, mock_rpc_manager, mock_rpc_client, mock_download_manager):
    """Test refreshing all downloads from aria2."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client

    mock_active = MagicMock()
    mock_active.gid = "gid-active"
    mock_active.raw = {"gid": "gid-active", "status": "active"}

    mock_waiting = MagicMock()
    mock_waiting.gid = "gid-waiting"
    mock_waiting.raw = {"gid": "gid-waiting", "status": "waiting"}

    mock_stopped = MagicMock()
    mock_stopped.gid = "gid-stopped"
    mock_stopped.raw = {"gid": "gid-stopped", "status": "complete"}

    mock_rpc_client.tell_active.return_value = [mock_active]
    mock_rpc_client.tell_waiting.return_value = [mock_waiting]
    mock_rpc_client.tell_stopped.return_value = [mock_stopped]

    # Execute
    await service.refresh_downloads()

    # Verify
    assert "gid-active" in service._active_gids
    assert "gid-waiting" in service._waiting_gids
    assert "gid-stopped" in service._stopped_gids
    assert mock_download_manager.update_download.call_count == 3


@pytest.mark.asyncio
async def test_refresh_downloads_skip_removed(
    service, mock_rpc_manager, mock_rpc_client, mock_download_manager
):
    """Test that refresh_downloads skips downloads with 'removed' status."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client

    mock_removed = MagicMock()
    mock_removed.gid = "gid-removed"
    mock_removed.raw = {"gid": "gid-removed", "status": "removed"}

    mock_stopped = MagicMock()
    mock_stopped.gid = "gid-stopped"
    mock_stopped.raw = {"gid": "gid-stopped", "status": "complete"}

    mock_rpc_client.tell_active.return_value = []
    mock_rpc_client.tell_waiting.return_value = []
    mock_rpc_client.tell_stopped.return_value = [mock_removed, mock_stopped]

    # Execute
    await service.refresh_downloads()

    # Verify - removed download should not be added to stopped_gids
    assert "gid-removed" not in service._stopped_gids
    assert "gid-stopped" in service._stopped_gids
    assert mock_download_manager.update_download.call_count == 1


@pytest.mark.asyncio
async def test_refresh_downloads_cleanup_removed(
    service, mock_rpc_manager, mock_rpc_client, mock_download_manager
):
    """Test that refresh_downloads cleans up downloads no longer in aria2."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_download_manager.downloads = {"gid-old": MagicMock(), "gid-current": MagicMock()}

    mock_current = MagicMock()
    mock_current.gid = "gid-current"
    mock_current.raw = {"gid": "gid-current", "status": "active"}

    mock_rpc_client.tell_active.return_value = [mock_current]
    mock_rpc_client.tell_waiting.return_value = []
    mock_rpc_client.tell_stopped.return_value = []

    # Execute
    await service.refresh_downloads()

    # Verify - old download should be removed
    mock_download_manager.remove_download.assert_called_with("gid-old")


@pytest.mark.asyncio
async def test_refresh_download(service, mock_rpc_manager, mock_rpc_client, mock_download_manager):
    """Test refreshing a single download."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client

    mock_status = MagicMock()
    mock_status.gid = "test-gid"
    mock_status.raw = {"gid": "test-gid", "status": "active"}
    mock_rpc_client.tell_status.return_value = mock_status

    # Execute
    await service.refresh_download("test-gid")

    # Verify
    mock_rpc_client.tell_status.assert_called_once_with("test-gid")
    mock_download_manager.update_download.assert_called_once_with("test-gid", mock_status.raw)


@pytest.mark.asyncio
async def test_start_auto_refresh(service, mock_rpc_manager, mock_rpc_client):
    """Test starting auto-refresh."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_rpc_client.tell_active.return_value = []
    mock_rpc_client.tell_waiting.return_value = []
    mock_rpc_client.tell_stopped.return_value = []

    # Execute
    await service.start_auto_refresh(interval=0.1)

    # Verify task is created
    assert service._auto_refresh_task is not None
    assert not service._auto_refresh_task.done()

    # Wait a bit to let it run
    await asyncio.sleep(0.15)

    # Cleanup
    await service.stop_auto_refresh()


@pytest.mark.asyncio
async def test_stop_auto_refresh(service, mock_rpc_manager, mock_rpc_client):
    """Test stopping auto-refresh."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_rpc_client.tell_active.return_value = []
    mock_rpc_client.tell_waiting.return_value = []
    mock_rpc_client.tell_stopped.return_value = []

    # Start auto-refresh
    await service.start_auto_refresh(interval=0.1)
    assert service._auto_refresh_task is not None

    # Execute
    await service.stop_auto_refresh()

    # Verify
    assert service._auto_refresh_task is None


@pytest.mark.asyncio
async def test_auto_refresh_loop_calls_refresh(service, mock_rpc_manager, mock_rpc_client):
    """Test that auto-refresh loop calls refresh_downloads periodically."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_rpc_client.tell_active.return_value = []
    mock_rpc_client.tell_waiting.return_value = []
    mock_rpc_client.tell_stopped.return_value = []

    # Execute
    await service.start_auto_refresh(interval=0.05)

    # Wait for multiple refresh cycles
    await asyncio.sleep(0.12)

    # Verify refresh was called multiple times
    assert mock_rpc_client.tell_active.call_count >= 2

    # Cleanup
    await service.stop_auto_refresh()


# ==================== Test: Event Handling ====================


@pytest.mark.asyncio
async def test_event_handlers_registered(service, mock_event_manager):
    """Test that event handlers are properly registered."""
    # Execute
    service._connect_event_handlers()

    # Verify all events are registered
    expected_events = [
        Aria2Event.DOWNLOAD_COMPLETE,
        Aria2Event.DOWNLOAD_ERROR,
        Aria2Event.DOWNLOAD_START,
        Aria2Event.DOWNLOAD_PAUSE,
        Aria2Event.DOWNLOAD_STOP,
    ]

    # Verify on() was called for each event (5 times total)
    assert mock_event_manager.on.call_count == len(expected_events)


@pytest.mark.asyncio
async def test_ui_refresh_callback_called(service, mock_rpc_manager, mock_rpc_client):
    """Test that UI refresh callback is called after state updates."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_status = MagicMock()
    mock_status.gid = "test-gid"
    mock_status.raw = {"gid": "test-gid", "status": "active"}
    mock_rpc_client.tell_status.return_value = mock_status

    callback = MagicMock()
    service.set_ui_refresh_callback(callback)

    # Execute
    await service.refresh_download("test-gid")

    # Verify callback was called
    callback.assert_called_once()


@pytest.mark.asyncio
async def test_notification_callback_set(service):
    """Test setting notification callback."""
    # Setup
    callback = MagicMock()

    # Execute
    service.set_notification_callback(callback)

    # Verify
    assert service._notification_callback == callback


@pytest.mark.asyncio
async def test_ui_refresh_callback_with_refresh_downloads(
    service, mock_rpc_manager, mock_rpc_client
):
    """Test that UI refresh callback is called during refresh_downloads."""
    # Setup
    mock_rpc_manager.get_client.return_value = mock_rpc_client
    mock_rpc_client.tell_active.return_value = []
    mock_rpc_client.tell_waiting.return_value = []
    mock_rpc_client.tell_stopped.return_value = []

    callback = MagicMock()
    service.set_ui_refresh_callback(callback)

    # Execute
    await service.refresh_downloads()

    # Verify callback was called
    callback.assert_called_once()
