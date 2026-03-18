"""Tests for aria2 RPC configurable timeout."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from aria2rpc.exceptions import Aria2TimeoutError
from aria2rpc.http import HTTPRPCClient


@pytest.mark.asyncio
async def test_default_timeout():
    """Test that default timeout is used when no override is provided."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", timeout=10.0)

    captured_timeout = None

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        nonlocal captured_timeout
        captured_timeout = kwargs.get("timeout")

        class MockResponse:
            def json(self):
                return {"jsonrpc": "2.0", "id": "1", "result": "OK"}

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch.object(client.client, "post", new=mock_post):
        await client._call("aria2.getVersion")

        # Should use default timeout
        assert captured_timeout == 10.0

    await client.close()


@pytest.mark.asyncio
async def test_custom_timeout():
    """Test that custom timeout overrides default."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", timeout=10.0)

    captured_timeout = None

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        nonlocal captured_timeout
        captured_timeout = kwargs.get("timeout")

        class MockResponse:
            def json(self):
                return {"jsonrpc": "2.0", "id": "1", "result": "OK"}

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch.object(client.client, "post", new=mock_post):
        # Call with custom timeout
        await client._call("aria2.getVersion", timeout=5.0)

        # Should use custom timeout
        assert captured_timeout == 5.0

    await client.close()


@pytest.mark.asyncio
async def test_timeout_exception_with_custom_timeout():
    """Test timeout exception with custom timeout."""
    client = HTTPRPCClient(
        "http://localhost:6800/jsonrpc",
        timeout=10.0,
        max_retries=0,  # Disable retries for simplicity
    )

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        timeout_val = kwargs.get("timeout")
        # Simulate timeout only if custom timeout is used
        if timeout_val == 2.0:
            raise httpx.TimeoutException("Request timeout")

        class MockResponse:
            def json(self):
                return {"jsonrpc": "2.0", "id": "1", "result": "OK"}

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch.object(client.client, "post", new=mock_post):
        # Should timeout with custom short timeout
        with pytest.raises(Aria2TimeoutError):
            await client._call("aria2.getVersion", timeout=2.0)

    await client.close()


@pytest.mark.asyncio
async def test_timeout_zero_uses_zero():
    """Test that timeout=0 is explicitly used (not treated as None)."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", timeout=10.0)

    captured_timeout = None

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        nonlocal captured_timeout
        captured_timeout = kwargs.get("timeout")

        class MockResponse:
            def json(self):
                return {"jsonrpc": "2.0", "id": "1", "result": "OK"}

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch.object(client.client, "post", new=mock_post):
        # Call with explicit zero timeout (infinite)
        await client._call("aria2.getVersion", timeout=0.0)

        # Should use zero timeout (infinite)
        assert captured_timeout == 0.0

    await client.close()


@pytest.mark.asyncio
async def test_timeout_applies_to_all_retries():
    """Test that custom timeout applies to all retry attempts."""
    client = HTTPRPCClient(
        "http://localhost:6800/jsonrpc",
        timeout=10.0,
        max_retries=2,
        retry_backoff_factor=0.1,
    )

    captured_timeouts = []

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        captured_timeouts.append(kwargs.get("timeout"))
        if len(captured_timeouts) <= 2:
            raise httpx.TimeoutException("Request timeout")

        class MockResponse:
            def json(self):
                return {"jsonrpc": "2.0", "id": "1", "result": "OK"}

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch.object(client.client, "post", new=mock_post):
        # Call with custom timeout
        await client._call("aria2.getVersion", timeout=5.0)

        # All retry attempts should use the same custom timeout
        assert len(captured_timeouts) == 3  # 1 initial + 2 retries
        assert all(t == 5.0 for t in captured_timeouts)

    await client.close()
