"""Unified client interface for aria2 RPC.

This module provides smart protocol selection based on URL scheme.
WebSocket protocol supports all HTTP RPC methods plus real-time events.
"""

from aria2rpc.http import HTTPRPCClient
from aria2rpc.websocket import WebSocketRPCClient


def Aria2Client(url: str, **kwargs) -> WebSocketRPCClient | HTTPRPCClient:
    """Smart aria2 RPC client with automatic protocol selection.

    Based on aria2 official documentation, WebSocket protocol supports all
    HTTP RPC methods. The only difference is that WebSocket also provides
    real-time event notifications.

    Protocol Selection:
        - ws:// or wss:// → WebSocketRPCClient (all 18 methods + events)
        - http:// or https:// → HTTPRPCClient (all 18 methods, no events)

    Args:
        url: aria2 RPC endpoint URL
        **kwargs: Additional arguments passed to the specific client
            For WebSocket: secret, timeout, auto_reconnect,
                          max_reconnect_attempts, heartbeat_interval
            For HTTP: secret, timeout

    Returns:
        WebSocketRPCClient or HTTPRPCClient based on URL scheme

    Examples:
        WebSocket client (recommended for long-running apps):

        >>> from aria2rpc import Aria2Client, Aria2Event
        >>> async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
        ...     # All 18 RPC methods available
        ...     gid = await client.add_uri(["http://example.com/file.zip"])
        ...     files = await client.get_files(gid)
        ...     await client.pause_all()
        ...
        ...     # Event subscription (WebSocket only)
        ...     client.on(Aria2Event.DOWNLOAD_COMPLETE, on_complete)

        HTTP client (simple scripts, no events):

        >>> async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        ...     # All 18 RPC methods available
        ...     gid = await client.add_uri(["http://example.com/file.zip"])
        ...     files = await client.get_files(gid)
        ...     # client.on() not available (HTTP doesn't support events)
    """
    if url.startswith(("ws://", "wss://")):
        return WebSocketRPCClient(url, **kwargs)
    return HTTPRPCClient(url, **kwargs)


__all__ = ["Aria2Client"]
