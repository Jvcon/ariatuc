# ariatuc - Terminal User Interface

A keyboard-driven terminal interface for managing aria2c downloads.

## Overview

ariatuc is a TUI application built with Textual that provides a rich, interactive interface for aria2c download manager. It's inspired by lazygit's UX and aims to provide feature parity with AriaNg web frontend.

**Status**: 25% complete (early development)

## Features

### Current
- 🚀 Fast & Lightweight TUI
- ⌨️ Keyboard-driven navigation
- 📊 Built on [aria2rpc](../aria2rpc/) library

### Planned
- 📋 Download list view
- ➕ Add download dialog
- ⚙️ Settings configuration
- 🔄 Multiple server management
- 📈 Real-time statistics
- 🎨 Rich progress indicators
- 🌓 Theme support

## Quick Start

See [Quick Start Guide](../quick-start.md) for getting started.

## Documentation

- **[User Guide](user-guide.md)** - Using ariatuc (coming soon)
- **[Development Guide](development.md)** - Contributing to ariatuc

## Installation

See [Installation Guide](../installation.md) for detailed instructions.

## Project Structure

```
src/ariatuc/
├── main.py           # Entry point
├── ui/               # Textual UI components
│   ├── app.py        # Main App class
│   ├── screens/      # Different screens
│   └── widgets/      # Reusable widgets
├── core/             # Business logic
│   ├── download_manager.py
│   ├── rpc_manager.py
│   └── config.py
└── utils/            # Utilities
```

## Design Goals

### Inspired by lazygit

- **Panel-based layout** - Multiple panels showing different information
- **Context-sensitive keys** - Different actions based on current focus
- **Vim-style navigation** - `j`/`k` for list navigation
- **Quick actions** - Single-key commands for common operations
- **Real-time updates** - Instant feedback on status changes

### Feature Parity with AriaNg

The TUI aims to provide equivalent functionality to AriaNg web frontend:

- Download management (add, pause, remove, etc.)
- Multiple server support
- Global and per-download settings
- BitTorrent-specific features
- Session management
- Statistics and monitoring

## Development Status

### Implemented (25%)
- ✅ RPC client integration ([aria2rpc](../aria2rpc/))
- ✅ Download state management
- ✅ Basic project structure

### In Progress (0%)
- 🔄 Main TUI interface
- 🔄 Download list widget
- 🔄 Add download dialog

### Planned (75%)
- ⏳ Settings screen
- ⏳ Multiple server management
- ⏳ Real-time status updates
- ⏳ Keyboard shortcuts system
- ⏳ Theme support
- ⏳ File selection for torrents
- ⏳ And more...

See [TODO.md](../../TODO.md) for detailed roadmap.

## Contributing

See [Development Guide](development.md) for:
- Setting up development environment
- Code architecture
- Contributing guidelines

## License

MIT License - see [LICENSE](../../LICENSE) file for details.
