"""aria2rpc - Python client for aria2 JSON-RPC interface.

This package provides a modern, async-first client for aria2 RPC interface.
It supports both HTTP and WebSocket JSON-RPC protocols, and is forward
compatible with the ``aria2-next`` fork's media extensions.

HTTP Example:
    >>> from aria2rpc import Aria2Client
    >>> async with Aria2Client("http://localhost:6800/jsonrpc") as client:
    ...     gid = await client.add_uri(["http://example.com/file.zip"])
    ...     status = await client.tell_status(gid)
    ...     print(f"Progress: {status.completed_length}/{status.total_length}")

WebSocket Example (with events):
    >>> from aria2rpc import Aria2Client, Aria2Event
    >>> async def on_complete(event):
    ...     print(f"Download {event['gid']} completed!")
    >>> # Aria2Client automatically selects WebSocket for ws:// URLs
    >>> async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
    ...     client.on(Aria2Event.DOWNLOAD_COMPLETE, on_complete)
    ...     gid = await client.add_uri(["http://example.com/file.zip"])
    ...     await asyncio.sleep(3600)  # Keep alive to receive events

aria2-next capability and media extensions:
    >>> from aria2rpc import Aria2Client, is_aria2_next
    >>> async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
    ...     if await is_aria2_next(client):
    ...         gid = await client.add_uri(
    ...             ["https://example.com/stream.m3u8"],
    ...             options={"media-pause-after-probe": "true"},
    ...         )
    ...         status = await client.tell_status(gid)
    ...         print(f"Media state: {status.media.state}, "
    ...               f"tracks: {len(status.media.tracks)}")

The package features smart protocol selection: use ws:// for WebSocket
(with real-time events) or http:// for HTTP (simple requests). Both
protocols support all 18 standard aria2 RPC methods; aria2-next's two
extra methods (``finishMedia``, ``retryMedia``) are exposed as
``finish_media`` and ``retry_media`` on every client.
"""

from aria2rpc._version import __version__
from aria2rpc.base import BaseRPCClient
from aria2rpc.client import Aria2Client, is_aria2_next
from aria2rpc.exceptions import (
    Aria2AuthenticationError,
    Aria2ConnectionError,
    Aria2Error,
    Aria2RPCError,
    Aria2TimeoutError,
)
from aria2rpc.http import HTTPRPCClient
from aria2rpc.models import (
    DownloadStatus,
    FileServer,
    GlobalStat,
    MediaDownloadStatus,
    MediaFeatures,
    MediaState,
    MediaTrack,
    Peer,
    Server,
    Version,
)
from aria2rpc.websocket import Aria2Event, WebSocketRPCClient

__all__ = [
    # Version
    "__version__",
    # Main client interface
    "Aria2Client",
    "is_aria2_next",
    # Base class for custom implementations
    "BaseRPCClient",
    # Protocol implementations
    "HTTPRPCClient",
    "WebSocketRPCClient",
    # Event system
    "Aria2Event",
    # Data models
    "DownloadStatus",
    "GlobalStat",
    "Version",
    "Peer",
    "Server",
    "FileServer",
    # aria2-next extensions
    "MediaState",
    "MediaTrack",
    "MediaDownloadStatus",
    "MediaFeatures",
    # Exceptions
    "Aria2Error",
    "Aria2ConnectionError",
    "Aria2TimeoutError",
    "Aria2AuthenticationError",
    "Aria2RPCError",
]
