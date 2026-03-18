# WebSocket Development Guide

The WebSocket RPC client provides real-time event notifications in addition to all standard RPC methods.

## Overview

`WebSocketRPCClient` is the WebSocket implementation of the aria2rpc package, offering:

- ✅ **Full RPC Support** - All methods available in HTTP client
- ✅ **Real-time Events** - Download status change notifications
- ✅ **Auto-reconnection** - Automatic reconnection with exponential backoff
- ✅ **Heartbeat** - Keep-alive mechanism to maintain connection
- ✅ **Async Callbacks** - Non-blocking event handling
- ✅ **Multiple Subscriptions** - Subscribe to multiple event types

## Quick Start

### Basic Usage

```python
import asyncio
from aria2rpc import WebSocketRPCClient, Aria2Event

async def main():
    # Connect to aria2 WebSocket endpoint
    async with WebSocketRPCClient(
        "ws://localhost:6800/jsonrpc",
        secret="my-secret"
    ) as client:
        # Add download
        gid = await client.add_uri(["http://example.com/file.zip"])
        print(f"Started download: {gid}")

        # Query status
        status = await client.tell_status(gid)
        print(f"Status: {status.status}")

asyncio.run(main())
```

### Event Subscription

```python
import asyncio
from aria2rpc import WebSocketRPCClient, Aria2Event

async def on_download_start(event):
    """Triggered when download starts"""
    print(f"📥 Download started: {event['gid']}")

async def on_download_complete(event):
    """Triggered when download completes"""
    print(f"✅ Download completed: {event['gid']}")

async def on_download_error(event):
    """Triggered on download error"""
    print(f"❌ Download error: {event['gid']}")

async def main():
    async with WebSocketRPCClient("ws://localhost:6800/jsonrpc") as client:
        # Subscribe to events
        client.on(Aria2Event.DOWNLOAD_START, on_download_start)
        client.on(Aria2Event.DOWNLOAD_COMPLETE, on_download_complete)
        client.on(Aria2Event.DOWNLOAD_ERROR, on_download_error)

        # Add download
        gid = await client.add_uri(["http://example.com/file.zip"])

        # Keep connection alive to receive events
        await asyncio.sleep(60)

asyncio.run(main())
```

## Supported Events

### Aria2Event Enum

| Event Type | Value | When Triggered |
|-----------|-------|----------------|
| `DOWNLOAD_START` | `aria2.onDownloadStart` | Download starts |
| `DOWNLOAD_PAUSE` | `aria2.onDownloadPause` | Download pauses |
| `DOWNLOAD_STOP` | `aria2.onDownloadStop` | Download stops |
| `DOWNLOAD_COMPLETE` | `aria2.onDownloadComplete` | Download completes |
| `DOWNLOAD_ERROR` | `aria2.onDownloadError` | Download error occurs |
| `BT_DOWNLOAD_COMPLETE` | `aria2.onBtDownloadComplete` | BitTorrent download completes |

### Event Data Structure

All event callbacks receive a dictionary parameter:

```python
{
    "gid": "2089b05ecca3d829"  # Download GID
}
```

## Connection Management

### Configuration Options

```python
client = WebSocketRPCClient(
    url="ws://localhost:6800/jsonrpc",
    secret="my-secret",                 # Optional RPC secret
    timeout=30.0,                       # Request timeout in seconds
    heartbeat_interval=60.0,            # Heartbeat interval
    auto_reconnect=True,                # Enable auto-reconnection
    max_reconnect_attempts=5,           # Max reconnection attempts
    reconnect_delay=5.0                 # Delay between reconnections
)
```

### Manual Connection Control

```python
# Manual connection
client = WebSocketRPCClient("ws://localhost:6800/jsonrpc")
await client.connect()

# Use client
version = await client.get_version()

# Manual disconnection
await client.close()
```

### Context Manager (Recommended)

```python
async with WebSocketRPCClient("ws://localhost:6800/jsonrpc") as client:
    # Automatic connection on entry
    # Automatic cleanup on exit
    pass
```

## Event Handling

### Subscribe to Events

```python
def on_event(event):
    print(f"Event: {event}")

# Subscribe
client.on(Aria2Event.DOWNLOAD_COMPLETE, on_event)
```

### Unsubscribe from Events

```python
# Unsubscribe specific handler
client.off(Aria2Event.DOWNLOAD_COMPLETE, on_event)

# Unsubscribe all handlers for an event
client.off(Aria2Event.DOWNLOAD_COMPLETE)
```

### Multiple Handlers

```python
async def handler1(event):
    print("Handler 1:", event)

async def handler2(event):
    print("Handler 2:", event)

# Both handlers will be called
client.on(Aria2Event.DOWNLOAD_COMPLETE, handler1)
client.on(Aria2Event.DOWNLOAD_COMPLETE, handler2)
```

## Advanced Features

### Auto-reconnection

The client automatically reconnects when connection is lost:

```python
client = WebSocketRPCClient(
    "ws://localhost:6800/jsonrpc",
    auto_reconnect=True,
    max_reconnect_attempts=5,
    reconnect_delay=5.0  # Initial delay, increases exponentially
)
```

Reconnection behavior:
1. First attempt: 5 seconds
2. Second attempt: 10 seconds
3. Third attempt: 20 seconds
4. And so on (exponential backoff)

### Heartbeat

Keeps connection alive by sending periodic messages:

```python
client = WebSocketRPCClient(
    "ws://localhost:6800/jsonrpc",
    heartbeat_interval=60.0  # Send heartbeat every 60 seconds
)
```

### Error Handling

```python
from aria2rpc.exceptions import (
    Aria2ConnectionError,
    Aria2TimeoutError,
    Aria2RPCError
)

try:
    async with WebSocketRPCClient("ws://localhost:6800/jsonrpc") as client:
        gid = await client.add_uri(["http://example.com/file.zip"])
except Aria2ConnectionError as e:
    print(f"Connection failed: {e}")
except Aria2TimeoutError as e:
    print(f"Request timeout: {e}")
except Aria2RPCError as e:
    print(f"RPC error: {e.code} - {e.message}")
```

## Complete Example

```python
import asyncio
from aria2rpc import WebSocketRPCClient, Aria2Event
from aria2rpc.exceptions import Aria2RPCError

class DownloadManager:
    def __init__(self, url: str, secret: str = None):
        self.client = WebSocketRPCClient(
            url,
            secret=secret,
            auto_reconnect=True,
            heartbeat_interval=30.0
        )
        self.downloads = {}

    async def start(self):
        """Start the download manager"""
        await self.client.connect()

        # Subscribe to events
        self.client.on(Aria2Event.DOWNLOAD_START, self.on_start)
        self.client.on(Aria2Event.DOWNLOAD_COMPLETE, self.on_complete)
        self.client.on(Aria2Event.DOWNLOAD_ERROR, self.on_error)

    async def on_start(self, event):
        """Handle download start event"""
        gid = event['gid']
        self.downloads[gid] = {"status": "active"}
        print(f"Download {gid} started")

    async def on_complete(self, event):
        """Handle download complete event"""
        gid = event['gid']
        self.downloads[gid] = {"status": "complete"}
        print(f"Download {gid} completed")

        # Get final status
        status = await self.client.tell_status(gid)
        print(f"Downloaded: {status.total_length} bytes")

    async def on_error(self, event):
        """Handle download error event"""
        gid = event['gid']
        self.downloads[gid] = {"status": "error"}
        print(f"Download {gid} failed")

    async def add_download(self, url: str) -> str:
        """Add a new download"""
        try:
            gid = await self.client.add_uri([url])
            print(f"Added download: {gid}")
            return gid
        except Aria2RPCError as e:
            print(f"Failed to add download: {e}")
            raise

    async def stop(self):
        """Stop the download manager"""
        await self.client.close()

async def main():
    manager = DownloadManager("ws://localhost:6800/jsonrpc")
    await manager.start()

    # Add some downloads
    await manager.add_download("http://example.com/file1.zip")
    await manager.add_download("http://example.com/file2.zip")

    # Keep running to receive events
    await asyncio.sleep(3600)  # Run for 1 hour

    await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

See [Testing Guide](testing.md) for information on testing WebSocket functionality.

## Best Practices

1. **Use Context Managers**: Ensures proper cleanup
2. **Handle Exceptions**: Always wrap RPC calls in try-except
3. **Keep Events Light**: Event handlers should be fast
4. **Enable Auto-reconnect**: For production applications
5. **Configure Timeouts**: Set appropriate timeout values
6. **Log Events**: Log important events for debugging

## Troubleshooting

### Connection Issues

```python
# Check if aria2c WebSocket is available
curl -i http://localhost:6800/
```

### Event Not Firing

- Ensure connection is established before download starts
- Check that download actually triggers the event (some may complete too fast)
- Verify event handler is registered correctly

### Memory Leaks

- Always unsubscribe event handlers when done
- Use context managers to ensure cleanup
- Close client explicitly if not using context manager

## See Also

- [Testing Guide](testing.md) - Integration testing
- [BitTorrent Guide](bittorrent-metalink.md) - BitTorrent-specific events
- [Architecture](architecture.md) - WebSocket client architecture
