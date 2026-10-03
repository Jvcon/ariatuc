"""Unified client interface for aria2 RPC.

This module provides smart protocol selection based on URL scheme.
WebSocket protocol supports all HTTP RPC methods plus real-time events.

It also exposes the module-level ``is_aria2_next`` capability check, which
detects the ``aria2-next`` fork's media-extensions field on ``getVersion``.
"""

from aria2rpc.base import BaseRPCClient
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


async def is_aria2_next(client: BaseRPCClient) -> bool:
    """Check whether the connected server is ``aria2-next``.

    Detects the fork by calling ``getVersion`` and looking for the
    ``mediaFeatures`` field, which is unique to ``aria2-next``. Returns
    ``False`` against upstream ``aria2c``.

    Use this to gate calls to ``finish_media`` and ``retry_media`` so the
    same client code can talk to either engine without a hard requirement
    on aria2-next.

    Args:
        client: Any ``aria2rpc`` client (HTTP or WebSocket). The client does
            not need to be connected yet; ``getVersion`` opens a request.

    Returns:
        ``True`` if the server reports ``mediaFeatures``; ``False`` otherwise.

    Raises:
        Aria2ConnectionError: If the server cannot be reached.
        Aria2AuthenticationError: If the secret token is rejected.
        Aria2RPCError: For other RPC-level failures.

    Example:
        >>> from aria2rpc import Aria2Client, is_aria2_next
        >>> async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
        ...     if await is_aria2_next(client):
        ...         print("HLS / DASH media extensions are available")
    """
    version = await client.get_version()
    return version.is_aria2_next


__all__ = ["Aria2Client", "is_aria2_next"]
