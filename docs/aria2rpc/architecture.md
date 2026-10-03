---
date: 2025-12-19
feature: "aria2rpc 包的整体架构设计 - RPC 客户端库核心架构"
files:
  - src/aria2rpc/base.py
  - src/aria2rpc/http.py
  - src/aria2rpc/websocket.py
  - src/aria2rpc/client.py
  - src/aria2rpc/models.py
  - src/aria2rpc/events.py
  - src/aria2rpc/exceptions.py
---

# Architecture Overview

## 概述

This document describes the architecture of the aria2rpc package, a standalone RPC client library for aria2. The package uses modern design patterns to provide a clean, type-safe, and extensible interface for interacting with aria2's JSON-RPC API over HTTP and WebSocket protocols.

## Package Structure

```
ariatuc/
├── src/
│   ├── aria2rpc/          # Standalone RPC client library
│   │   ├── __init__.py    # Package exports
│   │   ├── base.py        # BaseRPCClient (abstract base class)
│   │   ├── http.py        # HTTPRPCClient
│   │   ├── websocket.py   # WebSocketRPCClient
│   │   ├── client.py      # Aria2Client factory function
│   │   ├── models.py      # Data models (DownloadStatus, etc.)
│   │   ├── events.py      # Event definitions
│   │   └── exceptions.py  # Custom exceptions
│   └── ariatuc/           # TUI application
│       ├── main.py
│       ├── ui/            # Textual UI components
│       ├── core/          # Business logic
│       └── utils/         # Utilities
└── tests/
    ├── test_aria2_client.py
    ├── test_download_manager.py
    ├── test_websocket_client.py
    └── test_websocket_complete.py
```

## aria2rpc Package Design

### BaseRPCClient Pattern

The core of aria2rpc uses the Template Method pattern with an abstract base class:

```
┌─────────────────────────────────────────────┐
│         BaseRPCClient (ABC)                 │
├─────────────────────────────────────────────┤
│ @abstractmethod                             │
│ async def _call(method, params) -> Any      │
│                                             │
│ # 21+ RPC methods                           │
│ async def add_uri(...)                      │
│ async def add_torrent(...)                  │
│ async def tell_status(...)                  │
│ async def get_version(...)                  │
│ ... (all other methods)                     │
└─────────────────────────────────────────────┘
              ▲               ▲
              │               │
    ┌─────────┴────────┐  ┌──┴──────────────┐
    │ HTTPRPCClient    │  │ WebSocketRPC    │
    │                  │  │ Client          │
    ├──────────────────┤  ├─────────────────┤
    │ _call() via HTTP │  │ _call() via WS  │
    │ Connection mgmt  │  │ Event system    │
    │ Context manager  │  │ Auto-reconnect  │
    └──────────────────┘  │ Heartbeat       │
                          └─────────────────┘
```

### Design Principles

#### 1. Template Method Pattern

**BaseRPCClient** defines the algorithm structure (RPC method implementations), while subclasses implement the specific details (`_call()` method):

```python
class BaseRPCClient(ABC):
    @abstractmethod
    async def _call(self, method: str, params: list[Any] | None = None) -> Any:
        """Subclasses implement protocol-specific details"""
        pass

    async def add_uri(self, uris, options=None, position=None):
        """Common implementation for all protocols"""
        params = [uris]
        if options:
            params.append(options)
        if position is not None:
            params.append(position)
        return await self._call("aria2.addUri", params)  # Calls subclass method
```

#### 2. Strategy Pattern

Different protocol implementations (HTTP, WebSocket) are interchangeable strategies:

```python
# Both clients implement the same interface
http_client = HTTPRPCClient(url)
ws_client = WebSocketRPCClient(url)

# Can use either client with the same API
await http_client.add_uri([...])
await ws_client.add_uri([...])
```

#### 3. Factory Method Pattern

`Aria2Client()` function automatically selects the appropriate implementation:

```python
def Aria2Client(url: str, **kwargs):
    """Factory function that returns the appropriate client"""
    if url.startswith(("ws://", "wss://")):
        return WebSocketRPCClient(url, **kwargs)
    else:
        return HTTPRPCClient(url, **kwargs)
```

### Benefits of This Architecture

1. **DRY (Don't Repeat Yourself)**
   - RPC methods implemented once in BaseRPCClient
   - No code duplication between HTTP and WebSocket clients

2. **Single Responsibility**
   - BaseRPCClient: RPC method implementations
   - HTTPRPCClient: HTTP protocol specifics
   - WebSocketRPCClient: WebSocket protocol + events

3. **Open/Closed Principle**
   - Open for extension (add new protocol implementations)
   - Closed for modification (adding RPC methods doesn't require changing existing code)

4. **Easy to Extend**
   - Adding new RPC methods: only modify BaseRPCClient
   - Adding new protocol: create new subclass, implement `_call()`

### Code Metrics

**Before Refactoring** (duplicated code):
- `http.py`: ~500 lines (21 methods + HTTP logic)
- `websocket.py`: ~550 lines (21 methods + WebSocket logic)
- **Total**: 1050 lines with ~400 lines duplicated

**After Refactoring** (BaseRPCClient pattern):
- `base.py`: 622 lines (all 21+ RPC methods)
- `http.py`: 125 lines (HTTP specifics only, -75%)
- `websocket.py`: 335 lines (WebSocket specifics only, -39%)
- **Total**: 1082 lines, **no duplication**

## Data Models

Type-safe models for aria2 responses:

```python
# Example: DownloadStatus model
class DownloadStatus(RPCResponse):
    @property
    def gid(self) -> str:
        return self._data.get("gid", "")

    @property
    def status(self) -> str:
        return self._data.get("status", "")

    @property
    def total_length(self) -> int:
        return int(self._data.get("totalLength", 0))

    @property
    def completed_length(self) -> int:
        return int(self._data.get("completedLength", 0))

    @property
    def download_speed(self) -> int:
        return int(self._data.get("downloadSpeed", 0))
```

**Benefits**:
- Type hints for IDE autocomplete
- Property-based access (clean API)
- Automatic type conversion
- Validation and defaults

## Exception Hierarchy

```
Aria2Error (base exception)
├── Aria2ConnectionError    # Connection issues
├── Aria2TimeoutError        # Request timeout
├── Aria2AuthenticationError # Auth failed
└── Aria2RPCError           # RPC error response
    ├── code: int           # Error code from aria2
    └── message: str        # Error message
```

## WebSocket Event System

The WebSocket client implements an event-driven architecture:

```python
class WebSocketRPCClient(BaseRPCClient):
    def __init__(self):
        self._event_handlers: dict[Aria2Event, list[EventCallback]] = {}
        self._pending_requests: dict[str, asyncio.Future] = {}
        # ...

    async def _listen_loop(self):
        """Background task that listens for messages"""
        while True:
            message = await self._ws.recv()
            data = json.loads(message)

            if "id" in data:
                # RPC response
                self._handle_response(data)
            elif "method" in data:
                # Event notification
                await self._handle_event(data["method"], data["params"])

    async def _handle_event(self, method: str, params: list):
        """Dispatch event to registered handlers"""
        event = self._map_to_event(method)
        if event in self._event_handlers:
            for callback in self._event_handlers[event]:
                await callback(params[0])
```

**Key Features**:
- Non-blocking event handling
- Multiple handlers per event
- Async callback support
- Automatic event dispatching

## Connection Management

### HTTPRPCClient

Simple request-response model:

```python
async def _call(self, method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or []
    }
    response = await self.client.post(self.url, json=payload)
    return response.json()["result"]
```

### WebSocketRPCClient

Complex connection management:

1. **Connection**: Establishes WebSocket connection
2. **Listener Loop**: Background task receiving messages
3. **Heartbeat Loop**: Keep-alive messages
4. **Auto-reconnection**: Reconnect on connection loss
5. **Request-Response**: Async request/response handling

```python
async def connect(self):
    self._ws = await websockets.connect(self.url)
    self._listener_task = asyncio.create_task(self._listen_loop())
    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
```

## Testing Architecture

### Test Organization

```
tests/
├── test_aria2_client.py          # Unit tests (mocked)
├── test_download_manager.py      # Unit tests
├── test_websocket_client.py      # Integration tests
└── test_websocket_complete.py    # Integration tests
```

**Test Markers**:
- `@pytest.mark.integration` - Requires aria2c
- No marker - Unit tests (fast, mocked)

### Test Infrastructure

```
scripts/run_tests.py (Python)
    ├── Manages aria2c lifecycle
    ├── Runs unit or integration tests
    └── Generates coverage reports

mise tasks (mise.toml)
    ├── test:unit          # Fast unit tests
    ├── test:integration   # Integration tests
    └── test:coverage      # With coverage
```

## Future Extensions

### Adding New Protocol

To add a new protocol (e.g., XML-RPC):

```python
from aria2rpc import BaseRPCClient

class XMLRPCClient(BaseRPCClient):
    async def _call(self, method, params=None):
        # Implement XML-RPC protocol
        xml_payload = build_xml_request(method, params)
        response = await send_xml(xml_payload)
        return parse_xml_response(response)

# Automatically has all 21+ RPC methods!
```

### Adding New RPC Method

To add a new RPC method from aria2:

```python
# Only modify base.py
class BaseRPCClient(ABC):
    async def new_method(self, param):
        """New aria2 RPC method"""
        return await self._call("aria2.newMethod", [param])

# HTTPRPCClient and WebSocketRPCClient automatically get it!
```

## Design Decisions

### Why Async?

- aria2 operations are I/O-bound
- WebSocket requires async for event handling
- Textual framework is async-based
- Better concurrency for multiple downloads

### Why Abstract Base Class?

- Enforces protocol implementation
- Enables code reuse
- Maintains consistent API
- Type checking support

### Why Separate Package?

- aria2rpc is standalone (can be published to PyPI)
- Clear separation of concerns
- Can be used by other projects
- Independent testing and versioning

## See Also

- [Testing Guide](../testing.md) - Test architecture details
- [WebSocket Guide](../websocket.md) - WebSocket implementation
- [BitTorrent Guide](../bittorrent-metalink.md) - Advanced features
