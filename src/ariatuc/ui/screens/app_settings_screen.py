"""Application-level settings screen."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from ariatuc.ui.widgets.app_field_definitions import APP_FIELDS
from ariatuc.ui.widgets.command_bar import CommandBar
from ariatuc.ui.widgets.form_widget import FormWidget

if TYPE_CHECKING:
    from ariatuc.core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class AppSettingsScreen(ModalScreen[dict[str, Any] | None]):
    """Application settings screen.

    Features:
    - Single-column form layout (no sections)
    - VIEW/EDIT mode interaction (i/e/w/q/j/k)
    - Auto-save to ConfigManager

    Layout:
    ┌────────────────────────────────────────┐
    │ App Settings                           │ (Title bar)
    ├────────────────────────────────────────┤
    │ Theme:              [Dark      ▼]      │
    │ Refresh Interval:   [1000          ]   │
    │ Auto Refresh:       [Enabled    ▼]     │
    │ ...                                    │
    ├────────────────────────────────────────┤
    │ i-Edit | w-Save | q-Quit               │ (Command bar)
    └────────────────────────────────────────┘

    Keyboard shortcuts:
    VIEW Mode (default):
    - j/k: Navigate form fields (scroll only, no focus)
    - i: Enter EDIT mode (focus on first form field)
    - w: Save settings
    - Esc: Close screen
    - q: Quit screen

    EDIT Mode (when a field is focused):
    - Esc: Exit EDIT mode and return to VIEW mode
    - Tab: Navigate between fields (standard Textual behavior)
    - Type to edit field content

    Returns:
        None if cancelled, or dict with updated config
    """

    DEFAULT_CSS = """
    AppSettingsScreen {
        background: $surface;
    }

    /* Title bar matching other settings screens */
    #title {
        dock: top;
        height: 1;
        text-align: center;
        text-style: bold;
        background: $primary;
        color: $text;
        content-align: center middle;
        padding: 0 1;
    }

    /* Main form container */
    #form-container {
        height: 1fr;
        width: 100%;
        border: solid $primary;
        padding: 1 2;
    }

    /* Ensure FormWidget fills the container */
    #form-container > FormWidget {
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        ("i", "enter_edit_mode", "Edit"),
        ("escape", "handle_escape", ""),  # No hint - default behavior
        ("w", "save_settings", "Save"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        config_manager: ConfigManager,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize app settings screen.

        Args:
            config_manager: ConfigManager instance
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.config_manager = config_manager
        self._form_widget: FormWidget | None = None

        # VIEW/EDIT mode tracking
        self._mode = "VIEW"  # "VIEW" or "EDIT"
        self._current_field_index = 0  # Track current field in VIEW mode navigation

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        # Title bar at top
        yield Static("App Settings", id="title")

        # Form container
        with Vertical(id="form-container"):
            # Form will be added in on_mount
            pass

        # Command bar at bottom
        command_bar = CommandBar(id="command-bar")
        command_bar.update("i-Edit | w-Save | q-Quit")
        yield command_bar

    async def on_mount(self) -> None:
        """Load settings after mount."""
        logger.info("AppSettingsScreen.on_mount() called")

        # Get mounted container
        try:
            form_container = self.query_one("#form-container", Vertical)
        except Exception as e:
            logger.error(f"Failed to query form container: {e}")
            return

        # Load current config and convert to string dict for form
        config = self.config_manager.get()
        config_dict = {
            "theme": config.theme,
            "refresh_interval": str(config.refresh_interval),
            "auto_refresh": "true" if config.auto_refresh else "false",
            "connection_timeout": str(config.connection_timeout),
            "reconnect_interval": str(config.reconnect_interval),
            "prefer_websocket": "true" if config.prefer_websocket else "false",
            "websocket_fallback_http": "true" if config.websocket_fallback_http else "false",
            "max_concurrent_downloads": str(config.max_concurrent_downloads),
            "max_connection_per_server": str(config.max_connection_per_server),
            "enable_notifications": "true" if config.enable_notifications else "false",
            "play_sound_on_complete": "true" if config.play_sound_on_complete else "false",
            "play_sound_on_error": "true" if config.play_sound_on_error else "false",
        }

        # Create form widget
        self._form_widget = FormWidget(
            fields=APP_FIELDS,
            initial_values=config_dict,
            id="app-settings-form",
        )

        # Mount form
        await form_container.mount(self._form_widget)
        logger.info("App settings form mounted")

    def on_key(self, event) -> None:
        """Global keyboard event handler for unified navigation.

        Handles:
        - j/k: Navigate form fields (VIEW mode, global)
        - i: Enter EDIT mode
        - Esc: Exit EDIT mode or cancel
        """
        from textual import events
        from textual.widgets import Input, Select, TextArea

        if not isinstance(event, events.Key):
            return

        key = event.key

        # Check if we're in EDIT mode (any form field focused)
        focused = self.app.focused
        in_edit_mode = isinstance(focused, (Input, TextArea, Select))

        # Update mode state
        if in_edit_mode and self._mode == "VIEW":
            self._mode = "EDIT"
        elif not in_edit_mode and self._mode == "EDIT":
            self._mode = "VIEW"

        # In EDIT mode, only handle Esc
        if self._mode == "EDIT":
            if key == "escape":
                # Blur focused field and return to VIEW mode
                self.set_focus(None)
                self._mode = "VIEW"
                event.stop()  # Stop event propagation completely
                logger.info("Exited EDIT mode")
            return

        # VIEW mode: Handle global navigation keys
        if key == "j":
            # Next field in form (global)
            self._navigate_field(1)
            event.prevent_default()
        elif key == "k":
            # Previous field in form (global)
            self._navigate_field(-1)
            event.prevent_default()

    def _navigate_field(self, direction: int) -> None:
        """Navigate form fields in VIEW mode (highlight field for visual feedback).

        Args:
            direction: 1 for next, -1 for previous
        """
        if not self._form_widget:
            return

        # Get ordered list of field keys
        field_keys = self._form_widget.get_field_keys()
        if not field_keys:
            return

        # Update field index (wrap around)
        self._current_field_index = (self._current_field_index + direction) % len(field_keys)

        # Highlight the field at current index
        current_field_key = field_keys[self._current_field_index]
        self._form_widget.highlight_field(current_field_key)
        logger.debug(
            f"Navigated to field: {current_field_key} (index: {self._current_field_index})"
        )

    def action_enter_edit_mode(self) -> None:
        """Enter EDIT mode by focusing on first form field."""
        if not self._form_widget:
            return

        # Clear VIEW mode highlights
        self._form_widget.clear_highlight()

        # Focus on the first editable field
        for field_widget in self._form_widget.field_widgets.values():
            if hasattr(field_widget, "focus") and not field_widget.disabled:
                field_widget.focus()
                self._mode = "EDIT"
                logger.info("Entered EDIT mode")
                break

    def action_handle_escape(self) -> None:
        """Handle Escape key - exit EDIT mode or cancel.

        Note: This should rarely be called in EDIT mode because on_key()
        handles Esc with event.stop(). This is a fallback for robustness.
        """
        from textual.widgets import Input, Select, TextArea

        # Real-time detection: check if any form field is currently focused
        focused = self.app.focused
        in_edit_mode = isinstance(focused, (Input, TextArea, Select))

        if in_edit_mode:
            # We're in a form field - exit EDIT mode
            self.set_focus(None)
            self._mode = "VIEW"
            logger.info("Exited EDIT mode via action (fallback)")
        else:
            # No form field focused - close the screen
            self.dismiss(None)

    def action_save_settings(self) -> None:
        """Save settings to config."""
        if not self._form_widget:
            return

        # Get values from form
        values = self._form_widget.get_values()

        # Validate required fields
        is_valid, errors = self._form_widget.validate_all()
        if not is_valid:
            logger.warning(f"Validation failed: {errors}")
            try:
                if command_bar := self.query_one("#command-bar", CommandBar):
                    error_msg = ", ".join(errors.values())
                    command_bar.show_message(f"✗ Validation failed: {error_msg}")
            except Exception:
                pass
            return

        # Convert string values to appropriate types and update config
        try:
            self.config_manager.update(
                theme=values.get("theme", "dark"),
                refresh_interval=int(values.get("refresh_interval", "1000")),
                auto_refresh=values.get("auto_refresh") == "true",
                connection_timeout=int(values.get("connection_timeout", "10")),
                reconnect_interval=int(values.get("reconnect_interval", "5")),
                prefer_websocket=values.get("prefer_websocket") == "true",
                websocket_fallback_http=values.get("websocket_fallback_http") == "true",
                max_concurrent_downloads=int(values.get("max_concurrent_downloads", "5")),
                max_connection_per_server=int(values.get("max_connection_per_server", "16")),
                enable_notifications=values.get("enable_notifications") == "true",
                play_sound_on_complete=values.get("play_sound_on_complete") == "true",
                play_sound_on_error=values.get("play_sound_on_error") == "true",
            )

            logger.info("App settings saved successfully")

            try:
                if command_bar := self.query_one("#command-bar", CommandBar):
                    command_bar.show_message("✓ Settings saved")
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            try:
                if command_bar := self.query_one("#command-bar", CommandBar):
                    command_bar.show_message(f"✗ Failed to save: {e}")
            except Exception:
                pass

    def action_quit(self) -> None:
        """Quit and close screen."""
        self.dismiss(None)
