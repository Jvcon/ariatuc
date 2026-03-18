"""Confirmation dialog for user actions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Label, Static


class ConfirmDialog(ModalScreen[bool]):
    """Modal confirmation dialog.

    Displays a message and optional checkbox, with Confirm/Cancel buttons.
    Returns True if confirmed, False if cancelled.

    Examples:
        >>> result = await self.app.push_screen_wait(
        ...     ConfirmDialog("Delete this download?", checkbox_label="Also delete files")
        ... )
        >>> if result:
        ...     # User confirmed
        ...     pass
    """

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    ConfirmDialog > Vertical {
        width: 60;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 1 2;
    }

    ConfirmDialog #title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $text;
        background: $primary;
        padding: 1;
        margin-bottom: 1;
    }

    ConfirmDialog #message {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        padding: 1;
        color: $text;
    }

    ConfirmDialog #checkbox-container {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        padding: 0 1;
    }

    ConfirmDialog #button-container {
        width: 100%;
        height: auto;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
    }

    ConfirmDialog Button {
        width: 100%;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "confirm", "Confirm"),
    ]

    def __init__(
        self,
        message: str,
        *,
        title: str = "Confirm",
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        checkbox_label: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize confirmation dialog.

        Args:
            message: Confirmation message to display
            title: Dialog title
            confirm_label: Text for confirm button
            cancel_label: Text for cancel button
            checkbox_label: Optional checkbox label (shows checkbox if provided)
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.message: str = message
        self.title: str = title
        self.confirm_label: str = confirm_label
        self.cancel_label: str = cancel_label
        self.checkbox_label: str | None = checkbox_label
        self._checkbox: Checkbox | None = None
        self.checkbox_value: bool = False

    def compose(self) -> ComposeResult:
        """Create dialog widgets."""
        with Vertical():
            yield Static(self.title, id="title")
            yield Label(self.message, id="message")

            # Optional checkbox
            if self.checkbox_label:
                with Vertical(id="checkbox-container"):
                    self._checkbox = Checkbox(self.checkbox_label)
                    yield self._checkbox

            # Buttons
            with Grid(id="button-container"):
                yield Button(self.confirm_label, variant="primary", id="confirm-btn")
                yield Button(self.cancel_label, variant="default", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button pressed event
        """
        if event.button.id == "confirm-btn":
            self.action_confirm()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def action_confirm(self) -> None:
        """Confirm action and close dialog."""
        # Get checkbox value if present
        if self._checkbox:
            self.checkbox_value = self._checkbox.value

        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel action and close dialog."""
        self.dismiss(False)


class MessageDialog(ModalScreen[None]):
    """Simple message dialog with only an OK button.

    Used for informational messages or errors that don't require confirmation.
    """

    DEFAULT_CSS = """
    MessageDialog {
        align: center middle;
    }

    MessageDialog > Vertical {
        width: 60;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 1 2;
    }

    MessageDialog #title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $text;
        background: $primary;
        padding: 1;
        margin-bottom: 1;
    }

    MessageDialog #message {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        padding: 1;
        color: $text;
    }

    MessageDialog Button {
        width: 100%;
        margin: 0 auto;
    }
    """

    BINDINGS = [
        ("escape", "close", "Close"),
        ("enter", "close", "Close"),
    ]

    def __init__(
        self,
        message: str,
        *,
        title: str = "Message",
        button_label: str = "OK",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize message dialog.

        Args:
            message: Message to display
            title: Dialog title
            button_label: Text for OK button
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.message: str = message
        self.title: str = title
        self.button_label: str = button_label

    def compose(self) -> ComposeResult:
        """Create dialog widgets."""
        with Vertical():
            yield Static(self.title, id="title")
            yield Label(self.message, id="message")
            yield Button(self.button_label, variant="primary", id="ok-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button pressed event
        """
        if event.button.id == "ok-btn":
            self.action_close()

    def action_close(self) -> None:
        """Close dialog."""
        self.dismiss()
