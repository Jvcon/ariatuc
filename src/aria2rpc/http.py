"""HTTP JSON-RPC client for aria2."""

import asyncio
from typing import Any

import httpx

from aria2rpc.base import BaseRPCClient
from aria2rpc.exceptions import (
    Aria2AuthenticationError,
    Aria2ConnectionError,
    Aria2RPCError,
    Aria2TimeoutError,
)


class HTTPRPCClient(BaseRPCClient):
    """HTTP JSON-RPC client for aria2.

    This client implements the JSON-RPC 2.0 protocol over HTTP/HTTPS.
    It handles authentication, error handling, and provides typed responses.

    All RPC methods (add_uri, add_torrent, tell_status, etc.) are inherited
    from BaseRPCClient. This class only implements the HTTP-specific _call()
    method and connection management.

    Example:
        async with HTTPRPCClient("http://localhost:6800/jsonrpc") as client:
            gid = await client.add_uri(["http://example.com/file.zip"])
            status = await client.tell_status(gid)
            print(f"Download progress: {status.completed_length}/{status.total_length}")
    """

    def __init__(
        self,
        url: str = "http://localhost:6800/jsonrpc",
        secret: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
    ) -> None:
        """Initialize the HTTP RPC client.

        Args:
            url: The aria2 RPC endpoint URL
            secret: The RPC secret token for authentication (--rpc-secret)
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retry attempts for transient failures (default: 3)
            retry_backoff_factor: Backoff factor for exponential retry delay (default: 0.5)
                                 Delay = retry_backoff_factor * (2 ** attempt_number)
        """
        self.url = url
        self.secret = secret
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.client = httpx.AsyncClient(timeout=timeout)
        self._request_id = 0

    async def _call(
        self, method: str, params: list[Any] | None = None, timeout: float | None = None
    ) -> Any:
        """Make a JSON-RPC call to aria2 with retry logic.

        Args:
            method: The RPC method name (e.g., 'aria2.addUri')
            params: List of parameters for the method
            timeout: Optional timeout for this specific call (overrides default)

        Returns:
            The result from the RPC call

        Raises:
            Aria2ConnectionError: If connection to aria2 fails after retries
            Aria2TimeoutError: If request times out after retries
            Aria2AuthenticationError: If authentication fails (not retried)
            Aria2RPCError: If aria2 returns an error (not retried)
        """
        self._request_id += 1

        # Prepend secret token if configured
        if self.secret:
            params = [f"token:{self.secret}"] + (params or [])

        payload = {
            "jsonrpc": "2.0",
            "id": str(self._request_id),
            "method": method,
            "params": params or [],
        }

        last_exception: Exception | None = None

        # Use provided timeout or fall back to default
        request_timeout = timeout if timeout is not None else self.timeout

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(self.url, json=payload, timeout=request_timeout)
                response.raise_for_status()

                # Parse response
                try:
                    data = response.json()
                except Exception as e:
                    raise Aria2ConnectionError(
                        f"Invalid JSON response from {self.url}", self.url
                    ) from e

                # Check for RPC error (don't retry)
                if "error" in data:
                    error = data["error"]
                    code = error.get("code", 0)
                    message = error.get("message", "Unknown error")
                    raise Aria2RPCError(code, message)

                return data.get("result")

            except httpx.ConnectError as e:
                last_exception = Aria2ConnectionError(
                    f"Cannot connect to aria2 at {self.url}", self.url
                )
                last_exception.__cause__ = e
            except httpx.TimeoutException as e:
                last_exception = Aria2TimeoutError(f"Request to {self.url} timed out")
                last_exception.__cause__ = e
            except httpx.HTTPStatusError as e:
                # Don't retry authentication errors
                if e.response.status_code == 401:
                    raise Aria2AuthenticationError(
                        "Authentication failed: invalid secret token"
                    ) from e
                # Retry other HTTP errors
                last_exception = Aria2ConnectionError(
                    f"HTTP error {e.response.status_code}: {e.response.text}", self.url
                )
                last_exception.__cause__ = e
            except (Aria2RPCError, Aria2AuthenticationError, Aria2ConnectionError):
                # Don't retry these errors
                raise

            # If this was the last attempt, raise the exception
            if attempt >= self.max_retries:
                break

            # Calculate backoff delay: backoff_factor * (2 ** attempt)
            delay = self.retry_backoff_factor * (2**attempt)
            await asyncio.sleep(delay)

        # Raise the last exception if all retries failed
        if last_exception:
            raise last_exception

        # Should never reach here
        raise Aria2ConnectionError(f"Request to {self.url} failed", self.url)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        _ = (exc_type, exc_val, exc_tb)  # Unused
        await self.close()
