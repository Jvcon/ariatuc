"""Tests for aria2 RPC client."""

import base64
from unittest.mock import AsyncMock, patch

import pytest

from aria2rpc import Aria2Client
from aria2rpc.http import HTTPRPCClient


@pytest.mark.asyncio
async def test_client_initialization():
    """Test Aria2Client initialization."""
    client = Aria2Client("http://localhost:6800/jsonrpc", secret="test-secret")
    assert client.url == "http://localhost:6800/jsonrpc"
    assert client.secret == "test-secret"
    await client.close()


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test Aria2Client as context manager."""
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        assert client.url == "http://localhost:6800/jsonrpc"


@pytest.mark.asyncio
async def test_add_torrent():
    """Test adding a BitTorrent download."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    # Mock torrent file content
    torrent_data = b"mock torrent file content"
    expected_b64 = base64.b64encode(torrent_data).decode("ascii")
    expected_gid = "abc123"

    # Mock the _call method
    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = expected_gid

        gid = await client.add_torrent(torrent_data)

        # Verify the call was made with correct parameters
        mock_call.assert_called_once()
        call_args = mock_call.call_args
        assert call_args[0][0] == "aria2.addTorrent"
        assert call_args[0][1][0] == expected_b64
        assert gid == expected_gid

    await client.close()


@pytest.mark.asyncio
async def test_add_torrent_with_options():
    """Test adding a BitTorrent download with options."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    torrent_data = b"mock torrent"
    uris = ["http://example.com/webseed"]
    options = {"dir": "/downloads"}
    position = 0

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "gid123"

        await client.add_torrent(torrent_data, uris=uris, options=options, position=position)

        call_args = mock_call.call_args[0][1]
        assert len(call_args) == 4  # torrent_b64, uris, options, position
        assert call_args[1] == uris
        assert call_args[2] == options
        assert call_args[3] == position

    await client.close()


@pytest.mark.asyncio
async def test_add_metalink():
    """Test adding a Metalink download."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    metalink_data = b"<?xml version='1.0'?><metalink>...</metalink>"
    expected_b64 = base64.b64encode(metalink_data).decode("ascii")
    expected_gids = ["gid1", "gid2", "gid3"]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = expected_gids

        gids = await client.add_metalink(metalink_data)

        # Verify the call
        mock_call.assert_called_once()
        call_args = mock_call.call_args
        assert call_args[0][0] == "aria2.addMetalink"
        assert call_args[0][1][0] == expected_b64
        assert gids == expected_gids

    await client.close()


@pytest.mark.asyncio
async def test_get_peers():
    """Test getting peer list for a BitTorrent download."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    mock_peers_data = [
        {
            "peerId": "peer1",
            "ip": "192.168.1.100",
            "port": "6881",
            "downloadSpeed": "1024000",
            "uploadSpeed": "512000",
            "seeder": "false",
            "amChoking": "false",
            "peerChoking": "true",
        },
        {
            "peerId": "peer2",
            "ip": "192.168.1.101",
            "port": "6882",
            "downloadSpeed": "2048000",
            "uploadSpeed": "0",
            "seeder": "true",
            "amChoking": "true",
            "peerChoking": "false",
        },
    ]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_peers_data

        peers = await client.get_peers("gid123")

        # Verify the call
        mock_call.assert_called_once_with("aria2.getPeers", ["gid123"])

        # Verify the returned Peer objects
        assert len(peers) == 2

        # Check first peer
        assert peers[0].peer_id == "peer1"
        assert peers[0].ip == "192.168.1.100"
        assert peers[0].port == "6881"
        assert peers[0].download_speed == 1024000
        assert peers[0].upload_speed == 512000
        assert peers[0].seeder is False
        assert peers[0].am_choking is False
        assert peers[0].peer_choking is True

        # Check second peer
        assert peers[1].peer_id == "peer2"
        assert peers[1].seeder is True

    await client.close()


@pytest.mark.asyncio
async def test_get_servers():
    """Test getting server list for a download."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    mock_servers_data = [
        {
            "index": "1",
            "servers": [
                {
                    "uri": "http://example.com/file.zip",
                    "currentUri": "http://mirror.example.com/file.zip",
                    "downloadSpeed": "1048576",
                },
                {
                    "uri": "http://example.org/file.zip",
                    "currentUri": "http://example.org/file.zip",
                    "downloadSpeed": "524288",
                },
            ],
        },
    ]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_servers_data

        file_servers = await client.get_servers("gid456")

        # Verify the call
        mock_call.assert_called_once_with("aria2.getServers", ["gid456"])

        # Verify the returned FileServer objects
        assert len(file_servers) == 1
        assert file_servers[0].index == 1

        servers = file_servers[0].servers
        assert len(servers) == 2

        # Check first server
        assert servers[0].uri == "http://example.com/file.zip"
        assert servers[0].current_uri == "http://mirror.example.com/file.zip"
        assert servers[0].download_speed == 1048576

        # Check second server
        assert servers[1].uri == "http://example.org/file.zip"
        assert servers[1].download_speed == 524288

    await client.close()


@pytest.mark.asyncio
async def test_get_session_info():
    """Test getting session information."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    mock_session_data = {"sessionId": "test-session-id"}

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_session_data

        session_info = await client.get_session_info()

        mock_call.assert_called_once_with("aria2.getSessionInfo")
        assert session_info == mock_session_data

    await client.close()


@pytest.mark.asyncio
async def test_get_option():
    """Test getting download options."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    mock_options = {"dir": "/downloads", "max-connection-per-server": "4"}

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_options

        options = await client.get_option("gid123")

        mock_call.assert_called_once_with("aria2.getOption", ["gid123"])
        assert options == mock_options

    await client.close()


@pytest.mark.asyncio
async def test_change_option():
    """Test changing download options."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    new_options = {"max-download-limit": "1M"}

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "OK"

        result = await client.change_option("gid123", new_options)

        mock_call.assert_called_once_with("aria2.changeOption", ["gid123", new_options])
        assert result == "OK"

    await client.close()


@pytest.mark.asyncio
async def test_get_global_option():
    """Test getting global options."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    mock_options = {"max-concurrent-downloads": "5", "split": "5"}

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_options

        options = await client.get_global_option()

        mock_call.assert_called_once_with("aria2.getGlobalOption")
        assert options == mock_options

    await client.close()


@pytest.mark.asyncio
async def test_change_global_option():
    """Test changing global options."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    new_options = {"max-overall-download-limit": "2M"}

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "OK"

        result = await client.change_global_option(new_options)

        mock_call.assert_called_once_with("aria2.changeGlobalOption", [new_options])
        assert result == "OK"

    await client.close()


@pytest.mark.asyncio
async def test_change_position():
    """Test changing download position in queue."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = 3

        result = await client.change_position("gid123", 2, "POS_SET")

        mock_call.assert_called_once_with("aria2.changePosition", ["gid123", 2, "POS_SET"])
        assert result == 3

    await client.close()


@pytest.mark.asyncio
async def test_change_uri():
    """Test changing URIs for a download."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    del_uris = ["http://old.example.com/file"]
    add_uris = ["http://new.example.com/file", "http://mirror.example.com/file"]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = [1, 2]  # deleted 1, added 2

        deleted, added = await client.change_uri("gid123", 1, del_uris, add_uris)

        mock_call.assert_called_once_with("aria2.changeUri", ["gid123", 1, del_uris, add_uris])
        assert deleted == 1
        assert added == 2

    await client.close()


@pytest.mark.asyncio
async def test_change_uri_with_position():
    """Test changing URIs with position specified."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    del_uris = []
    add_uris = ["http://new.example.com/file"]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = [0, 1]

        deleted, added = await client.change_uri("gid123", 1, del_uris, add_uris, position=0)

        mock_call.assert_called_once_with("aria2.changeUri", ["gid123", 1, del_uris, add_uris, 0])
        assert deleted == 0
        assert added == 1

    await client.close()


@pytest.mark.asyncio
async def test_purge_download_result():
    """Test purging download results."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "OK"

        result = await client.purge_download_result()

        mock_call.assert_called_once_with("aria2.purgeDownloadResult")
        assert result == "OK"

    await client.close()


@pytest.mark.asyncio
async def test_remove_download_result():
    """Test removing a specific download result."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "OK"

        result = await client.remove_download_result("gid123")

        mock_call.assert_called_once_with("aria2.removeDownloadResult", ["gid123"])
        assert result == "OK"

    await client.close()


@pytest.mark.asyncio
async def test_save_session():
    """Test saving session."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "OK"

        result = await client.save_session()

        mock_call.assert_called_once_with("aria2.saveSession")
        assert result == "OK"

    await client.close()


@pytest.mark.asyncio
async def test_shutdown():
    """Test shutting down aria2 gracefully."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "OK"

        result = await client.shutdown()

        mock_call.assert_called_once_with("aria2.shutdown")
        assert result == "OK"

    await client.close()


@pytest.mark.asyncio
async def test_force_shutdown():
    """Test forcefully shutting down aria2."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "OK"

        result = await client.force_shutdown()

        mock_call.assert_called_once_with("aria2.forceShutdown")
        assert result == "OK"

    await client.close()


@pytest.mark.asyncio
async def test_list_methods():
    """Test listing available RPC methods."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    expected_methods = [
        "aria2.addUri",
        "aria2.getVersion",
        "aria2.shutdown",
        "system.listMethods",
    ]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = expected_methods

        result = await client.list_methods()

        mock_call.assert_called_once_with("system.listMethods")
        assert result == expected_methods
        assert isinstance(result, list)

    await client.close()


@pytest.mark.asyncio
async def test_multicall():
    """Test executing multiple RPC methods in a single request."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    calls = [
        {"methodName": "aria2.tellStatus", "params": ["gid1"]},
        {"methodName": "aria2.tellStatus", "params": ["gid2"]},
        {"methodName": "aria2.getGlobalStat", "params": []},
    ]

    expected_results = [
        {"gid": "gid1", "status": "active"},
        {"gid": "gid2", "status": "paused"},
        {"downloadSpeed": "1024"},
    ]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = expected_results

        result = await client.multicall(calls)

        mock_call.assert_called_once_with("system.multicall", [calls])
        assert result == expected_results
        assert len(result) == 3

    await client.close()


# TODO: Add integration tests with actual aria2c instance
# TODO: Add mock tests for error handling
