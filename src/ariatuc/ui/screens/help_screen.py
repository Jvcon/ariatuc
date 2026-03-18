"""Help screen displaying keyboard shortcuts and usage information."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static


class HelpScreen(ModalScreen[None]):
    """Help screen showing keyboard shortcuts and usage tips.

    Displays categorized keyboard shortcuts for all actions available
    in the application. Press any key or Esc to close.
    """

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen > VerticalScroll {
        width: 90;
        height: 90%;
        background: $panel;
        border: thick $primary;
        padding: 2;
    }

    HelpScreen #title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $text;
        background: $primary;
        padding: 1;
        margin-bottom: 2;
    }

    HelpScreen .section-title {
        text-style: bold;
        color: $primary;
        margin-top: 1;
        margin-bottom: 1;
    }

    HelpScreen .shortcut-row {
        color: $text;
        margin-left: 2;
    }

    HelpScreen .key {
        text-style: bold;
        color: $success;
    }

    HelpScreen .description {
        color: $text-muted;
    }

    HelpScreen #footer-hint {
        color: $text-muted;
        text-align: center;
        margin-top: 2;
        padding: 1;
        border: solid $primary;
    }
    """

    BINDINGS = [
        ("escape", "close", "Close"),
    ]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize help screen.

        Args:
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        """Create help content."""
        with VerticalScroll():
            yield Static("ariatuc - Keyboard Shortcuts", id="title")

            # Global shortcuts
            yield Static("Global", classes="section-title")
            yield Static("[key]?[/key]       Show this help", classes="shortcut-row")
            yield Static("[key]q[/key]       Quit application", classes="shortcut-row")
            yield Static("[key]:][/key]       Command mode (future)", classes="shortcut-row")

            # Navigation shortcuts
            yield Static("Navigation", classes="section-title")
            yield Static(
                "[key]j / k[/key]   Navigate up/down in download list", classes="shortcut-row"
            )
            yield Static(
                "[key]↑ / ↓[/key]   Navigate up/down (alternative)", classes="shortcut-row"
            )
            yield Static(
                "[key]H[/key]       Focus left panel (download list)", classes="shortcut-row"
            )
            yield Static(
                "[key]L[/key]       Focus right panel (download detail)", classes="shortcut-row"
            )
            yield Static("[key]Tab[/key]     Toggle focus between panels", classes="shortcut-row")

            # Tab switching shortcuts
            yield Static("Tab Switching", classes="section-title")
            yield Static(
                "[key]1[/key]       Switch to Active tab (left panel)", classes="shortcut-row"
            )
            yield Static(
                "[key]2[/key]       Switch to Waiting tab (left panel)", classes="shortcut-row"
            )
            yield Static(
                "[key]3[/key]       Switch to Stopped tab (left panel)", classes="shortcut-row"
            )
            yield Static(
                "[key]t[/key]       Next tab (within focused panel)", classes="shortcut-row"
            )
            yield Static(
                "[key]T[/key]       Previous tab (within focused panel)", classes="shortcut-row"
            )

            # Download actions
            yield Static("Download Actions", classes="section-title")
            yield Static("[key]a[/key]       Add new download", classes="shortcut-row")
            yield Static("[key]d[/key]       Delete selected download", classes="shortcut-row")
            yield Static("[key]p[/key]       Smart Pause/Resume/Retry:", classes="shortcut-row")
            yield Static("              - ACTIVE/WAITING → Pause", classes="shortcut-row")
            yield Static("              - PAUSED → Resume", classes="shortcut-row")
            yield Static(
                "              - ERROR → Retry (re-add with same URLs)", classes="shortcut-row"
            )
            yield Static(
                "[key]e[/key]       Edit download options (future)", classes="shortcut-row"
            )
            yield Static("[key]r[/key]       Refresh download list", classes="shortcut-row")
            yield Static("[key]Enter[/key]   Toggle preview mode", classes="shortcut-row")

            # Management shortcuts
            yield Static("Management", classes="section-title")
            yield Static("[key]s[/key]       Server management", classes="shortcut-row")
            yield Static("[key]g[/key]       Global settings", classes="shortcut-row")

            # Dialog shortcuts
            yield Static("Dialogs", classes="section-title")
            yield Static(
                "[key]Tab[/key]     Cycle focus between inputs/buttons", classes="shortcut-row"
            )
            yield Static("[key]Enter[/key]   Activate focused button", classes="shortcut-row")
            yield Static(
                "[key]Esc[/key]     First press: Exit edit mode, Second: Close",
                classes="shortcut-row",
            )
            yield Static(
                "[key]Ctrl+s[/key]  Confirm in add download dialog", classes="shortcut-row"
            )

            # Mode information
            yield Static("Modes", classes="section-title")
            yield Static(
                "Browse mode:  Default state, use shortcuts to navigate", classes="shortcut-row"
            )
            yield Static(
                "Edit mode:    Auto-entered when typing in Input/TextArea", classes="shortcut-row"
            )
            yield Static(
                "              Navigation shortcuts disabled in edit mode", classes="shortcut-row"
            )
            yield Static("Preview mode: Press Enter to enable/disable", classes="shortcut-row")
            yield Static(
                "              When ON: j/k auto-shows download details", classes="shortcut-row"
            )
            yield Static("              When OFF: right panel cleared", classes="shortcut-row")
            yield Static("              Auto-disabled when switching tabs", classes="shortcut-row")

            # Sorting and filtering (future)
            yield Static("Sorting & Filtering (Future)", classes="section-title")
            yield Static("[key]s n[/key]     Sort by name", classes="shortcut-row")
            yield Static("[key]s s[/key]     Sort by size", classes="shortcut-row")
            yield Static("[key]s p[/key]     Sort by progress", classes="shortcut-row")
            yield Static("[key]s v[/key]     Sort by speed", classes="shortcut-row")
            yield Static("[key]s t[/key]     Sort by time", classes="shortcut-row")

            # Footer
            yield Static(
                "[Press any key or Esc to close]",
                id="footer-hint",
            )

    def on_key(self, event) -> None:
        """Close help screen on any key press.

        Args:
            event: Key event
        """
        _ = event  # Unused, but required by Textual event handler signature
        self.action_close()

    def action_close(self) -> None:
        """Close the help screen."""
        self.dismiss()
