---
date: 2025-12-19
feature: "Service层 - 核心业务逻辑层"
files:
  - src/ariatuc/core/service.py
dependencies:
  - ConfigManager
  - RPCManager
  - DownloadManager
  - EventManager
---

# Service Layer Architecture

## Overview

Aria2Service is the core business logic layer of ariatuc that coordinates all Manager components and provides a unified API for the UI layer.

## Architecture

### Layer Hierarchy

```
UI Layer (Textual TUI)
         ↕
Service Layer (Aria2Service)
         ↕
Manager Layer (4 Managers)
         ↕
Library Layer (aria2rpc)
         ↕
aria2 RPC Server
```

### Responsibilities

**Service Layer**:
- Composes and coordinates 4 Managers
- Provides high-level business APIs
- Unified error handling
- State synchronization management
- Event dispatching to UI

**Not Responsible**:
- Direct RPC calls (handled by RPCManager)
- Config file I/O (handled by ConfigManager)
- Local state storage (handled by DownloadManager)
- Event subscription (handled by EventManager)

## Core Components

### 1. Lifecycle Management

```python
service = Aria2Service()

# Initialize
await service.initialize()

# Connect to server
await service.connect()

# Use service...

# Cleanup
await service.shutdown()
```

**Lifecycle Methods**:
- `initialize()` - Load config, initialize Managers
- `connect(name)` - Connect to RPC server
- `disconnect(name)` - Disconnect
- `shutdown()` - Cleanup resources, save config

### 2. Download Operations

**Single Operations**:
```python
# Add download
gid = await service.add_download(
    ["http://example.com/file.zip"],
    options=DownloadOptions(dir="/tmp", split=4)
)

# Add torrent
gid = await service.add_torrent(torrent_data)

# Control
await service.pause_download(gid)
await service.resume_download(gid)
await service.remove_download(gid, force=False)
```

**Batch Operations**:
```python
await service.pause_all()
await service.resume_all()
await service.purge_completed()
```

### 3. State Synchronization

**Manual Refresh**:
```python
await service.refresh_downloads()
await service.refresh_download(gid)
```

**Auto Refresh**:
```python
await service.start_auto_refresh(interval=1.0)
await service.stop_auto_refresh()
```

### 4. Event-Driven Updates

When using WebSocket, Service automatically subscribes to aria2 events:

```python
DOWNLOAD_START → Refresh state
DOWNLOAD_COMPLETE → Refresh + notify
DOWNLOAD_ERROR → Refresh + notify
DOWNLOAD_PAUSE → Refresh state
DOWNLOAD_STOP → Refresh state
```

**UI Integration**:
```python
service.set_ui_refresh_callback(on_ui_refresh)
service.set_notification_callback(on_notification)
```

### 5. Query Methods

```python
# By status
active = service.get_active_downloads()
waiting = service.get_waiting_downloads()
paused = service.get_paused_downloads()
stopped = service.get_stopped_downloads()

# Single query
download = service.get_download(gid)

# Global stats
stats = await service.get_global_stat()
version = await service.get_version()
```

### 6. Server Management

```python
service.add_server("local", "ws://localhost:6800/jsonrpc", secret=None)
service.remove_server("local")
await service.switch_server("remote")
servers = service.list_servers()
healthy = await service.test_connection()
```

## Error Handling

Service layer defines 3 exception types:

```python
try:
    await service.add_download(urls)
except ConnectionError:
    # Connection errors
    pass
except DownloadOperationError:
    # Download operation errors
    pass
except ServiceError:
    # Generic service errors
    pass
```

## Configuration

### DownloadOptions

```python
options = DownloadOptions(
    dir="/path/to/download",
    out="filename.zip",
    max_connection_per_server=4,
    split=4,
    max_download_limit=1024*1024,
    header=["User-Agent: MyApp"],
    user_agent="MyApp/1.0"
)
```

## State Properties

```python
service.is_connected  # bool
service.current_server  # str | None
service.is_websocket  # bool
service.event_monitoring_active  # bool
```

## Integration with Textual

```python
from textual.app import App
from ariatuc.core import Aria2Service

class AriatucApp(App):
    def __init__(self):
        super().__init__()
        self.service = Aria2Service()

    async def on_mount(self):
        await self.service.initialize()
        self.service.set_ui_refresh_callback(self.refresh_ui)
        self.service.set_notification_callback(self.show_notification)
        await self.service.connect()
        await self.service.start_auto_refresh()

    async def on_unmount(self):
        await self.service.shutdown()
```

## Performance Considerations

### Refresh Strategy

**Auto Refresh (Polling)**:
- Pros: Works with HTTP and WebSocket
- Cons: Has delay, increased network overhead
- Use: HTTP connections

**Event-Driven (WebSocket)**:
- Pros: Real-time, no delay, low overhead
- Cons: WebSocket only
- Use: WebSocket connections

**Recommended**:
- WebSocket: Disable auto refresh, rely on events
- HTTP: Enable auto refresh with 1-2 second interval

### Memory Management

- DownloadManager maintains all download states in memory
- For large numbers of downloads (1000+), periodically clean completed downloads
- Use `purge_completed()` to clean history

## Extension Points

### Custom Event Handlers

```python
async def custom_handler(event_data):
    # Custom logic
    pass

service.event_mgr.on(Aria2Event.DOWNLOAD_COMPLETE, custom_handler)
```

### Custom Notifications

```python
def custom_notification(data):
    send_to_slack(data['message'])

service.set_notification_callback(custom_notification)
```

## See Also

- [Manager Refactoring](manager-refactoring.md)
- [Example: Manager Integration](../../examples/manager_integration.py)
- [Example: Service Usage](../../examples/service_usage.py)