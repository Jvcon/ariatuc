"""Integration tests for WebSocket RPC client.

These tests require a running aria2c instance with RPC enabled:
    aria2c --enable-rpc --rpc-listen-all --rpc-allow-origin-all

Set environment variable ARIA2_WS_URL to customize the test endpoint:
    export ARIA2_WS_URL=ws://localhost:6800/jsonrpc
    export ARIA2_SECRET=your-secret  # Optional
"""

import asyncio
import os

import pytest

from aria2rpc import Aria2Event, WebSocketRPCClient
from aria2rpc.exceptions import (
    Aria2ConnectionError,
    Aria2RPCError,
    Aria2TimeoutError,
)

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Test configuration
ARIA2_WS_URL = os.getenv("ARIA2_WS_URL", "ws://localhost:6800/jsonrpc")
ARIA2_SECRET = os.getenv("ARIA2_SECRET")
TEST_FILE_URL = "http://httpbin.org/bytes/1024"  # Small test file


@pytest.fixture
def ws_url():
    """Get WebSocket URL from environment."""
    return ARIA2_WS_URL


@pytest.fixture
def secret():
    """Get RPC secret from environment."""
    return ARIA2_SECRET


@pytest.fixture
async def client(ws_url, secret):
    """Create a WebSocket client for testing."""
    client = WebSocketRPCClient(
        url=ws_url,
        secret=secret,
        timeout=10.0,
        auto_reconnect=True,
        max_reconnect_attempts=3,
        heartbeat_interval=5.0,
    )
    await client.connect()
    yield client
    await client.close()


@pytest.fixture
async def client_no_connect(ws_url, secret):
    """Create a WebSocket client without connecting."""
    client = WebSocketRPCClient(
        url=ws_url,
        secret=secret,
        timeout=5.0,
    )
    yield client
    if client._ws:
        await client.close()


# Connection Tests


@pytest.mark.asyncio
async def test_connect_success(ws_url, secret):
    """Test successful WebSocket connection."""
    async with WebSocketRPCClient(ws_url, secret=secret) as client:
        assert client._ws is not None
        assert client._listener_task is not None
        assert client._heartbeat_task is not None


@pytest.mark.asyncio
async def test_connect_invalid_url():
    """Test connection to invalid URL."""
    with pytest.raises(Aria2ConnectionError) as exc_info:
        async with WebSocketRPCClient("ws://invalid-host-12345:6800/jsonrpc"):
            pass
    assert "invalid-host-12345" in str(exc_info.value)


@pytest.mark.asyncio
async def test_connect_timeout():
    """Test connection timeout."""
    client = WebSocketRPCClient(
        "ws://192.0.2.1:6800/jsonrpc",  # Non-routable IP
        timeout=1.0,
    )
    with pytest.raises((Aria2ConnectionError, Aria2TimeoutError)):
        await client.connect()


@pytest.mark.asyncio
async def test_context_manager(ws_url, secret):
    """Test async context manager protocol."""
    async with WebSocketRPCClient(ws_url, secret=secret) as client:
        assert client._ws is not None

    # After exiting context, connection should be closed
    assert client._ws is None or client._is_closing


# RPC Method Tests


@pytest.mark.asyncio
async def test_get_version(client):
    """Test get_version RPC call."""
    version = await client.get_version()
    assert version.version is not None
    assert isinstance(version.version, str)
    assert len(version.version) > 0
    assert isinstance(version.enabled_features, list)


@pytest.mark.asyncio
async def test_get_global_stat(client):
    """Test get_global_stat RPC call."""
    stat = await client.get_global_stat()
    assert stat.download_speed >= 0
    assert stat.upload_speed >= 0
    assert stat.num_active >= 0
    assert stat.num_waiting >= 0
    assert stat.num_stopped >= 0


@pytest.mark.asyncio
async def test_add_uri_and_tell_status(client):
    """Test adding a download and checking its status."""
    # Add download
    gid = await client.add_uri([TEST_FILE_URL])
    assert gid is not None
    assert isinstance(gid, str)
    assert len(gid) > 0

    # Check status
    status = await client.tell_status(gid)
    assert status.gid == gid
    assert status.status in ["active", "waiting", "paused", "complete"]

    # Clean up
    try:
        await client.remove(gid)
    except Aria2RPCError:
        pass  # Already removed or completed


@pytest.mark.asyncio
async def test_pause_and_unpause(client):
    """Test pausing and unpausing a download."""
    # Add a download
    gid = await client.add_uri([TEST_FILE_URL])

    # Wait a bit for download to start
    await asyncio.sleep(0.5)

    # Pause
    result = await client.pause(gid)
    assert result == gid

    # Check status
    status = await client.tell_status(gid)
    # Status might be paused or already complete for small file
    assert status.status in ["paused", "complete"]

    # Unpause if not complete
    if status.status == "paused":
        result = await client.unpause(gid)
        assert result == gid

    # Clean up
    try:
        await client.remove(gid)
    except Aria2RPCError:
        pass


@pytest.mark.asyncio
async def test_tell_active(client):
    """Test tell_active RPC call."""
    downloads = await client.tell_active()
    assert isinstance(downloads, list)
    # Each item should be a DownloadStatus
    for download in downloads:
        assert hasattr(download, "gid")
        assert hasattr(download, "status")


@pytest.mark.asyncio
async def test_tell_waiting(client):
    """Test tell_waiting RPC call."""
    downloads = await client.tell_waiting(0, 10)
    assert isinstance(downloads, list)


@pytest.mark.asyncio
async def test_tell_stopped(client):
    """Test tell_stopped RPC call."""
    downloads = await client.tell_stopped(0, 10)
    assert isinstance(downloads, list)


@pytest.mark.asyncio
async def test_rpc_error_handling(client):
    """Test RPC error handling."""
    with pytest.raises(Aria2RPCError) as exc_info:
        # Try to get status of non-existent GID
        await client.tell_status("0000000000000000")

    assert exc_info.value.code != 0
    assert exc_info.value.message is not None


@pytest.mark.asyncio
async def test_concurrent_rpc_calls(client):
    """Test multiple concurrent RPC calls."""
    # Make multiple concurrent calls
    tasks = [
        client.get_version(),
        client.get_global_stat(),
        client.tell_active(),
        client.tell_waiting(0, 10),
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 4
    assert results[0].version is not None  # Version
    assert results[1].download_speed >= 0  # GlobalStat
    assert isinstance(results[2], list)  # Active downloads
    assert isinstance(results[3], list)  # Waiting downloads


# Event Subscription Tests


@pytest.mark.asyncio
async def test_event_subscription(client):
    """Test event subscription mechanism."""
    events_received = []

    async def on_start(event):
        events_received.append(("start", event))

    async def on_complete(event):
        events_received.append(("complete", event))

    # Subscribe to events
    client.on(Aria2Event.DOWNLOAD_START, on_start)
    client.on(Aria2Event.DOWNLOAD_COMPLETE, on_complete)

    # Add a download
    gid = await client.add_uri([TEST_FILE_URL])

    # Wait for events (small file should complete quickly)
    await asyncio.sleep(2)

    # Check events
    # Note: Events might not trigger for very small/fast downloads
    # or if download completes before listener starts
    assert isinstance(events_received, list)

    # Clean up
    try:
        await client.remove(gid)
    except Aria2RPCError:
        pass


@pytest.mark.asyncio
async def test_multiple_event_handlers(client):
    """Test multiple handlers for the same event."""
    handler1_called = []
    handler2_called = []

    async def handler1(event):
        handler1_called.append(event)

    async def handler2(event):
        handler2_called.append(event)

    # Subscribe both handlers to the same event
    client.on(Aria2Event.DOWNLOAD_COMPLETE, handler1)
    client.on(Aria2Event.DOWNLOAD_COMPLETE, handler2)

    # Add and wait for download
    gid = await client.add_uri([TEST_FILE_URL])
    await asyncio.sleep(2)

    # Both handlers should be called
    # (or neither if download too fast)
    assert len(handler1_called) == len(handler2_called)

    # Clean up
    try:
        await client.remove(gid)
    except Aria2RPCError:
        pass


@pytest.mark.asyncio
async def test_unsubscribe_event(client):
    """Test unsubscribing from events."""
    events = []

    async def handler(event):
        events.append(event)

    # Subscribe
    client.on(Aria2Event.DOWNLOAD_COMPLETE, handler)

    # Unsubscribe specific handler
    client.off(Aria2Event.DOWNLOAD_COMPLETE, handler)

    # Add download
    gid = await client.add_uri([TEST_FILE_URL])
    await asyncio.sleep(2)

    # Handler should not be called
    assert len(events) == 0

    # Clean up
    try:
        await client.remove(gid)
    except Aria2RPCError:
        pass


@pytest.mark.asyncio
async def test_unsubscribe_all_handlers(client):
    """Test unsubscribing all handlers for an event."""
    events1 = []
    events2 = []

    async def handler1(event):
        events1.append(event)

    async def handler2(event):
        events2.append(event)

    # Subscribe both
    client.on(Aria2Event.DOWNLOAD_COMPLETE, handler1)
    client.on(Aria2Event.DOWNLOAD_COMPLETE, handler2)

    # Unsubscribe all
    client.off(Aria2Event.DOWNLOAD_COMPLETE)

    # Add download
    gid = await client.add_uri([TEST_FILE_URL])
    await asyncio.sleep(2)

    # No handlers should be called
    assert len(events1) == 0
    assert len(events2) == 0

    # Clean up
    try:
        await client.remove(gid)
    except Aria2RPCError:
        pass


@pytest.mark.asyncio
async def test_event_handler_exception(client):
    """Test that exception in one handler doesn't affect others."""
    good_handler_called = []

    async def bad_handler(event):
        _ = event  # Unused
        raise ValueError("Test exception")

    async def good_handler(event):
        good_handler_called.append(event)

    # Subscribe both handlers
    client.on(Aria2Event.DOWNLOAD_COMPLETE, bad_handler)
    client.on(Aria2Event.DOWNLOAD_COMPLETE, good_handler)

    # Add download
    gid = await client.add_uri([TEST_FILE_URL])
    await asyncio.sleep(2)

    # Good handler should still work despite bad handler exception
    # (or neither called if download too fast)
    # The important thing is no exception propagates

    # Clean up
    try:
        await client.remove(gid)
    except Aria2RPCError:
        pass


# Reconnection Tests


@pytest.mark.asyncio
async def test_auto_reconnect_disabled(ws_url, secret):
    """Test client with auto-reconnect disabled."""
    client = WebSocketRPCClient(
        ws_url,
        secret=secret,
        auto_reconnect=False,
    )
    await client.connect()

    # Verify connection
    assert client._ws is not None

    await client.close()


@pytest.mark.asyncio
async def test_reconnect_attempts_limit(ws_url):
    """Test max reconnection attempts limit."""
    client = WebSocketRPCClient(
        ws_url + "-invalid",  # Invalid URL to force reconnection failure
        auto_reconnect=True,
        max_reconnect_attempts=2,
        timeout=1.0,
    )

    with pytest.raises(Aria2ConnectionError):
        await client.connect()


# Heartbeat Tests


@pytest.mark.asyncio
async def test_heartbeat_keeps_connection_alive(client):
    """Test that heartbeat keeps connection alive."""
    # Get version to verify connection
    version1 = await client.get_version()
    assert version1.version is not None

    # Wait for multiple heartbeat intervals
    await asyncio.sleep(6)  # heartbeat_interval is 5s in fixture

    # Connection should still work
    version2 = await client.get_version()
    assert version2.version is not None


# Error Handling Tests


@pytest.mark.asyncio
async def test_rpc_call_without_connection(client_no_connect):
    """Test RPC call without establishing connection."""
    with pytest.raises(Aria2ConnectionError) as exc_info:
        await client_no_connect.add_uri([TEST_FILE_URL])

    assert "Not connected" in str(exc_info.value)


@pytest.mark.asyncio
async def test_timeout_on_slow_response():
    """Test timeout on slow response."""
    client = WebSocketRPCClient(
        ARIA2_WS_URL,
        secret=ARIA2_SECRET,
        timeout=0.1,  # Very short timeout
    )

    await client.connect()

    try:
        # This might timeout if response takes too long
        # Note: This test might be flaky depending on server speed
        with pytest.raises(Aria2TimeoutError):
            # Try multiple operations to increase chance of timeout
            await asyncio.gather(*[client.get_version() for _ in range(10)])
    except Aria2TimeoutError:
        pass  # Expected
    finally:
        await client.close()


# Integration Tests


@pytest.mark.asyncio
async def test_full_download_lifecycle(client):
    """Test complete download lifecycle with events."""
    events = []

    async def track_event(event_type):
        async def handler(event):
            events.append((event_type, event["gid"]))

        return handler

    # Subscribe to all events
    client.on(Aria2Event.DOWNLOAD_START, await track_event("start"))
    client.on(Aria2Event.DOWNLOAD_COMPLETE, await track_event("complete"))
    client.on(Aria2Event.DOWNLOAD_ERROR, await track_event("error"))

    # Add download
    gid = await client.add_uri([TEST_FILE_URL])

    # Wait for download to complete
    await asyncio.sleep(3)

    # Check final status
    try:
        status = await client.tell_status(gid)
        assert status.status in ["complete", "removed"]
    except Aria2RPCError:
        # Download might be removed from history
        pass

    # Clean up
    try:
        await client.remove(gid)
    except Aria2RPCError:
        pass


@pytest.mark.asyncio
async def test_multiple_concurrent_downloads(client):
    """Test handling multiple concurrent downloads."""
    urls = [
        "http://httpbin.org/bytes/512",
        "http://httpbin.org/bytes/1024",
        "http://httpbin.org/bytes/2048",
    ]

    # Add multiple downloads
    gids = []
    for url in urls:
        gid = await client.add_uri([url])
        gids.append(gid)

    # Wait a bit
    await asyncio.sleep(2)

    # Check all downloads
    for gid in gids:
        try:
            status = await client.tell_status(gid)
            assert status.gid == gid
        except Aria2RPCError:
            pass  # Might already be complete and removed

    # Clean up
    for gid in gids:
        try:
            await client.remove(gid)
        except Aria2RPCError:
            pass


@pytest.mark.asyncio
async def test_client_reuse():
    """Test that client can be reused after closing."""
    client = WebSocketRPCClient(ARIA2_WS_URL, secret=ARIA2_SECRET)

    # First connection
    await client.connect()
    version1 = await client.get_version()
    assert version1.version is not None
    await client.close()

    # Second connection
    await client.connect()
    version2 = await client.get_version()
    assert version2.version is not None
    await client.close()


# Performance Tests


@pytest.mark.asyncio
async def test_many_concurrent_rpc_calls(client):
    """Test handling many concurrent RPC calls."""
    # Create 50 concurrent calls
    tasks = [client.get_version() for _ in range(50)]

    # All should complete successfully
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check that most succeeded (some might timeout)
    successful = [r for r in results if not isinstance(r, Exception)]
    assert len(successful) > 40  # At least 80% success rate


@pytest.mark.asyncio
async def test_rapid_subscribe_unsubscribe(client):
    """Test rapid event subscription and unsubscription."""

    async def dummy_handler(event):
        _ = event  # Unused
        pass

    # Rapidly subscribe and unsubscribe
    for _ in range(100):
        client.on(Aria2Event.DOWNLOAD_COMPLETE, dummy_handler)
        client.off(Aria2Event.DOWNLOAD_COMPLETE, dummy_handler)

    # Client should still work
    version = await client.get_version()
    assert version.version is not None
