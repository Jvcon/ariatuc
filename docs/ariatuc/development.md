# ariatuc Development Guide

Guide for contributing to the ariatuc TUI application.

## Overview

ariatuc is built with:
- **Textual** - Python TUI framework
- **aria2rpc** - RPC client library (see [aria2rpc docs](../aria2rpc/))
- **Python 3.11+** - Modern Python features

## Development Setup

### Prerequisites

```bash
# Install dependencies
poetry install --with dev

# Install aria2c
brew install aria2  # macOS
sudo apt install aria2  # Ubuntu
```

### Start aria2c

```bash
aria2c --enable-rpc
```

### Run ariatuc

```bash
poetry run ariatuc
```

## Project Structure

```
src/ariatuc/
├── main.py              # Entry point
├── ui/                  # UI components
│   ├── app.py           # Main Textual App
│   ├── screens/         # Screen classes
│   │   ├── main.py      # Main download screen
│   │   ├── settings.py  # Settings screen
│   │   └── add.py       # Add download dialog
│   └── widgets/         # Reusable widgets
│       ├── download_list.py
│       ├── status_bar.py
│       └── progress.py
├── core/                # Business logic
│   ├── download_manager.py  # Download state (95% done)
│   ├── rpc_manager.py       # Multi-server management
│   └── config.py            # Configuration
└── utils/               # Utilities
```

## Current Status

### Completed (25%)
- ✅ aria2rpc integration
- ✅ Download state management (download_manager.py)
- ✅ Project structure

### In Development
- 🔄 Main TUI interface
- 🔄 Download list widget
- 🔄 Basic keyboard navigation

### Planned
- ⏳ Settings screen
- ⏳ Add download dialog
- ⏳ Server management
- ⏳ Real-time updates via WebSocket

## Design Principles

### Textual Framework

ariatuc is built with [Textual](https://textual.textualize.io/), a modern Python TUI framework:

- **Reactive** - Automatic UI updates
- **Async** - Non-blocking operations
- **CSS styling** - Flexible layout and theming
- **Rich** - Beautiful terminal output

### Architecture

```
┌─────────────┐
│  Textual    │  UI Layer
│  App/Widgets│
└─────┬───────┘
      │
┌─────▼──────────┐
│ download_manager│  State Management
│ rpc_manager    │
└─────┬──────────┘
      │
┌─────▼──────┐
│  aria2rpc  │  RPC Communication
└────────────┘
```

### Key Concepts

1. **Screens** - Full-screen views (main, settings, dialogs)
2. **Widgets** - Reusable UI components (lists, progress bars)
3. **Reactive** - Auto-update UI when data changes
4. **Async** - All RPC calls are async

## Development Workflow

### 1. Create a New Widget

```python
# src/ariatuc/ui/widgets/my_widget.py
from textual.widget import Widget
from textual.reactive import reactive

class MyWidget(Widget):
    """Custom widget"""

    # Reactive attribute - UI updates automatically
    value = reactive(0)

    def render(self) -> str:
        return f"Value: {self.value}"
```

### 2. Create a New Screen

```python
# src/ariatuc/ui/screens/my_screen.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer

class MyScreen(Screen):
    """Custom screen"""

    def compose(self) -> ComposeResult:
        yield Header()
        yield MyWidget()
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted"""
        pass
```

### 3. Add to Main App

```python
# src/ariatuc/ui/app.py
from textual.app import App

class AriatucApp(App):
    SCREENS = {
        "main": MainScreen,
        "my": MyScreen,  # Add new screen
    }

    def on_mount(self) -> None:
        self.push_screen("main")
```

## Testing

### Unit Tests

```bash
# Test download manager
poetry run pytest tests/ariatuc/unit/test_download_manager.py
```

### TUI Testing

Textual provides testing utilities:

```python
import pytest
from ariatuc.ui.app import AriatucApp

@pytest.mark.asyncio
async def test_app():
    app = AriatucApp()
    async with app.run_test() as pilot:
        # Simulate key press
        await pilot.press("a")

        # Check if dialog appeared
        assert app.screen.query_one("#add-dialog").visible
```

## Keyboard Shortcuts

### Planned Shortcuts

| Key | Action |
|-----|--------|
| `a` | Add download |
| `d` | Delete download |
| `p` | Pause/unpause |
| `e` | Edit options |
| `r` | Refresh |
| `s` | Switch server |
| `g` | Settings |
| `j`/`k` or `↓`/`↑` | Navigate |
| `h`/`l` or `Tab` | Switch panel |
| `?` | Help |
| `q` | Quit |

## Styling

Textual uses CSS for styling:

```css
/* src/ariatuc/ui/app.tcss */
Screen {
    background: $surface;
}

DownloadList {
    border: solid $primary;
    height: 1fr;
}

.active {
    background: $success;
}

.paused {
    background: $warning;
}
```

## Contributing

### Before Starting

1. Check [TODO.md](../../TODO.md) for planned features
2. Open an issue to discuss large changes
3. Read [aria2rpc docs](../aria2rpc/) to understand the RPC layer

### Coding Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions focused
- Use async/await for I/O

### Pull Request Process

1. Fork repository
2. Create feature branch
3. Write tests for UI components
4. Ensure tests pass: `mise run test`
5. Update documentation
6. Submit PR

## Resources

- [Textual Documentation](https://textual.textualize.io/)
- [Textual Examples](https://github.com/Textualize/textual/tree/main/examples)
- [aria2rpc Documentation](../aria2rpc/)
- [lazygit](https://github.com/jesseduffield/lazygit) - UX inspiration

## Roadmap

See [TODO.md](../../TODO.md) for detailed feature roadmap.

High-level priorities:

1. **Phase 1** (Current) - Core TUI
   - Main download list screen
   - Basic keyboard navigation
   - Add download dialog

2. **Phase 2** - Enhanced Features
   - Settings screen
   - Multiple server support
   - Real-time updates (WebSocket)

3. **Phase 3** - Advanced Features
   - BitTorrent file selection
   - Statistics and charts
   - Theming support

## Support

- GitHub Issues: Bug reports
- GitHub Discussions: Questions
- Pull Requests: Contributions
