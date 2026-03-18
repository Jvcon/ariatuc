# ariatuc

**Aria2c TUI** - A Terminal User Interface for aria2c download manager

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A feature-rich, keyboard-driven terminal interface for managing aria2c downloads, inspired by lazygit's UX principles and providing functionality equivalent to the AriaNg web frontend.

## Features

- 🚀 **Fast & Lightweight** - Built with Python and Textual
- ⌨️ **Keyboard-Driven** - Vim-style navigation and shortcuts
- 📊 **Real-time Updates** - WebSocket support for instant status updates
- 🔄 **Multiple Servers** - Manage multiple aria2 RPC servers
- 📦 **Protocol Support** - HTTP, FTP, BitTorrent, and Metalink downloads
- ⚙️ **Full Configuration** - Global and per-download settings
- 🎨 **Rich UI** - Progress bars, color coding, and statistics

## Quick Start

### 1. Install aria2c

```bash
# macOS
brew install aria2

# Ubuntu/Debian
sudo apt install aria2
```

### 2. Start aria2c with RPC

```bash
aria2c --enable-rpc
```

### 3. Install ariatuc

```bash
git clone https://github.com/Jvcon/ariatuc.git
cd ariatuc
poetry install
poetry run ariatuc
```

## Documentation

📖 **[Full Documentation](docs/)** - Comprehensive guides and references

### For Users
- [Quick Start Guide](docs/quick-start.md) - Get started in 5 minutes
- [Installation Guide](docs/installation.md) - Detailed installation instructions

### For Developers
- [Development Guide](docs/development.md) - Toolchain setup (Ruff, Mypy, Pytest)
- [aria2rpc Library](docs/aria2rpc/) - RPC client library documentation
- [ariatuc Development](docs/ariatuc/) - TUI application development

## Development

### Running Tests

```bash
# Run unit tests (fast)
mise run test:unit

# Run all tests
mise run test

# With coverage
mise run test:coverage
```

See [Testing Guide](docs/aria2rpc/testing.md) for details.

### Project Status

- **aria2rpc**: 95% complete - Standalone RPC client library
- **download_manager**: 95% complete - State management
- **ariatuc CLI**: 25% complete - TUI interface
- **Overall**: 67% complete

See [TODO.md](TODO.md) for detailed roadmap.

## Contributing

Contributions are welcome! Please see our documentation:

- [Development Guide](docs/development.md) - Setup toolchain (Ruff, Mypy, Pytest)
- [aria2rpc Development](docs/aria2rpc/) - RPC library (95% complete)
- [ariatuc Development](docs/ariatuc/development.md) - TUI application (25% complete)
- [Testing Guide](docs/aria2rpc/testing.md) - Running tests

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [aria2](https://aria2.github.io/) - The download utility
- [Textual](https://textual.textualize.io/) - Python TUI framework
- [AriaNg](https://github.com/mayswind/AriaNg) - Feature reference
- [lazygit](https://github.com/jesseduffield/lazygit) - UX inspiration