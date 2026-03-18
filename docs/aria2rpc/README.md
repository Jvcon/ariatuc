# aria2rpc - Python Client Library

A standalone Python client library for aria2's RPC interface.

## Overview

aria2rpc is a modern, async Python library that provides a complete interface to aria2's RPC API. It supports both HTTP and WebSocket protocols with real-time event notifications.

**Status**: 95% complete (core functionality implemented)

## Features

- ✅ **Async/await** throughout
- ✅ **HTTP JSON-RPC** client
- ✅ **WebSocket client** with real-time events
- ✅ **Type-safe models** for all responses
- ✅ **Complete RPC coverage** (21+ methods)
- ✅ **Auto-reconnection** and heartbeat
- ✅ **BitTorrent** and **Metalink** support
- ✅ **Comprehensive tests** (63 tests, 18 unit + 45 integration)

## Documentation

### Getting Started
- **[Getting Started Guide](getting-started.md)** - Installation and basic usage

### Core Features
- **[WebSocket Guide](websocket.md)** - Real-time event notifications
- **[BitTorrent & Metalink](bittorrent-metalink.md)** - Advanced download features

### Development
- **[Testing Guide](testing.md)** - Running tests and contributing
- **[Architecture](architecture.md)** - Design and implementation details

## Quick Example

### HTTP Client

```python
from aria2rpc import Aria2Client

async def main():
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        # Add download
        gid = await client.add_uri(["http://example.com/file.zip"])

        # Check status
        status = await client.tell_status(gid)
        print(f"Download speed: {status.download_speed}")
```

### WebSocket Client with Events

```python
from aria2rpc import Aria2Client, Aria2Event

async def on_complete(event):
    print(f"Download completed: {event['gid']}")

async def main():
    async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
        # Subscribe to events
        client.on(Aria2Event.DOWNLOAD_COMPLETE, on_complete)

        # Add download
        gid = await client.add_uri(["http://example.com/file.zip"])

        # Keep running to receive events
        await asyncio.sleep(60)
```

## Installation

```bash
# As part of ariatuc
poetry install

# Or use aria2rpc standalone (when published)
pip install aria2rpc
```

## Design

aria2rpc uses a clean architecture with:

- **BaseRPCClient** - Abstract base class with all RPC methods
- **HTTPRPCClient** - HTTP JSON-RPC implementation
- **WebSocketRPCClient** - WebSocket with event support
- **Models** - Type-safe response models
- **Events** - Event-driven architecture

See [Architecture](architecture.md) for details.

## API Coverage

### Download Control
- `add_uri()`, `add_torrent()`, `add_metalink()`
- `remove()`, `force_remove()`
- `pause()`, `pause_all()`, `unpause()`, `unpause_all()`
- `force_pause()`, `force_pause_all()`

### Status & Information
- `tell_status()`, `tell_active()`, `tell_waiting()`, `tell_stopped()`
- `get_uris()`, `get_files()`, `get_peers()`, `get_servers()`
- `get_global_stat()`, `get_version()`, `get_session_info()`

### Configuration
- `get_option()`, `change_option()`
- `get_global_option()`, `change_global_option()`

### Queue Management
- `change_position()`, `change_uri()`

### Results Management
- `purge_download_result()`, `remove_download_result()`

### Session Management
- `save_session()`

See [Getting Started](getting-started.md) for usage examples.

## Testing

```bash
# Run unit tests (fast, no aria2c needed)
mise run test:unit

# Run integration tests (requires aria2c)
mise run test:integration

# Run all tests
mise run test
```

See [Testing Guide](testing.md) for details.

## Contributing

Contributions are welcome! See [Testing Guide](testing.md) for development setup.

## License

MIT License - see [LICENSE](../../LICENSE) file for details.
