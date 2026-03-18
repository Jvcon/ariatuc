"""Add download dialog for creating new downloads."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from textual import events
from textual.app import ComposeResult
from textual.containers import Grid, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, TabbedContent, TabPane, TextArea


class AddDownloadDialog(ModalScreen[dict[str, Any] | None]):
    """Modal dialog for adding new downloads.

    Supports three input types:
    - URLs: Enter one or more HTTP/FTP URLs (one per line)
    - Torrent File: Provide path to .torrent file
    - Magnet Link: Enter magnet URI

    Allows users to optionally set:
    - Download directory
    - Connection parameters (max connections, split)

    Returns a dict with download info if confirmed, None if cancelled.

    Return structure:
        {
            'type': 'url' | 'torrent' | 'magnet',
            'urls': List[str],  # For URL and magnet types
            'torrent_data': bytes,  # For torrent type
            'options': Dict[str, Any]
        }

    Example:
        >>> result = await self.app.push_screen_wait(AddDownloadDialog())
        >>> if result:
        ...     if result['type'] == 'torrent':
        ...         await service.add_torrent(result['torrent_data'], options=result['options'])
        ...     else:
        ...         await service.add_download(result['urls'], options=result['options'])
    """

    DEFAULT_CSS = """
    AddDownloadDialog {
        align: center middle;
    }

    AddDownloadDialog > Vertical {
        width: 80;
        height: auto;
        max-height: 90%;
        background: $panel;
        border: thick $primary;
        padding: 1;
    }

    AddDownloadDialog #title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $text;
        background: $primary;
        padding: 0 1;
        margin-bottom: 0;
    }

    AddDownloadDialog TabbedContent {
        width: 100%;
        height: auto;
        min-height: 30;
        max-height: 45;
        margin-bottom: 0;
    }

    AddDownloadDialog TabPane {
        padding: 1;
        height: auto;
        min-height: 25;
    }

    AddDownloadDialog TabPane > VerticalScroll {
        width: 100%;
        height: 28;
        min-height: 20;
    }

    /* Form elements inherit compact spacing from theme */
    AddDownloadDialog Label {
        width: 100%;
        color: $text-muted;
    }

    AddDownloadDialog Input {
        width: 100%;
    }

    AddDownloadDialog TextArea {
        width: 100%;
    }

    /* Options container */
    AddDownloadDialog #options-container {
        width: 100%;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-top: 1;
    }

    AddDownloadDialog #button-container {
        width: 100%;
        height: auto;
        grid-size: 2;
        grid-gutter: 1;
        padding: 0;
        margin-top: 1;
    }

    AddDownloadDialog Button {
        width: 100%;
        min-width: 16;
    }

    AddDownloadDialog .error {
        color: $error;
        text-style: bold;
    }

    /* Info labels inherit compact spacing from theme */
    AddDownloadDialog .info {
        color: $text-muted;
        text-style: italic;
    }
    """

    # Note: escape removed - handled by on_key() for two-stage behavior
    BINDINGS = [
        ("ctrl+s", "confirm", "Add Download"),
    ]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize add download dialog.

        Args:
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        # URL tab widgets
        self._url_input: TextArea | None = None
        # Torrent tab widgets
        self._torrent_path_input: Input | None = None
        # Magnet tab widgets
        self._magnet_input: Input | None = None
        # Common options
        self._dir_input: Input | None = None
        self._max_conn_input: Input | None = None
        self._split_input: Input | None = None
        self._error_label: Label | None = None
        # Track active tab
        self._tabbed_content: TabbedContent | None = None

    def compose(self) -> ComposeResult:
        """Create dialog widgets."""
        with Vertical():
            yield Static("Add Download", id="title")

            # Tabbed content for different input types
            with TabbedContent(id="input-tabs"):
                # Tab 1: URLs
                with TabPane("URLs", id="tab-urls"):
                    with VerticalScroll():
                        yield Label("Enter URLs (one per line):")
                        yield Label("Supports HTTP, HTTPS, FTP protocols", classes="info")
                        self._url_input = TextArea(id="url-input")
                        yield self._url_input

                        # Options section (within URL tab)
                        with Vertical(id="options-container"):
                            yield Label("Download Options (optional)")

                            yield Label("Directory:")
                            self._dir_input = Input(
                                placeholder="/path/to/download/directory",
                                id="dir-input",
                            )
                            yield self._dir_input

                            yield Label("Max Connections per Server:")
                            self._max_conn_input = Input(
                                placeholder="16",
                                id="max-conn-input",
                            )
                            yield self._max_conn_input

                            yield Label("Split (number of connections per file):")
                            self._split_input = Input(
                                placeholder="4",
                                id="split-input",
                            )
                            yield self._split_input

                # Tab 2: Torrent File
                with TabPane("Torrent File", id="tab-torrent"):
                    with VerticalScroll():
                        yield Label("Torrent File Path:")
                        yield Label("Enter the full path to a .torrent file", classes="info")
                        self._torrent_path_input = Input(
                            placeholder="/path/to/file.torrent",
                            id="torrent-path-input",
                        )
                        yield self._torrent_path_input

                        # Options section (within Torrent tab) - reference same inputs
                        with Vertical(id="options-container-torrent"):
                            yield Label("Download Options (optional)")

                            yield Label("Directory:")
                            yield Input(
                                placeholder="/path/to/download/directory",
                                id="dir-input-torrent",
                            )

                            yield Label("Max Connections per Server:")
                            yield Input(
                                placeholder="16",
                                id="max-conn-input-torrent",
                            )

                            yield Label("Split (number of connections per file):")
                            yield Input(
                                placeholder="4",
                                id="split-input-torrent",
                            )

                # Tab 3: Magnet Link
                with TabPane("Magnet Link", id="tab-magnet"):
                    with VerticalScroll():
                        yield Label("Magnet URI:")
                        yield Label("Paste magnet link starting with magnet:?", classes="info")
                        self._magnet_input = Input(
                            placeholder="magnet:?xt=urn:btih:...",
                            id="magnet-input",
                        )
                        yield self._magnet_input

                        # Options section (within Magnet tab) - reference same inputs
                        with Vertical(id="options-container-magnet"):
                            yield Label("Download Options (optional)")

                            yield Label("Directory:")
                            yield Input(
                                placeholder="/path/to/download/directory",
                                id="dir-input-magnet",
                            )

                            yield Label("Max Connections per Server:")
                            yield Input(
                                placeholder="16",
                                id="max-conn-input-magnet",
                            )

                            yield Label("Split (number of connections per file):")
                            yield Input(
                                placeholder="4",
                                id="split-input-magnet",
                            )

            # Error message (initially hidden)
            self._error_label = Label("", classes="error")
            yield self._error_label

            # Buttons
            with Grid(id="button-container"):
                yield Button(
                    "Add Download",
                    variant="primary",
                    id="confirm-btn",
                )
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        """Set up after mounting."""
        # Store reference to tabbed content
        self._tabbed_content = self.query_one("#input-tabs", TabbedContent)

        # Focus URL input when mounted
        if self._url_input:
            self._url_input.focus()

    def on_key(self, event: events.Key) -> None:
        """Handle ESC key for two-stage behavior.

        First ESC: Blur focused input (exit edit mode)
        Second ESC: Close dialog
        """
        if event.key == "escape":
            focused = self.app.focused

            if isinstance(focused, (Input, TextArea)):
                # Currently in edit mode - blur to browse mode
                focused.blur()
            else:
                # Already in browse mode - close dialog
                self.action_cancel()

            event.prevent_default()

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
        """Validate and confirm adding download."""
        # Clear previous error
        if self._error_label:
            self._error_label.update("")

        if not self._tabbed_content:
            return

        # Determine which tab is active
        active_tab = self._tabbed_content.active

        result: dict[str, Any] | None = None

        if active_tab == "tab-urls":
            result = self._process_url_input()
        elif active_tab == "tab-torrent":
            result = self._process_torrent_input()
        elif active_tab == "tab-magnet":
            result = self._process_magnet_input()

        if result:
            self.dismiss(result)

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)

    def _get_urls(self) -> list[str]:
        """Extract and validate URLs from input.

        Returns:
            List of non-empty URLs
        """
        if not self._url_input:
            return []

        # Get text and split by lines
        text = self._url_input.text
        lines = text.strip().split("\n")

        # Filter out empty lines and whitespace
        urls = [line.strip() for line in lines if line.strip()]

        return urls

    def _get_options(self, tab_id: str = "tab-urls") -> dict[str, Any]:
        """Extract download options from inputs based on active tab.

        Args:
            tab_id: ID of the active tab to read options from

        Returns:
            Dict of aria2 download options
        """
        options: dict[str, Any] = {}

        # Determine input ID suffixes based on tab
        if tab_id == "tab-urls":
            dir_id = "dir-input"
            max_conn_id = "max-conn-input"
            split_id = "split-input"
        elif tab_id == "tab-torrent":
            dir_id = "dir-input-torrent"
            max_conn_id = "max-conn-input-torrent"
            split_id = "split-input-torrent"
        elif tab_id == "tab-magnet":
            dir_id = "dir-input-magnet"
            max_conn_id = "max-conn-input-magnet"
            split_id = "split-input-magnet"
        else:
            return options

        # Directory
        try:
            dir_input = self.query_one(f"#{dir_id}", Input)
            if dir_input.value:
                options["dir"] = dir_input.value
        except Exception:
            pass

        # Max connections per server
        try:
            max_conn_input = self.query_one(f"#{max_conn_id}", Input)
            if max_conn_input.value:
                try:
                    max_conn = int(max_conn_input.value)
                    if max_conn > 0:
                        options["max-connection-per-server"] = max_conn
                except ValueError:
                    pass  # Ignore invalid input
        except Exception:
            pass

        # Split
        try:
            split_input = self.query_one(f"#{split_id}", Input)
            if split_input.value:
                try:
                    split = int(split_input.value)
                    if split > 0:
                        options["split"] = split
                except ValueError:
                    pass  # Ignore invalid input
        except Exception:
            pass

        return options

    def _process_url_input(self) -> dict[str, Any] | None:
        """Process URL input and return result dict.

        Returns:
            Result dict or None if validation fails
        """
        # Get and validate URLs
        urls = self._get_urls()
        if not urls:
            if self._error_label:
                self._error_label.update("Error: At least one URL is required")
            return None

        # Get options from URL tab
        options = self._get_options(tab_id="tab-urls")

        # Return result
        return {"type": "url", "urls": urls, "options": options}

    def _process_torrent_input(self) -> dict[str, Any] | None:
        """Process torrent file input and return result dict.

        Returns:
            Result dict or None if validation fails
        """
        if not self._torrent_path_input or not self._torrent_path_input.value:
            if self._error_label:
                self._error_label.update("Error: Torrent file path is required")
            return None

        torrent_path = Path(self._torrent_path_input.value.strip())

        # Validate file exists
        if not torrent_path.exists():
            if self._error_label:
                self._error_label.update(f"Error: File not found: {torrent_path}")
            return None

        # Validate file extension
        if torrent_path.suffix.lower() != ".torrent":
            if self._error_label:
                self._error_label.update("Error: File must have .torrent extension")
            return None

        # Read and encode torrent file
        try:
            with open(torrent_path, "rb") as f:
                torrent_data = f.read()

            # Encode to base64 for aria2 RPC
            torrent_base64 = base64.b64encode(torrent_data).decode("ascii")

        except Exception as e:
            if self._error_label:
                self._error_label.update(f"Error reading torrent file: {str(e)}")
            return None

        # Get options from Torrent tab
        options = self._get_options(tab_id="tab-torrent")

        # Return result
        return {"type": "torrent", "torrent_data": torrent_base64, "options": options}

    def _process_magnet_input(self) -> dict[str, Any] | None:
        """Process magnet link input and return result dict.

        Returns:
            Result dict or None if validation fails
        """
        if not self._magnet_input or not self._magnet_input.value:
            if self._error_label:
                self._error_label.update("Error: Magnet link is required")
            return None

        magnet_uri = self._magnet_input.value.strip()

        # Validate magnet URI format
        if not magnet_uri.startswith("magnet:?"):
            if self._error_label:
                self._error_label.update("Error: Invalid magnet link (must start with magnet:?)")
            return None

        # Basic validation - check for xt parameter
        if "xt=urn:btih:" not in magnet_uri:
            if self._error_label:
                self._error_label.update("Error: Invalid magnet link (missing info hash)")
            return None

        # Get options from Magnet tab
        options = self._get_options(tab_id="tab-magnet")

        # Return result (magnet links are treated as URLs by aria2)
        return {"type": "magnet", "urls": [magnet_uri], "options": options}
