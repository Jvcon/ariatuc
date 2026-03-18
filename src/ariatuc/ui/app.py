"""Main Textual application class."""

from __future__ import annotations

from pathlib import Path

from textual import events
from textual.app import App

from ariatuc.core.service import Aria2Service
from ariatuc.ui.keybinding_manager import KeybindingManager
from ariatuc.ui.screens.main_screen import MainScreen
from ariatuc.ui.themes import DEFAULT_THEME


class AriatucApp(App):
    """Aria2c TUI Application.

    Main application class that initializes the Aria2Service and displays
    the MainScreen.

    Attributes:
        service: Aria2Service instance for managing aria2 connections
    """

    TITLE = "ariatuc - Aria2c TUI"

    # Apply Dracula theme with explicit CSS variables
    CSS = (
        """
/* ===== Dracula Theme Color Variables ===== */
$primary: #bd93f9;      /* Purple - main UI elements */
$accent: #ff79c6;       /* Pink - focus/active states */
$secondary: #8be9fd;    /* Cyan - secondary highlights */
$background: #282a36;   /* Dark background */
$surface: #44475a;      /* Panels and surfaces */
$panel: #282a36;        /* Dialog backgrounds */
$boost: #44475a;        /* Hover/focus backgrounds */
$foreground: #f8f8f2;   /* Main text color */
$text: #f8f8f2;         /* Text alias */
$success: #50fa7b;      /* Green - success states */
$error: #ff5555;        /* Red - error states */
$warning: #ffb86c;      /* Orange - warning states */

Screen {
    background: $background;
}
"""
        + DEFAULT_THEME.component_overrides
    )

    def __init__(
        self,
        config_dir: Path | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize application.

        Args:
            config_dir: Optional custom config directory path
            *args: Additional positional arguments for App
            **kwargs: Additional keyword arguments for App
        """
        super().__init__(*args, **kwargs)
        self.service = Aria2Service(config_dir=config_dir)
        self.keybinding_manager = KeybindingManager()
        self._main_screen: MainScreen | None = None

    async def on_mount(self) -> None:
        """Initialize the application after mounting."""
        # Initialize the service
        await self.service.initialize()

        # Auto-connect to the configured server (if any)
        if self.service.current_server:
            try:
                await self.service.connect()
                # Initial refresh to populate download list
                await self.service.refresh_downloads()
            except Exception as e:
                # Log error but continue - user can connect manually later
                # TODO: Show connection error dialog with details from e
                _ = e  # Keep for future error dialog implementation
                pass

        # Create and push main screen
        self._main_screen = MainScreen(self.service, self.keybinding_manager)
        await self.push_screen(self._main_screen)

    async def on_unmount(self) -> None:
        """Cleanup before exiting."""
        # Shutdown service gracefully
        await self.service.shutdown()

    def on_key(self, event: events.Key) -> None:
        """Handle global key presses through keybinding manager.

        This provides centralized key handling at the app level for global
        shortcuts. Individual screens/widgets can still handle their own keys.

        Args:
            event: The key event
        """
        # Let keybinding manager try to resolve global shortcuts
        result = self.keybinding_manager.resolve(event.key)
        if result:
            action_name, _ = result
            # Global actions handled here (q for quit, ? for help, etc.)
            # Most actions will be handled by individual screens
            if action_name == "quit":
                self.exit()
                event.prevent_default()
            elif action_name == "help":
                # TODO: Show help screen
                event.prevent_default()
