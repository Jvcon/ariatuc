---
date: 2025-12-25
feature: "Unified Logging System"
files:
  - src/ariatuc/utils/logger.py
  - src/ariatuc/main.py
  - mise.toml
  - .gitignore
---

# Logging System

## Overview

ariatuc uses a unified logging system that provides:
- **File logging** with automatic rotation
- **Console logging** (optional, **disabled by default** to avoid overlaying TUI)
- **Environment variable configuration** for easy debugging
- **Structured log format** with timestamps, module names, and log levels
- **tmux integration** for convenient dual-pane development (TUI + live logs)

## Configuration

### Environment Variables

#### `ARIATUC_LOG_LEVEL`

Control the logging verbosity:

```bash
# Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
export ARIATUC_LOG_LEVEL=DEBUG
python -m ariatuc
```

**Default**: `INFO`

#### `ARIATUC_LOG_FILE`

Customize the log file path:

```bash
export ARIATUC_LOG_FILE=/path/to/custom/logfile.log
python -m ariatuc
```

**Default**: `logs/ariatuc.log` (relative to project root)

#### `ARIATUC_LOG_CONSOLE`

Control whether logs are printed to console (stderr):

```bash
# Enable console output (NOT recommended for TUI, will overlay on interface)
export ARIATUC_LOG_CONSOLE=true
python -m ariatuc

# Disable console output (recommended, default)
export ARIATUC_LOG_CONSOLE=false
python -m ariatuc
```

**Default**: `false` (logs only written to file)

**Note**: Console logging will overlay on the TUI interface. Use the dual-terminal workflow instead (see below).

### Log Rotation

Log files are automatically rotated to prevent excessive disk usage:
- **Maximum file size**: 10 MB
- **Backup count**: 7 files
- **Naming pattern**: `ariatuc.log`, `ariatuc.log.1`, `ariatuc.log.2`, etc.

## Recommended Workflows

### 1. Dual-Terminal Workflow with tmux (Recommended)

The best way to use ariatuc is with a split terminal setup:

```bash
# Automatically split terminal: TUI on top, logs on bottom
mise run dev:watch
```

This command:
- Creates a tmux session with split panes
- Runs ariatuc in the top pane
- Shows live logs (`tail -f`) in the bottom pane
- Logs are written to file only (no overlay on TUI)

**Requirements**: `tmux` must be installed
```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt install tmux

# Arch Linux
sudo pacman -S tmux
```

**tmux Quick Keys**:
- `Ctrl+b` then `↑`/`↓` - Switch between panes
- `Ctrl+b` then `d` - Detach from session
- `tmux attach -t ariatuc` - Reattach to session
- `Ctrl+b` then `x` - Kill pane
- `Ctrl+b` then `[` - Enter scroll mode (use arrow keys, press `q` to exit)

### 2. Manual Two-Terminal Workflow

If you don't have tmux, use two separate terminal windows:

**Terminal 1 (Application)**:
```bash
cd /path/to/ariatuc
mise run dev           # Normal logging
# or
mise run dev:debug     # Debug logging
```

**Terminal 2 (Log Viewer)**:
```bash
cd /path/to/ariatuc
mise run logs:tail     # Live log streaming
```

### 3. Console Logging (Not Recommended)

If you really want logs on the same terminal as TUI:

```bash
mise run dev:console
```

⚠️ **Warning**: Logs will overlay on the TUI interface, making it hard to use.

## Using Logs in Development

### Mise Tasks

#### Application Tasks

```bash
# Normal start (INFO level, logs to file only)
mise run dev

# Debug mode (DEBUG level, logs to file only)
mise run dev:debug

# With console output (logs overlay on TUI, not recommended)
mise run dev:console

# Split terminal mode (TUI + live logs, requires tmux)
mise run dev:watch
```

#### Log Viewing Tasks

```bash
# View complete log file
mise run logs

# Follow logs in real-time (like tail -f)
mise run logs:tail

# View last 100 lines
mise run logs:tail:n

# Clean up all log files
mise run logs:clean
```

### Manual Commands

```bash
# View logs
cat logs/ariatuc.log

# Follow logs in real-time
tail -f logs/ariatuc.log

# View last N lines
tail -n 50 logs/ariatuc.log

# Search logs for specific patterns
grep "ERROR" logs/ariatuc.log
grep "download" logs/ariatuc.log

# Clean logs
rm -rf logs/*.log*
```

## Log Format

Logs follow this format:

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**Example**:
```
2025-12-25 10:30:45 - ariatuc.core.service - INFO - Service initialized successfully
2025-12-25 10:30:46 - ariatuc.ui.widgets.download_list - DEBUG - get_selected_download_gid: cursor_row=0, row_count=5, keys_count=5
2025-12-25 10:30:46 - ariatuc.ui.widgets.download_detail - DEBUG - show_download called with gid: abc123def456
```

Components:
- **Timestamp**: `2025-12-25 10:30:45`
- **Module**: `ariatuc.core.service`
- **Level**: `INFO`, `DEBUG`, `WARNING`, `ERROR`, `CRITICAL`
- **Message**: Human-readable log message

## Debugging Common Issues

### 1. Download Overview Not Showing Selection

**Problem**: Pressing Enter doesn't show download details.

**Debug Steps**:

**Option 1: Using tmux (recommended)**
```bash
# Start with split terminal
ARIATUC_LOG_LEVEL=DEBUG mise run dev:watch

# Press Ctrl+b then ↓ to view logs pane
# Look for debug messages while using the app
```

**Option 2: Manual two terminals**
```bash
# Terminal 1: Run with DEBUG logging
mise run dev:debug

# Terminal 2: Follow logs
mise run logs:tail

# Look for these messages:
# - "get_selected_download_gid: returning gid=..."
# - "show_download called with gid: ..."
# - "refresh_details: updating overview for download ..."
```

**Common causes**:
- No download selected (cursor_row is None)
- Preview mode not activated (press Enter to toggle)
- GID extraction failed (check RowKey handling)

### 2. RPC Connection Issues

**Problem**: Application can't connect to aria2c.

**Debug Steps**:
```bash
# Start with debug mode and log viewer
ARIATUC_LOG_LEVEL=DEBUG mise run dev:watch

# Or in separate terminals:
# Terminal 1
mise run dev:debug

# Terminal 2: Check logs for connection errors
mise run logs | grep "Connection"
mise run logs | grep "ERROR"
```

**Look for**:
- "Failed to connect: ..."
- "Connection error: ..."
- "RPC error: ..."

### 3. Performance Issues

**Problem**: Application feels slow or unresponsive.

**Debug Steps**:
```bash
# Enable DEBUG logging to see timing information
ARIATUC_LOG_LEVEL=DEBUG mise run dev:watch

# Or monitor refresh operations in separate terminal:
mise run logs:tail | grep "refresh"
```

## Adding Logging to New Code

When adding new features, use the logger like this:

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Detailed debug information")
    logger.info("General informational message")
    logger.warning("Warning: something might be wrong")
    logger.error("Error: operation failed")
    logger.critical("Critical: system is in bad state")
```

**Best Practices**:
- Use `logger.debug()` for detailed diagnostic information
- Use `logger.info()` for high-level progress messages
- Use `logger.warning()` for recoverable issues
- Use `logger.error()` for errors that require attention
- Use `logger.critical()` for severe errors that may cause shutdown

## Implementation Details

### Architecture

```
ariatuc/
├── utils/
│   └── logger.py          # Logging configuration module
├── main.py                # Calls setup_logging() at startup
└── logs/                  # Log files (gitignored)
    ├── ariatuc.log
    ├── ariatuc.log.1
    ├── ariatuc.log.2
    └── ...
```

### Initialization Flow

1. `main.py` calls `setup_logging()` before creating the app
2. `logger.py` reads environment variables:
   - `ARIATUC_LOG_LEVEL` (default: INFO)
   - `ARIATUC_LOG_FILE` (default: logs/ariatuc.log)
3. Creates log directory if needed
4. Configures root logger with:
   - RotatingFileHandler (10MB max, 7 backups)
   - StreamHandler (stderr, optional)
5. All modules use `logging.getLogger(__name__)` to get configured loggers

### File Handler Configuration

```python
RotatingFileHandler(
    filename="logs/ariatuc.log",
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=7,               # Keep 7 backups
    encoding="utf-8"
)
```

### Console Handler Configuration

```python
StreamHandler(sys.stderr)  # Output to stderr
```

## Troubleshooting

### No Log File Created

**Problem**: Log file doesn't exist after running the app.

**Solution**:
1. Check if `logs/` directory was created
2. Verify file permissions
3. Check for errors during logger initialization

### Logs Not Showing Debug Messages

**Problem**: DEBUG messages aren't visible.

**Solution**:
```bash
# Ensure DEBUG level is set
export ARIATUC_LOG_LEVEL=DEBUG
mise run dev
```

### Log Files Growing Too Large

**Problem**: Log files consuming too much disk space.

**Solution**:
```bash
# Clean old logs
mise run logs:clean

# Or adjust rotation settings in logger.py:
# MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
# BACKUP_COUNT = 3                # Keep 3 backups
```

## Related Files

- `src/ariatuc/utils/logger.py` - Logger configuration module (src/ariatuc/utils/logger.py:1)
- `src/ariatuc/main.py` - Application entry point with logger initialization (src/ariatuc/main.py:11)
- `mise.toml` - Task definitions for log management (mise.toml:61-65)
- `.gitignore` - Excludes logs/ directory from git (. gitignore:119)
