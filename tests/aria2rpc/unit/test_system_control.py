"""Tests for aria2 RPC system control methods."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from aria2rpc.http import HTTPRPCClient


@pytest.mark.asyncio
async def test_shutdown():
    """Test graceful shutdown."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "OK"

        result = await client.shutdown()

        # Verify the call
        mock_call.assert_called_once_with("aria2.shutdown")
        assert result == "OK"

    await client.close()


@pytest.mark.asyncio
async def test_force_shutdown():
    """Test forced shutdown."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "OK"

        result = await client.force_shutdown()

        # Verify the call
        mock_call.assert_called_once_with("aria2.forceShutdown")
        assert result == "OK"

    await client.close()


@pytest.mark.asyncio
async def test_list_methods():
    """Test listing available RPC methods."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    expected_methods = [
        "aria2.addUri",
        "aria2.addTorrent",
        "aria2.remove",
        "aria2.pause",
        "aria2.tellStatus",
        "aria2.getGlobalStat",
        "aria2.shutdown",
        "system.listMethods",
        "system.multicall",
    ]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = expected_methods

        methods = await client.list_methods()

        # Verify the call
        mock_call.assert_called_once_with("system.listMethods")
        assert methods == expected_methods
        assert "aria2.addUri" in methods
        assert "system.multicall" in methods

    await client.close()


@pytest.mark.asyncio
async def test_multicall_basic():
    """Test multicall with multiple operations."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    calls = [
        {"methodName": "aria2.tellStatus", "params": ["gid1"]},
        {"methodName": "aria2.tellStatus", "params": ["gid2"]},
        {"methodName": "aria2.getGlobalStat", "params": []},
    ]

    expected_results = [
        {"gid": "gid1", "status": "active"},
        {"gid": "gid2", "status": "paused"},
        {"downloadSpeed": "1024000", "uploadSpeed": "512000"},
    ]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = expected_results

        results = await client.multicall(calls)

        # Verify the call
        mock_call.assert_called_once_with("system.multicall", [calls])
        assert results == expected_results
        assert len(results) == 3

    await client.close()


@pytest.mark.asyncio
async def test_multicall_empty():
    """Test multicall with empty call list."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    calls: list[dict[str, Any]] = []

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = []

        results = await client.multicall(calls)

        # Verify the call
        mock_call.assert_called_once_with("system.multicall", [calls])
        assert results == []

    await client.close()


@pytest.mark.asyncio
async def test_multicall_mixed_methods():
    """Test multicall with different method types."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    calls = [
        {"methodName": "aria2.getGlobalStat", "params": []},
        {"methodName": "aria2.pause", "params": ["gid123"]},
        {"methodName": "aria2.getVersion", "params": []},
    ]

    expected_results = [
        {"downloadSpeed": "0", "uploadSpeed": "0"},
        "gid123",  # pause returns GID
        {"version": "1.36.0"},
    ]

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = expected_results

        results = await client.multicall(calls)

        # Verify the call
        mock_call.assert_called_once_with("system.multicall", [calls])
        assert results == expected_results
        assert len(results) == 3

    await client.close()
