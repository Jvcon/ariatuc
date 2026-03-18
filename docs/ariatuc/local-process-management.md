---
date: 2026-02-04
feature: "Local aria2c Process Management User Guide"
files:
  - src/ariatuc/core/local_process_manager.py
  - src/ariatuc/ui/screens/server_management_screen.py
  - src/ariatuc/ui/widgets/status_bar.py
---

# Local aria2c Process Management

## Overview

Ariatuc provides comprehensive local aria2c process management capabilities, allowing you to control aria2c daemon processes directly from the TUI. This guide covers all aspects of local process management, from basic operations to advanced configuration.

## Core Capabilities

### Process Control

- **Start** - Launch aria2c daemon with configured options
- **Stop** - Gracefully shutdown with automatic session saving
- **Restart** - Stop and start in one operation
- **Session Management** - Manual and automatic session persistence

### Visual Indicators

The TUI provides clear visual feedback for process status:

**In Server List:**

```text
● local-server                    ← Current server (●)
  [HTTP|✓] localhost:6800 [PROC:▶]  ← Connected (✓), Process Running (▶)

  remote-server
  [WS|○] example.com:6800           ← Not connected (○), No process indicator
```

**In Status Bar:**

```text
Server: local-server (🟢 ws) [▶] | 3 Active | 2 Waiting | ...
                             ↑
                    Process running
```

**Process Status Indicators:**

| Indicator | Status | Description |
|-----------|--------|-------------|
| `[PROC:▶]` | Running | Process is active and healthy |
| `[PROC:■]` | Stopped | Process is not running |
| `[PROC:⋯]` | Starting | Process is initializing |
| `[PROC:✗]` | Error | Process encountered an error |
| _(none)_ | Remote | Not a local server (no process control) |

## Keyboard Shortcuts

All process management operations are accessible through keyboard shortcuts in the Server Management screen.

### Accessing Server Management

From the main screen, press `M` to open the Server Management screen.

### Available Operations

| Key | Action | Description |
|-----|--------|-------------|
| `s` | **Start Process** | Start local aria2c process |
| `t` | **Stop Process** | Stop local process (saves session) |
| `r` | **Restart Process** | Restart local process |
| `Ctrl+S` | **Save Session** | Manually save session file |

## Usage Tutorials

### Starting a Local Process

**Use Case:** Launch a local aria2c daemon to begin downloading.

**Steps:**

1. Press `M` to open Server Management
2. Navigate to your local server using arrow keys or `j`/`k`
3. Press `s` to start the process
4. Watch the status indicator change:
   - `[PROC:■]` (stopped) → `[PROC:⋯]` (starting) → `[PROC:▶]` (running)
5. Press `Esc` to return to the main screen
6. Downloads are now ready to be added!

**Behind the Scenes:**

- aria2c starts with your configured options
- Existing session file is loaded (if available)
- RPC server starts on configured port
- Previous downloads are automatically restored

### Stopping Gracefully

**Use Case:** Stop aria2c while preserving all download state.

**Steps:**

1. Press `M` to open Server Management
2. Navigate to the running local server
3. Press `t` to stop
4. Automatic operations:
   - Current session is saved
   - aria2c receives graceful shutdown signal
   - UI waits for clean exit
   - Success message is displayed
5. Your download state is safely preserved

**Session File Location:**

```text
~/.config/ariatuc/sessions/<server-name>.session
```

### Restarting a Process

**Use Case:** aria2c is unresponsive or you need to apply configuration changes.

**Steps:**

1. Press `M` to open Server Management
2. Navigate to the local server (any state)
3. Press `r` to restart
4. Watch the process cycle:
   - Stopping... → Stopped → Starting... → Running
5. All downloads resume automatically

**Ideal For:**

- Recovering from hung connections
- Applying new configuration settings
- Clearing stale network connections
- General troubleshooting

### Manual Session Save

**Use Case:** Create a backup before making risky changes or testing.

**Steps:**

1. From any screen, press `M` to open Server Management
2. Press `Ctrl+S`
3. See confirmation: `✓ Session saved successfully`
4. Current download state is now saved to disk

**Alternative: Auto-Save**

Ariatuc automatically saves your session every 5 minutes (configurable), so manual saves are typically only needed before risky operations.

## Common Workflows

### Daily Usage Pattern

**Morning Routine:**

1. Open ariatuc
2. Press `M` → `s` to start local aria2c
3. Add downloads and work normally

**Evening Routine:**

1. Press `M` → `t` to stop gracefully
2. Exit ariatuc
3. Downloads are automatically saved and will resume tomorrow

### Multi-Server Setup

Manage both local and remote servers simultaneously:

```text
Local development server:
  local-dev [PROC:▶]      ← Running locally for testing

Production server:
  remote-prod [WS|✓]      ← Connected to remote server

Switch between servers with Space key!
```

### Emergency Recovery

**Problem:** aria2c has crashed or become unresponsive

**Solution:**

1. Press `M` to open Server Management
2. Navigate to the problematic server
3. Press `r` to restart
4. Downloads resume within ~2 seconds

## Configuration

### Server Configuration

Local servers require `is_local: true` in the server configuration:

```json
{
  "name": "my-local-server",
  "url": "http://localhost:6800/jsonrpc",
  "is_local": true,
  "session_file": "~/.config/ariatuc/sessions/my-local-server.session"
}
```

### Custom Session File Location

Override the default session file path:

```json
{
  "name": "my-server",
  "url": "http://localhost:6800/jsonrpc",
  "is_local": true,
  "session_file": "/path/to/custom/location.session"
}
```

### Custom aria2c Options

Configure startup options for the local process:

```json
{
  "aria2c_options": {
    "max-concurrent-downloads": 10,
    "max-connection-per-server": 8,
    "split": 16,
    "min-split-size": "10M"
  }
}
```

### Auto-Save Interval

Adjust the automatic session save interval (in seconds):

```json
{
  "auto_save_session_interval": 300  // 5 minutes (default)
}
```

Set to `null` to disable auto-save:

```json
{
  "auto_save_session_interval": null  // Disable auto-save
}
```

## Troubleshooting

### "Process already running"

**Cause:** Attempted to start a process that is already running

**Solution:** Check the status indicator - it should show `[PROC:▶]`. If the process is truly running, no action is needed.

### "Process not running"

**Cause:** Attempted to stop a process that is already stopped

**Solution:** Check the status indicator. If it shows `[PROC:■]`, press `s` to start the process.

### "Not a local server"

**Cause:** Attempted process operations on a remote server

**Solution:** Process management operations only work for servers with `is_local: true` in their configuration.

### Process Won't Start

**Possible Causes:**

1. **Port already in use**
   - Solution: Change the port in your server configuration
   - Check: `lsof -i :<port>` to see what's using the port

2. **aria2c not in PATH**
   - Solution: Set `aria2c_path` in your configuration
   - Example: `"aria2c_path": "/usr/local/bin/aria2c"`

3. **Corrupted session file**
   - Solution: Delete the session file and restart
   - Location: `~/.config/ariatuc/sessions/<server-name>.session`

### Downloads Not Restored

**Checklist:**

1. Verify session file exists:
   ```bash
   ls ~/.config/ariatuc/sessions/<server-name>.session
   ```

2. Check that session was saved before stop (automatic)

3. Verify `--input-file` option is configured (automatic in ariatuc)

4. Review aria2c logs for errors loading the session file

## Best Practices

### Recommended Actions

- **Always use graceful stop** (`t` key) instead of killing the process
- **Save manually** before risky operations (testing, configuration changes)
- **Monitor status indicators** to stay aware of process state
- **Check logs** when something seems wrong
- **Restart** if aria2c becomes unresponsive

### Actions to Avoid

- **Don't use `kill -9`** on the aria2c process (use UI stop instead)
- **Don't edit session files** while aria2c is running
- **Don't start multiple instances** on the same port
- **Don't ignore error status** (`[PROC:✗]`)

## Advanced Topics

### Session File Format

Session files store download metadata in aria2c's native format:

```text
# Example session file
http://example.com/file1.zip
  gid=abc123
  dir=/downloads
  out=file1.zip
  ...

http://example.com/file2.zip
  gid=def456
  dir=/downloads
  ...
```

**Note:** Session files are managed automatically by ariatuc. Manual editing is not recommended.

### Process Lifecycle

Understanding the process lifecycle helps with troubleshooting:

1. **Stopped** (`[PROC:■]`)
   - No aria2c process running
   - Press `s` to start

2. **Starting** (`[PROC:⋯]`)
   - aria2c process is initializing
   - RPC server is starting
   - Session file is being loaded
   - Wait for transition to Running

3. **Running** (`[PROC:▶]`)
   - Process is healthy and active
   - RPC server is accepting connections
   - Downloads can be managed normally

4. **Error** (`[PROC:✗]`)
   - Process encountered a fatal error
   - Check logs for details
   - Try restarting with `r`

### Integration with Existing Features

Local process management works seamlessly with:

- **Server switching** - Auto-start on connect (if configured)
- **Download operations** - Session preserved across restarts
- **Configuration management** - Process settings saved with server config
- **Event notifications** - Process state changes trigger UI updates
- **Auto-refresh** - Process status updates in real-time
- **Multiple servers** - Mix local and remote servers freely

## Summary

Local aria2c process management in ariatuc provides:

- **Fast** - Start/stop operations complete in seconds
- **Safe** - Automatic session saving prevents data loss
- **Visible** - Clear status indicators throughout the UI
- **Convenient** - One-key operations for common tasks
- **Reliable** - Graceful handling of all process lifecycle events

**Get started now:** Press `M`, select a local server, and press `s` to start managing your downloads!

## See Also

- [Server Management Guide](./server-management.md) - General server configuration
- [Configuration Reference](./configuration-reference.md) - Detailed config options
- [Architecture: Local Process Manager](./architecture/local-process-manager.md) - Technical implementation details
