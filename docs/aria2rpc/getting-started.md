# Getting Started with aria2rpc

Quick guide to using the aria2rpc Python library.

## Installation

Currently, aria2rpc is part of the ariatuc project:

```bash
git clone https://github.com/Jvcon/ariatuc.git
cd ariatuc
poetry install
```

When published to PyPI, you'll be able to install it directly:

```bash
pip install aria2rpc  # Future
```

## Prerequisites

You need a running aria2c instance with RPC enabled:

```bash
# Basic RPC server
aria2c --enable-rpc

# With authentication (recommended)
aria2c --enable-rpc --rpc-secret=my-secret-token

# Custom port
aria2c --enable-rpc --rpc-listen-port=6800
```

## Basic Usage

### HTTP Client

The HTTP client is simple and suitable for most use cases:

```python
import asyncio
from aria2rpc import Aria2Client

async def main():
    # Connect to aria2
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        # Add a download
        gid = await client.add_uri(["http://example.com/file.zip"])
        print(f"Download started: {gid}")

        # Check status
        status = await client.tell_status(gid)
        print(f"Status: {status.status}")
        print(f"Progress: {status.completed_length}/{status.total_length}")

asyncio.run(main())
```

### With Authentication

If your aria2c uses authentication:

```python
async with Aria2Client(
    "http://localhost:6800/jsonrpc",
    secret="my-secret-token"
) as client:
    # Your code here
    pass
```

### WebSocket Client

WebSocket client provides real-time event notifications:

```python
from aria2rpc import Aria2Client, Aria2Event

async def on_download_complete(event):
    print(f"Download completed: {event['gid']}")

async def main():
    async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
        # Subscribe to events
        client.on(Aria2Event.DOWNLOAD_COMPLETE, on_download_complete)

        # Add download
        gid = await client.add_uri(["http://example.com/file.zip"])

        # Keep connection alive
        await asyncio.sleep(60)

asyncio.run(main())
```

See [WebSocket Guide](websocket.md) for more details.

## Common Operations

### Add Downloads

```python
# HTTP/FTP download
gid = await client.add_uri(["http://example.com/file.zip"])

# With options
gid = await client.add_uri(
    ["http://example.com/file.zip"],
    options={"dir": "/downloads", "max-connection-per-server": "4"}
)

# BitTorrent
with open("file.torrent", "rb") as f:
    torrent_data = f.read()
gid = await client.add_torrent(torrent_data)

# Metalink
with open("file.metalink", "rb") as f:
    metalink_data = f.read()
gids = await client.add_metalink(metalink_data)  # Returns list of GIDs
```

### Control Downloads

```python
# Pause
await client.pause(gid)

# Resume
await client.unpause(gid)

# Remove
await client.remove(gid)

# Force remove
await client.force_remove(gid)
```

### Query Status

```python
# Single download
status = await client.tell_status(gid)
print(f"Speed: {status.download_speed} bytes/s")
print(f"Progress: {status.completed_length}/{status.total_length}")

# Active downloads
active = await client.tell_active()
for dl in active:
    print(f"{dl.gid}: {dl.status}")

# Waiting downloads
waiting = await client.tell_waiting(0, 10)  # offset, num

# Stopped downloads
stopped = await client.tell_stopped(0, 10)
```

### Global Statistics

```python
stats = await client.get_global_stat()
print(f"Download speed: {stats.download_speed} bytes/s")
print(f"Upload speed: {stats.upload_speed} bytes/s")
print(f"Active: {stats.num_active}")
print(f"Waiting: {stats.num_waiting}")
```

### Configuration

```python
# Get download options
options = await client.get_option(gid)

# Change download options
await client.change_option(gid, {"max-download-limit": "1M"})

# Get global options
global_opts = await client.get_global_option()

# Change global options
await client.change_global_option({"max-concurrent-downloads": "5"})
```

## Error Handling

```python
from aria2rpc.exceptions import (
    Aria2ConnectionError,
    Aria2TimeoutError,
    Aria2RPCError
)

try:
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        gid = await client.add_uri(["http://example.com/file.zip"])
except Aria2ConnectionError as e:
    print(f"Connection failed: {e}")
except Aria2TimeoutError as e:
    print(f"Request timeout: {e}")
except Aria2RPCError as e:
    print(f"RPC error {e.code}: {e.message}")
```

## Data Models

All responses are wrapped in typed models:

```python
# DownloadStatus
status = await client.tell_status(gid)
status.gid           # str
status.status        # str: "active", "waiting", "paused", "error", "complete"
status.total_length  # int: total bytes
status.completed_length  # int: downloaded bytes
status.download_speed    # int: bytes/sec
status.upload_speed      # int: bytes/sec (for torrents)
status.files         # list: file information

# GlobalStat
stats = await client.get_global_stat()
stats.download_speed  # int
stats.upload_speed    # int
stats.num_active      # int
stats.num_waiting     # int
stats.num_stopped     # int

# Version
version = await client.get_version()
version.version           # str: e.g., "1.35.0"
version.enabled_features  # list: enabled features
```

## Client Modes

### Factory Function (Recommended)

The `Aria2Client()` function automatically selects HTTP or WebSocket:

```python
from aria2rpc import Aria2Client

# Returns HTTPRPCClient
client = Aria2Client("http://localhost:6800/jsonrpc")

# Returns WebSocketRPCClient
client = Aria2Client("ws://localhost:6800/jsonrpc")
```

### Direct Client Creation

You can also create clients directly:

```python
from aria2rpc import HTTPRPCClient, WebSocketRPCClient

# HTTP client
http_client = HTTPRPCClient("http://localhost:6800/jsonrpc")

# WebSocket client
ws_client = WebSocketRPCClient("ws://localhost:6800/jsonrpc")
```

## Next Steps

- [WebSocket Guide](websocket.md) - Real-time events and notifications
- [BitTorrent & Metalink](bittorrent-metalink.md) - Advanced features
- [Testing Guide](testing.md) - Contributing and testing
- [Architecture](architecture.md) - Design and implementation

## API Reference

For complete API documentation, see:
- [aria2 RPC Interface](https://aria2.github.io/manual/en/html/aria2c.html#rpc-interface)
- Source code in `src/aria2rpc/`
