"""Integration tests for WebSocket client's newly added methods.

These tests verify that the 7 methods added to WebSocketRPCClient work correctly
with a real aria2c instance. They also test the Aria2Client factory function.

Requirements:
- Running aria2c instance with RPC enabled
- Set ARIA2_WS_URL and ARIA2_SECRET environment variables if needed
"""

import os

import pytest

from aria2rpc import Aria2Client
from aria2rpc.exceptions import Aria2RPCError
from aria2rpc.http import HTTPRPCClient
from aria2rpc.websocket import WebSocketRPCClient

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Test configuration
ARIA2_WS_URL = os.getenv("ARIA2_WS_URL", "ws://localhost:6800/jsonrpc")
ARIA2_HTTP_URL = os.getenv("ARIA2_HTTP_URL", "http://localhost:6800/jsonrpc")
ARIA2_SECRET = os.getenv("ARIA2_SECRET")
TEST_FILE_URL = "http://httpbin.org/bytes/1024"  # Small test file


@pytest.fixture
def ws_url():
    """Get WebSocket URL from environment."""
    return ARIA2_WS_URL


@pytest.fixture
def http_url():
    """Get HTTP URL from environment."""
    return ARIA2_HTTP_URL


@pytest.fixture
def secret():
    """Get RPC secret from environment."""
    return ARIA2_SECRET


@pytest.fixture
async def ws_client(ws_url, secret):
    """Create a WebSocket client for testing."""
    client = WebSocketRPCClient(
        url=ws_url,
        secret=secret,
        timeout=10.0,
    )
    await client.connect()
    yield client
    await client.close()


# Test newly added WebSocket methods


@pytest.mark.asyncio
async def test_force_remove(ws_client):
    """Test force_remove method."""
    # Add a download
    gid = await ws_client.add_uri([TEST_FILE_URL])
    assert gid is not None

    # Force remove it
    result = await ws_client.force_remove(gid)
    assert result == gid

    # Verify it's removed (should raise error)
    with pytest.raises(Aria2RPCError):
        await ws_client.tell_status(gid)


@pytest.mark.asyncio
async def test_pause_all_unpause_all(ws_client):
    """Test pause_all and unpause_all methods."""
    # Add some downloads
    gid1 = await ws_client.add_uri([TEST_FILE_URL])
    gid2 = await ws_client.add_uri([f"{TEST_FILE_URL}?v=2"])

    # Pause all
    result = await ws_client.pause_all()
    assert result == "OK"

    # Wait a bit for status to update
    import asyncio

    await asyncio.sleep(0.5)

    # Check status (might be paused or complete for small files)
    status1 = await ws_client.tell_status(gid1)
    status2 = await ws_client.tell_status(gid2)
    # For small files, they might complete before pause
    assert status1.status in ["paused", "complete"]
    assert status2.status in ["paused", "complete"]

    # Unpause all
    result = await ws_client.unpause_all()
    assert result == "OK"

    # Clean up
    try:
        await ws_client.remove(gid1)
        await ws_client.remove(gid2)
    except Aria2RPCError:
        pass  # Already removed or completed


@pytest.mark.asyncio
async def test_force_pause_force_pause_all(ws_client):
    """Test force_pause and force_pause_all methods."""
    # Add a download
    gid = await ws_client.add_uri([TEST_FILE_URL])

    # Force pause it
    result = await ws_client.force_pause(gid)
    assert result == gid

    # Clean up
    try:
        await ws_client.remove(gid)
    except Aria2RPCError:
        pass

    # Test force_pause_all
    gid1 = await ws_client.add_uri([TEST_FILE_URL])
    gid2 = await ws_client.add_uri([f"{TEST_FILE_URL}?v=2"])

    result = await ws_client.force_pause_all()
    assert result == "OK"

    # Clean up
    try:
        await ws_client.remove(gid1)
        await ws_client.remove(gid2)
    except Aria2RPCError:
        pass


@pytest.mark.asyncio
async def test_get_files(ws_client):
    """Test get_files method."""
    # Add a download
    gid = await ws_client.add_uri([TEST_FILE_URL])

    # Get files
    files = await ws_client.get_files(gid)
    assert isinstance(files, list)

    # For a single-file download, should have one file
    if files:  # May be empty if download completed too quickly
        assert len(files) >= 1
        file_info = files[0]
        assert "index" in file_info
        assert "path" in file_info

    # Clean up
    try:
        await ws_client.remove(gid)
    except Aria2RPCError:
        pass


@pytest.mark.asyncio
async def test_get_uris(ws_client):
    """Test get_uris method."""
    # Add a download
    gid = await ws_client.add_uri([TEST_FILE_URL])

    # Get URIs
    uris = await ws_client.get_uris(gid)
    assert isinstance(uris, list)

    # Should have at least one URI
    if uris:  # May be empty if download completed too quickly
        assert len(uris) >= 1
        uri_info = uris[0]
        assert "uri" in uri_info
        assert "status" in uri_info
        assert uri_info["uri"] == TEST_FILE_URL

    # Clean up
    try:
        await ws_client.remove(gid)
    except Aria2RPCError:
        pass


# Test Aria2Client factory function


@pytest.mark.asyncio
async def test_aria2client_websocket_url(ws_url, secret):
    """Test Aria2Client returns WebSocketRPCClient for ws:// URLs."""
    client = Aria2Client(ws_url, secret=secret)
    assert isinstance(client, WebSocketRPCClient)

    await client.connect()

    # Test that it works
    version = await client.get_version()
    assert version.version is not None

    # Test new methods are available
    gid = await client.add_uri([TEST_FILE_URL])
    files = await client.get_files(gid)
    assert isinstance(files, list)

    await client.close()


@pytest.mark.asyncio
async def test_aria2client_http_url(http_url, secret):
    """Test Aria2Client returns HTTPRPCClient for http:// URLs."""
    client = Aria2Client(http_url, secret=secret)
    assert isinstance(client, HTTPRPCClient)

    # Test that it works
    async with client:
        version = await client.get_version()
        assert version.version is not None


@pytest.mark.asyncio
async def test_aria2client_with_context_manager(ws_url, secret):
    """Test Aria2Client works with context manager."""
    async with Aria2Client(ws_url, secret=secret) as client:
        assert isinstance(client, WebSocketRPCClient)

        # Test all new methods are accessible
        version = await client.get_version()
        assert version.version is not None

        # Add and immediately remove
        gid = await client.add_uri([TEST_FILE_URL])
        await client.force_remove(gid)


@pytest.mark.asyncio
async def test_websocket_has_all_18_methods(ws_client):
    """Verify WebSocketRPCClient has all 18 RPC methods."""
    # Check that all methods exist
    assert hasattr(ws_client, "add_uri")
    assert hasattr(ws_client, "remove")
    assert hasattr(ws_client, "pause")
    assert hasattr(ws_client, "unpause")
    assert hasattr(ws_client, "force_remove")
    assert hasattr(ws_client, "pause_all")
    assert hasattr(ws_client, "unpause_all")
    assert hasattr(ws_client, "force_pause")
    assert hasattr(ws_client, "force_pause_all")
    assert hasattr(ws_client, "tell_status")
    assert hasattr(ws_client, "tell_active")
    assert hasattr(ws_client, "tell_waiting")
    assert hasattr(ws_client, "tell_stopped")
    assert hasattr(ws_client, "get_global_stat")
    assert hasattr(ws_client, "get_version")
    assert hasattr(ws_client, "get_files")
    assert hasattr(ws_client, "get_uris")

    # Event methods (WebSocket only)
    assert hasattr(ws_client, "on")
    assert hasattr(ws_client, "off")


@pytest.mark.asyncio
async def test_method_parity_websocket_http(ws_url, http_url, secret):
    """Test that WebSocket and HTTP clients have the same RPC methods."""
    ws_client = Aria2Client(ws_url, secret=secret)
    http_client = Aria2Client(http_url, secret=secret)

    # RPC methods that should exist in both
    rpc_methods = [
        "add_uri",
        "remove",
        "pause",
        "unpause",
        "force_remove",
        "pause_all",
        "unpause_all",
        "force_pause",
        "force_pause_all",
        "tell_status",
        "tell_active",
        "tell_waiting",
        "tell_stopped",
        "get_global_stat",
        "get_version",
        "get_files",
        "get_uris",
    ]

    for method in rpc_methods:
        assert hasattr(ws_client, method), f"WebSocket missing {method}"
        assert hasattr(http_client, method), f"HTTP missing {method}"

    # Event methods (WebSocket only)
    assert hasattr(ws_client, "on")
    assert hasattr(ws_client, "off")
    assert not hasattr(http_client, "on")
    assert not hasattr(http_client, "off")
