"""WebSocket JSON-RPC client for aria2 with event support.

This module provides a WebSocket-based client that supports both RPC method calls
and real-time event notifications from aria2.
"""

import asyncio
import json
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from aria2rpc.base import BaseRPCClient
from aria2rpc.exceptions import (
    Aria2ConnectionError,
    Aria2RPCError,
    Aria2TimeoutError,
)


class Aria2Event(Enum):
    """aria2 event types."""

    DOWNLOAD_START = "aria2.onDownloadStart"
    DOWNLOAD_PAUSE = "aria2.onDownloadPause"
    DOWNLOAD_STOP = "aria2.onDownloadStop"
    DOWNLOAD_COMPLETE = "aria2.onDownloadComplete"
    DOWNLOAD_ERROR = "aria2.onDownloadError"
    BT_DOWNLOAD_COMPLETE = "aria2.onBtDownloadComplete"


# Type alias for event callback
EventCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class WebSocketRPCClient(BaseRPCClient):
    """WebSocket JSON-RPC client for aria2 with event notifications.

    This client supports both RPC method calls and subscribes to real-time
    events from aria2 such as download start, pause, complete, etc.

    All RPC methods (add_uri, add_torrent, tell_status, etc.) are inherited
    from BaseRPCClient. This class implements the WebSocket-specific _call()
    method, connection management, and event subscription system.

    Example:
        async def on_download_complete(event_data):
            gid = event_data['gid']
            print(f"Download {gid} completed!")

        async with WebSocketRPCClient("ws://localhost:6800/jsonrpc") as client:
            # Subscribe to events
            client.on(Aria2Event.DOWNLOAD_COMPLETE, on_download_complete)

            # Regular RPC calls
            gid = await client.add_uri(["http://example.com/file.zip"])

            # Keep connection alive to receive events
            await asyncio.sleep(3600)
    """

    def __init__(
        self,
        url: str = "ws://localhost:6800/jsonrpc",
        secret: str | None = None,
        timeout: float = 30.0,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        heartbeat_interval: float = 30.0,
    ) -> None:
        """Initialize the WebSocket RPC client.

        Args:
            url: The aria2 WebSocket RPC endpoint URL
            secret: The RPC secret token for authentication
            timeout: Request timeout in seconds (default: 30.0)
            auto_reconnect: Enable automatic reconnection (default: True)
            max_reconnect_attempts: Maximum reconnection attempts (default: 5)
            heartbeat_interval: Heartbeat interval in seconds (default: 30.0)
        """
        self.url = url
        self.secret = secret
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.heartbeat_interval = heartbeat_interval

        self._ws: ClientConnection | None = None
        self._request_id = 0
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._event_handlers: dict[Aria2Event, list[EventCallback]] = {}
        self._listener_task: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._reconnect_attempts = 0
        self._is_closing = False

    async def connect(self) -> None:
        """Establish WebSocket connection to aria2.

        Raises:
            Aria2ConnectionError: If connection fails
        """
        try:
            self._ws = await asyncio.wait_for(websockets.connect(self.url), timeout=self.timeout)
            self._reconnect_attempts = 0
            self._is_closing = False

            # Start listener and heartbeat tasks
            self._listener_task = asyncio.create_task(self._listen_loop())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        except TimeoutError as e:
            raise Aria2TimeoutError(f"Connection to {self.url} timed out") from e
        except Exception as e:
            raise Aria2ConnectionError(f"Failed to connect to {self.url}: {e}", self.url) from e

    async def close(self) -> None:
        """Close the WebSocket connection."""
        self._is_closing = True

        # Cancel tasks
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def _reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        if self._is_closing or not self.auto_reconnect:
            return

        self._reconnect_attempts += 1

        if self._reconnect_attempts > self.max_reconnect_attempts:
            raise Aria2ConnectionError(
                f"Max reconnection attempts ({self.max_reconnect_attempts}) exceeded",
                self.url,
            )

        # Exponential backoff: 2^n seconds
        delay = min(2**self._reconnect_attempts, 60)
        await asyncio.sleep(delay)

        try:
            await self.connect()
        except Exception:
            # Will be retried by the listener loop
            pass

    async def _listen_loop(self) -> None:
        """Listen for incoming messages from aria2."""
        while not self._is_closing:
            try:
                if not self._ws:
                    await self._reconnect()
                    continue

                message = await self._ws.recv()
                data = json.loads(message)

                # Handle RPC responses
                if "id" in data and data["id"] in self._pending_requests:
                    future = self._pending_requests.pop(data["id"])
                    if "error" in data:
                        error = data["error"]
                        future.set_exception(
                            Aria2RPCError(error.get("code", 0), error.get("message", ""))
                        )
                    else:
                        future.set_result(data.get("result"))

                # Handle event notifications
                elif "method" in data:
                    await self._handle_event(data["method"], data.get("params", []))

            except websockets.ConnectionClosed:
                if not self._is_closing:
                    await self._reconnect()
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error and continue
                pass

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat to keep connection alive."""
        while not self._is_closing:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if self._ws:
                    # Send a lightweight RPC call as heartbeat
                    await self.get_version()
            except asyncio.CancelledError:
                break
            except Exception:
                # Connection might be dead, listener will handle reconnect
                pass

    async def _handle_event(self, method: str, params: list[Any]) -> None:
        """Handle incoming event notification from aria2.

        Args:
            method: Event method name (e.g., 'aria2.onDownloadComplete')
            params: Event parameters
        """
        # Find matching event type
        event_type = None
        for event in Aria2Event:
            if event.value == method:
                event_type = event
                break

        if not event_type or event_type not in self._event_handlers:
            return

        # Extract event data (first param contains gid)
        event_data = {"gid": params[0]} if params else {}

        # Call all registered handlers for this event
        handlers = self._event_handlers[event_type]
        await asyncio.gather(
            *[handler(event_data) for handler in handlers],
            return_exceptions=True,
        )

    async def _call(
        self, method: str, params: list[Any] | None = None, timeout: float | None = None
    ) -> Any:
        """Make a JSON-RPC call via WebSocket.

        Args:
            method: The RPC method name
            params: List of parameters for the method
            timeout: Optional timeout for this specific call (currently not implemented
                    for WebSocket; uses response_timeout from constructor)

        Returns:
            The result from the RPC call

        Raises:
            Aria2ConnectionError: If not connected
            Aria2RPCError: If aria2 returns an error
            Aria2TimeoutError: If request times out

        Note:
            The timeout parameter is currently ignored for WebSocket connections.
            WebSocket uses the response_timeout set during initialization.
        """
        # Note: timeout parameter is for API compatibility with HTTPRPCClient
        # WebSocket implementation uses self.response_timeout instead
        _ = timeout  # Mark as intentionally unused
        if not self._ws:
            raise Aria2ConnectionError("Not connected to aria2", self.url)

        self._request_id += 1
        request_id = str(self._request_id)

        # Prepend secret token if configured
        if self.secret:
            params = [f"token:{self.secret}"] + (params or [])

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or [],
        }

        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            # Send request
            await self._ws.send(json.dumps(payload))

            # Wait for response with timeout
            result = await asyncio.wait_for(future, timeout=self.timeout)
            return result

        except TimeoutError as e:
            self._pending_requests.pop(request_id, None)
            raise Aria2TimeoutError(f"Request timed out after {self.timeout}s") from e

    # Event subscription methods

    def on(self, event: Aria2Event, callback: EventCallback) -> None:
        """Subscribe to an aria2 event.

        Args:
            event: The event type to subscribe to
            callback: Async callback function to handle the event
                     Signature: async def callback(event_data: dict) -> None
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(callback)

    def off(self, event: Aria2Event, callback: EventCallback | None = None) -> None:
        """Unsubscribe from an aria2 event.

        Args:
            event: The event type to unsubscribe from
            callback: Specific callback to remove, or None to remove all
        """
        if event not in self._event_handlers:
            return

        if callback is None:
            # Remove all handlers for this event
            del self._event_handlers[event]
        else:
            # Remove specific handler
            self._event_handlers[event] = [h for h in self._event_handlers[event] if h != callback]

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        _ = (exc_type, exc_val, exc_tb)  # Unused
        await self.close()
