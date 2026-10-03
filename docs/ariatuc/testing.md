# Server Management Testing Guide

This guide explains how to test the server management functionality, including HTTP and WebSocket connections.

## Prerequisites

### 1. Install aria2c

```bash
# macOS
brew install aria2

# Ubuntu/Debian
sudo apt install aria2
```

### 2. Start aria2c with RPC enabled

```bash
# Basic RPC (HTTP + WebSocket on same port)
aria2c --enable-rpc

# With custom port
aria2c --enable-rpc --rpc-listen-port=6800

# With secret token (recommended for security)
aria2c --enable-rpc --rpc-secret=mysecrettoken
```

**Important**: By default, aria2c's RPC server supports **both** HTTP and WebSocket on the same URL:
- HTTP: `http://localhost:6800/jsonrpc`
- WebSocket: `ws://localhost:6800/jsonrpc`

## Testing Connections

### Manual Test Script

We provide a test script to verify both HTTP and WebSocket connections:

```bash
# Test HTTP connection (default)
python tests/manual_test_connections.py

# Test WebSocket connection
python tests/manual_test_connections.py --websocket

# With secret token
python tests/manual_test_connections.py --secret mysecrettoken
python tests/manual_test_connections.py --websocket --secret mysecrettoken

# Custom URL
python tests/manual_test_connections.py --url http://192.168.1.100:6800/jsonrpc
python tests/manual_test_connections.py --websocket --url ws://192.168.1.100:6800/jsonrpc
```

### Expected Output

**HTTP Connection:**
```
============================================================
Testing HTTP Connection
URL: http://localhost:6800/jsonrpc
Secret: None
============================================================

✓ HTTP client created
→ Testing get_version()...
✓ Connected! aria2 version: 1.37.0
  Enabled features: Async DNS, BitTorrent, Firefox3 Cookie, ...

→ Testing get_global_stat()...
✓ Global stats retrieved:
  Download speed: 0 B/s
  Upload speed: 0 B/s
  Active downloads: 0

============================================================
✅ HTTP Connection Test PASSED
============================================================
```

**WebSocket Connection:**
```
============================================================
Testing WebSocket Connection
URL: ws://localhost:6800/jsonrpc
Secret: None
============================================================

✓ WebSocket client created
→ Connecting to WebSocket...
✓ WebSocket connected
→ Testing get_version()...
✓ RPC call successful! aria2 version: 1.37.0
  Enabled features: Async DNS, BitTorrent, Firefox3 Cookie, ...

→ Testing get_global_stat()...
✓ Global stats retrieved:
  Download speed: 0 B/s
  Upload speed: 0 B/s
  Active downloads: 0

→ Disconnecting...
✓ Disconnected cleanly

============================================================
✅ WebSocket Connection Test PASSED
============================================================
```

## Using Server Management in ariatuc

### 1. Launch ariatuc

```bash
poetry run ariatuc
```

### 2. Open Server Management

Press `s` to open the Server Management screen.

### 3. Add a Server

Press `a` to add a new server. The interface operates in two modes:

**VIEW Mode** (default):
- Use `j`/`k` to scroll through fields and see what's available
- Press `i` when ready to edit

**EDIT Mode** (field editing):
1. Press `i` to enter EDIT mode (focuses on first field)
2. Type to edit the current field
3. Press `Tab` to move to next field
4. Press `Esc` to return to VIEW mode when done

Configure the following:
- **Name**: Friendly name (e.g., "Local HTTP", "Remote WS")
- **RPC URL**:
  - HTTP: `http://localhost:6800/jsonrpc`
  - WebSocket: `ws://localhost:6800/jsonrpc`
- **Protocol**: Select "Auto Detect" (recommended)
- **Secret**: Enter your RPC secret if configured

### 4. Test Connection

In VIEW mode:
1. Use `t`/`T` to cycle through servers (works globally, no need to focus on list)
2. Press `Enter` to test connection to selected server
3. Check the command bar for results:
   - ✓ Success: Shows protocol type and aria2 version
   - ✗ Failure: Shows error message

### 5. Switch Server

In VIEW mode:
1. Use `t`/`T` to select desired server
2. Press `Space` to set as current server
3. The app will:
   - Disconnect from old server
   - Connect to new server
   - Update the current indicator (●)

### 6. Save Configuration

In VIEW mode, press `w` to save server configurations permanently.

## Keyboard Shortcuts

This screen uses a unified interaction model with Aria2 Settings, featuring **VIEW** and **EDIT** modes.

### VIEW Mode (Default)

Navigation keys work **globally** regardless of focus position:

| Key | Action |
|-----|--------|
| `t` / `T` | Cycle through servers (next/previous) |
| `j` / `k` | Navigate form fields (scroll only, no focus) |
| `i` | Enter EDIT mode (focus on first field) |
| `a` | Add new server |
| `d` | Delete selected server |
| `r` | Rename server |
| `w` | Save configuration |
| `Enter` | Test connection |
| `Space` | Set as current server |
| `Esc` | Close screen |
| `q` | Quit |

### EDIT Mode (Field Focused)

When a form field is focused:

| Key | Action |
|-----|--------|
| `Esc` | Exit EDIT mode (return to VIEW) |
| `Tab` | Navigate between fields |
| Type | Edit field content |

## Troubleshooting

### Connection Timeout

**Problem**: Test connection times out

**Solutions**:
1. Verify aria2c is running: `ps aux | grep aria2c`
2. Check if RPC is enabled: `aria2c --enable-rpc`
3. Verify port is correct (default: 6800)
4. Check firewall settings

### WebSocket Connection Failed

**Problem**: HTTP works but WebSocket fails

**Solutions**:
1. Ensure URL starts with `ws://` (not `http://`)
2. Verify aria2c version supports WebSocket (1.34.0+)
3. Check if reverse proxy is interfering (nginx, apache)

### Authentication Failed

**Problem**: Connection rejected with authentication error

**Solutions**:
1. Verify secret token matches aria2c configuration
2. Check aria2c was started with `--rpc-secret=yourtoken`
3. Leave username/password empty (deprecated auth method)

### Protocol Detection

The `Aria2Client` factory automatically detects protocol from URL:
- `ws://` or `wss://` → WebSocket
- `http://` or `https://` → HTTP

No manual protocol selection needed in most cases.

## Development Notes

### Protocol Implementation

- **HTTP**: Uses `HTTPRPCClient` - stateless request/response
- **WebSocket**: Uses `WebSocketRPCClient` - persistent connection with events

### Connection Testing

The test connection feature (`Enter` key) creates a temporary client:
1. Creates client based on URL protocol
2. For WebSocket: explicitly connects
3. Calls `get_version()` to verify RPC
4. For WebSocket: cleanly disconnects
5. Shows result in command bar

### Server Switching

The switch server feature (`Space` key):
1. Updates `is_current` flag in server list
2. Adds/updates server in `RPCManager`
3. Calls `switch_server()` to set as current
4. Disconnects from old server
5. Connects to new server
6. Refreshes UI to show current indicator (●)

## Best Practices

1. **Use WebSocket for Production**: Better performance with real-time events
2. **Always Set Secret**: Use `--rpc-secret` for security
3. **Test Before Switching**: Press `Enter` to test before setting as current
4. **Save Configuration**: Press `w` after adding/modifying servers
5. **Monitor Command Bar**: Watch for success/error messages

## See Also

- [aria2 RPC Documentation](https://aria2.github.io/manual/en/html/aria2c.html#rpc-interface)
- [aria2rpc Library](../docs/aria2rpc/)
- [ariatuc Development](../docs/ariatuc/)
