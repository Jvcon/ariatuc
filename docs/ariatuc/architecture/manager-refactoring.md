---
date: 2025-12-19
feature: "Manager层重构 - 4个核心Manager的设计和实现"
files:
  - src/ariatuc/core/config_manager.py
  - src/ariatuc/core/rpc_manager.py
  - src/ariatuc/core/download_manager.py
  - src/ariatuc/core/event_manager.py
---

# Manager Layer Refactoring

## Overview

This document summarizes the refactoring of core manager modules in ariatuc, focusing on:

1. **Consistent naming** - All managers use `*_manager.py` convention
2. **Protocol intelligence** - Automatic WebSocket/HTTP detection
3. **Event support** - New EventManager for WebSocket notifications
4. **Configuration enhancement** - Connection preferences and notifications

## Changes Made

### 1. File Naming Convention

All manager files now follow `*_manager.py` naming:
- `config_manager.py`
- `download_manager.py`
- `rpc_manager.py`
- `event_manager.py` (new)

### 2. ConfigManager

#### New Configuration Fields

**Connection Preferences**:
```python
prefer_websocket: bool = True
websocket_fallback_http: bool = True
connection_timeout: int = 10
reconnect_interval: int = 5
```

**Event Notifications**:
```python
enable_notifications: bool = True
play_sound_on_complete: bool = True
play_sound_on_error: bool = True
```

### 3. RPCManager

#### Design Decisions

**No Manual Protocol Fallback**:
- The `Aria2Client` factory in `aria2rpc` handles protocol selection
- `ws://` or `wss://` → WebSocketRPCClient
- `http://` or `https://` → HTTPRPCClient
- RPCManager focuses on connection management, not protocol fallback

#### New Features

**Protocol Detection**:
```python
ServerConfig.protocol: ConnectionProtocol  # Auto-detected from URL
ServerConfig.is_websocket: bool  # Quick check
RPCManager.get_protocol(name) -> ConnectionProtocol
RPCManager.is_websocket(name) -> bool
```

**Connection State Tracking**:
```python
class ServerState:
    state: ConnectionState  # DISCONNECTED/CONNECTING/CONNECTED/FAILED
    last_error: Optional[str]
    client: Optional[HTTPRPCClient | WebSocketRPCClient]
```

**Enhanced Methods**:
- `connect(name)` - Connect with automatic protocol selection
- `disconnect(name)` - Clean disconnect with proper cleanup
- `health_check(name)` - Verify connection health
- `get_websocket_client(name)` - Get WebSocket client for events
- `get_server_state(name)` - Get runtime state information

### 4. EventManager (NEW)

A new manager for WebSocket event notifications.

#### Features

**Event Subscription**:
```python
event_mgr = EventManager()
event_mgr.set_client(websocket_client)

async def on_complete(event_data):
    gid = event_data['gid']
    print(f"Download {gid} completed!")

event_mgr.on(Aria2Event.DOWNLOAD_COMPLETE, on_complete)
```

**Supported Events**:
- `DOWNLOAD_START`
- `DOWNLOAD_PAUSE`
- `DOWNLOAD_STOP`
- `DOWNLOAD_COMPLETE`
- `DOWNLOAD_ERROR`
- `BT_DOWNLOAD_COMPLETE`

**Built-in Handlers**:
- `set_notification_handler(handler)` - UI notifications
- `set_sound_handler(handler)` - Sound alerts
- Automatic notification generation

**Event Utilities**:
```python
# Wait for specific event
event_data = await event_mgr.wait_for_event(
    Aria2Event.DOWNLOAD_COMPLETE,
    predicate=lambda e: e['gid'] == target_gid,
    timeout=60
)

# Get statistics
counts = event_mgr.get_event_counts()
```

**Lifecycle Management**:
- `enable()` - Enable event monitoring
- `disable()` - Disable event monitoring
- `is_active()` - Check if monitoring is active
- Auto-enables when WebSocket client is set
- Auto-disables for HTTP clients

### 5. DownloadManager

No changes - already well-designed for state management.

## Architecture Benefits

### 1. Clean Separation of Concerns

- **ConfigManager**: Configuration persistence
- **RPCManager**: Connection management and protocol handling
- **DownloadManager**: Download state tracking
- **EventManager**: Event notification and callbacks

### 2. Protocol Intelligence

- Automatic protocol detection from URL
- No redundant fallback logic (delegated to aria2rpc)
- Easy access to WebSocket client for events
- Clear indication of protocol capabilities

### 3. Event System

- Centralized event handling
- Multiple callbacks per event support
- Built-in notification and sound support
- Event statistics tracking
- Utility methods for common patterns

### 4. Service Layer Ready

Managers are designed to be composed by a service layer:

```python
class Aria2Service:
    def __init__(self):
        self.config_mgr = ConfigManager()
        self.rpc_mgr = RPCManager()
        self.download_mgr = DownloadManager()
        self.event_mgr = EventManager()

    async def initialize(self):
        config = self.config_mgr.load()
        await self.rpc_mgr.connect()

        # Setup events if WebSocket
        ws_client = self.rpc_mgr.get_websocket_client()
        if ws_client:
            self.event_mgr.set_client(ws_client)
            self.event_mgr.on(Aria2Event.DOWNLOAD_COMPLETE, self._on_complete)
```

## Example Usage

See `examples/manager_integration.py` for complete example:

1. Loading configuration
2. Connecting to aria2 server
3. Auto-detecting protocol
4. Setting up event monitoring (if WebSocket)
5. Performing RPC operations
6. Handling events
7. Proper cleanup

Run the example:
```bash
# Start aria2c with RPC
aria2c --enable-rpc

# Run example
poetry run python examples/manager_integration.py
```

## Summary

This refactoring establishes a solid foundation:

✅ Consistent naming convention (`*_manager.py`)
✅ Smart protocol handling (leveraging aria2rpc)
✅ Comprehensive event system for WebSocket
✅ Enhanced configuration for connection preferences
✅ Ready for service layer integration
✅ Complete usage examples

The managers are ready to be composed into a higher-level service layer for the TUI application.

## See Also

- [Service Layer Architecture](service-layer.md)
- [Example: Manager Integration](../../examples/manager_integration.py)