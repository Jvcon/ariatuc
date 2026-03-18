"""Input dialog for user text input."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class InputDialog(ModalScreen[str | None]):
    """Modal input dialog.

    Displays a message and input field, with OK/Cancel buttons.
    Returns the input value if confirmed, None if cancelled.

    Examples:
        >>> result = await self.app.push_screen_wait(
        ...     InputDialog("Enter server name:", initial_value="Server 1")
        ... )
        >>> if result:
        ...     # User entered a value
        ...     print(f"Got: {result}")
    """

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }

    InputDialog > Vertical {
        width: 60;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 1 2;
    }

    InputDialog #title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $text;
        background: $primary;
        padding: 1;
        margin-bottom: 1;
    }

    InputDialog #message {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        padding: 1;
        color: $text;
    }

    InputDialog #input-container {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        padding: 0 1;
    }

    InputDialog Input {
        width: 100%;
    }

    InputDialog #button-container {
        width: 100%;
        height: auto;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
    }

    InputDialog Button {
        width: 100%;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        message: str,
        *,
        title: str = "Input",
        initial_value: str = "",
        placeholder: str = "",
        ok_label: str = "OK",
        cancel_label: str = "Cancel",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize input dialog.

        Args:
            message: Message to display above input field
            title: Dialog title
            initial_value: Initial value for input field
            placeholder: Placeholder text for input field
            ok_label: Text for OK button
            cancel_label: Text for cancel button
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.message: str = message
        self.title: str = title
        self.initial_value: str = initial_value
        self.placeholder: str = placeholder
        self.ok_label: str = ok_label
        self.cancel_label: str = cancel_label
        self._input: Input | None = None

    def compose(self) -> ComposeResult:
        """Create dialog widgets."""
        with Vertical():
            yield Static(self.title, id="title")
            yield Label(self.message, id="message")

            # Input field
            with Vertical(id="input-container"):
                self._input = Input(
                    value=self.initial_value,
                    placeholder=self.placeholder,
                    id="input-field",
                )
                yield self._input

            # Buttons
            with Grid(id="button-container"):
                yield Button(self.ok_label, variant="primary", id="ok-btn")
                yield Button(self.cancel_label, variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        """Focus input field when mounted."""
        if self._input:
            self._input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button pressed event
        """
        if event.button.id == "ok-btn":
            self.action_submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input field.

        Args:
            event: Input submitted event
        """
        self.action_submit()

    def action_submit(self) -> None:
        """Submit input value and close dialog."""
        if self._input:
            value = self._input.value.strip()
            # Don't allow empty values
            if value:
                self.dismiss(value)
            else:
                # Flash input field to indicate error
                self._input.focus()

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)
