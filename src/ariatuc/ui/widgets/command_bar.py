"""Command bar widget displaying available keyboard shortcuts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import Static

if TYPE_CHECKING:
    from ariatuc.ui.keybinding_manager import (
        KeybindingContext,
        KeybindingManager,
        KeybindingMode,
    )


class CommandBar(Static):
    """Command bar showing available keyboard shortcuts for current context.

    Displays context-sensitive shortcuts to help users remember available
    commands. The command bar updates based on which panel has focus.

    Inspired by lazygit's command bar.
    """

    DEFAULT_CSS = """
    CommandBar {
        height: 1;
        dock: bottom;
        background: $panel;
        color: $text-muted;
        content-align: left middle;
        padding: 0 1;
    }
    """

    # Command sets for different contexts
    MAIN_COMMANDS = (
        "a-add | d-delete | p-pause | e-edit | r-refresh | s-servers | g-settings | ?-help | q-quit"
    )
    LIST_COMMANDS = "j/k-navigate | 1/2/3-tabs | Space-select | /-search | Enter-details"
    DETAIL_COMMANDS = "h/l-tabs | Esc-close | e-edit"
    DIALOG_COMMANDS = "Tab-next | Enter-confirm | Esc-cancel"

    def __init__(
        self,
        keybinding_manager: KeybindingManager | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize command bar.

        Args:
            keybinding_manager: Keybinding manager instance for dynamic hints
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(self.MAIN_COMMANDS, name=name, id=id, classes=classes)
        self.keybinding_manager = keybinding_manager
        self._current_context = "main"
        self._current_mode_name = ""

    def set_context(self, context: str) -> None:
        """Update command bar for a specific context.

        Args:
            context: Context name ("main", "list", "detail", "dialog")
        """
        self._current_context = context

        if context == "list":
            commands = f"{self.LIST_COMMANDS} | {self.MAIN_COMMANDS}"
        elif context == "detail":
            commands = f"{self.DETAIL_COMMANDS} | {self.MAIN_COMMANDS}"
        elif context == "dialog":
            commands = self.DIALOG_COMMANDS
        else:
            commands = self.MAIN_COMMANDS

        self.update(commands)

    def update_hints(
        self,
        context: KeybindingContext,
        mode: KeybindingMode | None = None,
    ) -> None:
        """Update command bar hints from keybinding manager.

        Args:
            context: The context to show hints for
            mode: The mode to filter hints by (defaults to current mode)
        """
        if not self.keybinding_manager:
            # Fallback to old behavior
            return

        from ariatuc.ui.keybinding_manager import KeybindingMode

        # Get hints from manager
        hints = self.keybinding_manager.get_hints_for_context(context, mode, max_hints=12)

        # Format hints
        hint_str = " | ".join(f"{key}-{desc}" for key, desc in hints)

        # Add mode indicator if not NORMAL
        use_mode = mode or self.keybinding_manager.current_mode
        if use_mode != KeybindingMode.NORMAL:
            mode_name = use_mode.value.upper()
            hint_str = f"[{mode_name}] {hint_str}"
            self._current_mode_name = mode_name
        else:
            self._current_mode_name = ""

        self.update(hint_str)

    def show_message(self, message: str, duration: float = 3.0) -> None:
        """Temporarily show a message in the command bar.

        Args:
            message: Message to display
            duration: How long to show the message (seconds)
        """
        original_context = self._current_context

        # Show message
        self.update(message)

        # Restore original context after duration
        self.set_timer(duration, lambda: self.set_context(original_context))
