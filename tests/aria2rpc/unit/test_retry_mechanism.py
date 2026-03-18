"""Tests for aria2 RPC retry mechanism."""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from aria2rpc.exceptions import (
    Aria2AuthenticationError,
    Aria2ConnectionError,
    Aria2TimeoutError,
)
from aria2rpc.http import HTTPRPCClient


@pytest.mark.asyncio
async def test_retry_on_connect_error():
    """Test retry mechanism for connection errors."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", max_retries=2, retry_backoff_factor=0.1)

    call_count = 0

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise httpx.ConnectError("Connection refused")

        # Return mock response on success
        class MockResponse:
            def json(self):
                return {"jsonrpc": "2.0", "id": "1", "result": "OK"}

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch.object(client.client, "post", new=mock_post):
        result = await client._call("aria2.getVersion")

        assert result == "OK"
        assert call_count == 3  # First 2 attempts failed, 3rd succeeded

    await client.close()


@pytest.mark.asyncio
async def test_retry_on_timeout():
    """Test retry mechanism for timeout errors."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", max_retries=2, retry_backoff_factor=0.1)

    call_count = 0

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.TimeoutException("Request timeout")

        class MockResponse:
            def json(self):
                return {"jsonrpc": "2.0", "id": "1", "result": "OK"}

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch.object(client.client, "post", new=mock_post):
        result = await client._call("aria2.getVersion")

        assert result == "OK"
        assert call_count == 2  # First attempt timed out, 2nd succeeded

    await client.close()


@pytest.mark.asyncio
async def test_retry_exhausted():
    """Test that exception is raised when all retries are exhausted."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", max_retries=2, retry_backoff_factor=0.1)

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        raise httpx.ConnectError("Connection refused")

    with patch.object(client.client, "post", new=mock_post):
        with pytest.raises(Aria2ConnectionError) as exc_info:
            await client._call("aria2.getVersion")

        assert "Cannot connect to aria2" in str(exc_info.value)

    await client.close()


@pytest.mark.asyncio
async def test_no_retry_on_authentication_error():
    """Test that authentication errors are not retried."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", max_retries=3, retry_backoff_factor=0.1)

    call_count = 0

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        response = AsyncMock()
        response.status_code = 401
        response.text = "Unauthorized"
        raise httpx.HTTPStatusError("401", request=AsyncMock(), response=response)

    with patch.object(client.client, "post", new=mock_post):
        with pytest.raises(Aria2AuthenticationError):
            await client._call("aria2.getVersion")

        # Should not retry authentication errors
        assert call_count == 1

    await client.close()


@pytest.mark.asyncio
async def test_retry_backoff_timing():
    """Test exponential backoff timing."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", max_retries=2, retry_backoff_factor=0.2)

    call_times = []

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        call_times.append(asyncio.get_event_loop().time())
        if len(call_times) <= 2:
            raise httpx.ConnectError("Connection refused")

        class MockResponse:
            def json(self):
                return {"jsonrpc": "2.0", "id": "1", "result": "OK"}

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch.object(client.client, "post", new=mock_post):
        await client._call("aria2.getVersion")

        # Check backoff delays
        # First retry: 0.2 * 2^0 = 0.2s
        # Second retry: 0.2 * 2^1 = 0.4s
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        assert 0.15 <= delay1 <= 0.25  # Allow some timing variance
        assert 0.35 <= delay2 <= 0.45  # Allow some timing variance

    await client.close()


@pytest.mark.asyncio
async def test_retry_with_zero_retries():
    """Test client with retry disabled (max_retries=0)."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", max_retries=0)

    call_count = 0

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        raise httpx.ConnectError("Connection refused")

    with patch.object(client.client, "post", new=mock_post):
        with pytest.raises(Aria2ConnectionError):
            await client._call("aria2.getVersion")

        # Should not retry
        assert call_count == 1

    await client.close()


@pytest.mark.asyncio
async def test_retry_on_http_server_error():
    """Test retry on 5xx HTTP errors."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc", max_retries=2, retry_backoff_factor=0.1)

    call_count = 0

    async def mock_post(*args, **kwargs):  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            response = AsyncMock()
            response.status_code = 503
            response.text = "Service Unavailable"
            raise httpx.HTTPStatusError(
                "503 Service Unavailable", request=AsyncMock(), response=response
            )

        class MockResponse:
            def json(self):
                return {"jsonrpc": "2.0", "id": "1", "result": "OK"}

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch.object(client.client, "post", new=mock_post):
        result = await client._call("aria2.getVersion")

        assert result == "OK"
        assert call_count == 2  # First attempt failed, 2nd succeeded

    await client.close()
