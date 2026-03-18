"""Server management screen for managing multiple aria2 RPC servers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static

from ariatuc.ui.widgets.command_bar import CommandBar
from ariatuc.ui.widgets.form_widget import FormWidget
from ariatuc.ui.widgets.server_field_definitions import SERVER_FIELDS

if TYPE_CHECKING:
    from ariatuc.core.service import Aria2Service

logger = logging.getLogger(__name__)


class ServerManagementScreen(ModalScreen[dict[str, Any] | None]):
    """Server management screen for managing multiple aria2 RPC servers.

    Features:
    - Server list display with current server indicator
    - Add/edit/delete server operations
    - Server configuration form with validation
    - Connection testing
    - Protocol auto-detection

    Layout:
    ┌────────────────────────────────────────┐
    │ Server Management                      │ (Title bar)
    ├──────────────┬─────────────────────────┤
    │ Servers (2:8)│ Configuration           │
    │ • Server 1 * │ Name: [          ]      │
    │   Server 2   │ URL:  [          ]      │
    │   Server 3   │ Protocol: [Auto ▼]     │
    │              │ Secret: [          ]    │
    │              │ ...                     │
    ├──────────────┴─────────────────────────┤
    │ a-Add | d-Del | r-Rename | w-Save ...  │ (Command bar)
    └────────────────────────────────────────┘

    Keyboard shortcuts (Unified with Aria2 Settings):
    VIEW Mode (default):
    - t/T: Cycle through servers (global, regardless of focus)
    - j/k: Navigate form fields (global, scroll only, no focus)
    - i: Enter EDIT mode (focus on first form field)
    - a: Add new server
    - d: Delete selected server
    - r: Rename server
    - w: Save server configuration
    - Enter: Test connection
    - Space: Set as current server
    - Esc: Close screen
    - q: Quit screen

    EDIT Mode (when a field is focused):
    - Esc: Exit EDIT mode and return to VIEW mode
    - Tab: Navigate between fields (standard Textual behavior)
    - Type to edit field content

    Returns:
        None if cancelled, or dict with server changes
    """

    DEFAULT_CSS = """
    ServerManagementScreen {
        background: $surface;
    }

    /* Title bar matching StatusBar style (height: 1) */
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

    /* Main content with 2:8 ratio (1fr:4fr) */
    #main-content {
        height: 1fr;
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 4fr;
    }

    /* Server list panel (left, 1fr = 20% width) */
    #server-list-panel {
        border: solid $primary;
        width: 100%;
        height: 100%;
    }

    #server-list-title {
        dock: top;
        height: 1;
        text-style: bold;
        background: $primary;
        color: $text;
        content-align: left middle;
        padding: 0 1;
    }

    #server-list {
        height: 1fr;
        width: 100%;
    }

    /* Form panel (right, 4fr = 80% width) */
    #form-panel {
        border: solid $primary;
        width: 100%;
        height: 100%;
        margin-left: 1;
    }

    #form-container {
        width: 100%;
        height: 100%;
    }

    /* Ensure FormWidget fills the container */
    #form-container > FormWidget {
        width: 100%;
        height: 100%;
    }

    /* Server list items */
    #server-list > ListItem {
        padding: 0 1;
        height: 3;
    }

    #server-list > ListItem:hover {
        background: $primary-darken-2;
    }

    #server-list > ListItem > Label {
        width: 100%;
        height: 100%;
    }

    /* Current server indicator */
    .server-current {
        color: $success;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("a", "add_server", "Add Server"),
        ("d", "delete_server", "Delete Server"),
        ("i", "enter_edit_mode", "Edit"),
        ("escape", "handle_escape", ""),  # No hint - default behavior
        ("w", "save_server", "Save"),
        ("q", "quit", "Quit"),
        ("enter", "test_connection", "Test Connection"),
        ("space", "set_current_server", "Set as Current"),
        ("less_than_sign", "move_server_up", "Move Up"),
        ("greater_than_sign", "move_server_down", "Move Down"),
        ("s", "start_local_process", "Start Process"),
        ("t", "stop_local_process", "Stop Process"),
        ("r", "restart_local_process", "Restart Process"),
        ("ctrl+s", "save_session", "Save Session"),
    ]

    def __init__(
        self,
        service: Aria2Service,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize server management screen.

        Args:
            service: Aria2Service instance
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service = service

        # Server data storage - load from RPCManager
        self._servers: list[dict[str, Any]] = []
        self._current_server_index = 0
        self._load_servers_from_service()

        # UI components
        self._server_list: ListView | None = None
        self._form_widget: FormWidget | None = None
        self._form_container: Vertical | None = None

        # VIEW/EDIT mode tracking
        self._mode = "VIEW"  # "VIEW" or "EDIT"
        self._current_field_index = 0  # Track current field in VIEW mode navigation

    def _load_servers_from_service(self) -> None:
        """Load server configurations from RPCManager."""
        # Load from RPCManager's server list
        for name, server_config in self.service.rpc_mgr.servers.items():
            self._servers.append(
                {
                    "name": name,
                    "url": server_config.url,
                    "protocol": "auto",  # Will be detected from URL
                    "secret": server_config.secret or "",
                    "username": "",
                    "password": "",
                    "timeout": str(self.service.rpc_mgr.connection_timeout),
                    "is_current": name == self.service.rpc_mgr.current_server,
                    "is_local": server_config.is_local,  # Track local servers
                }
            )

            # Track current server index
            if name == self.service.rpc_mgr.current_server:
                self._current_server_index = len(self._servers) - 1

        # If no servers loaded, add a default one
        if not self._servers:
            self._servers.append(
                {
                    "name": "Local Server",
                    "url": "http://localhost:6800/jsonrpc",
                    "protocol": "auto",
                    "secret": "",
                    "username": "",
                    "password": "",
                    "timeout": "30",
                    "is_current": True,
                }
            )
            self._current_server_index = 0

        logger.info(f"Loaded {len(self._servers)} servers from service")

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        # Title bar at top (like StatusBar)
        yield Static("Server Management", id="title")

        # Main content area with two panels
        with Horizontal(id="main-content"):
            # Left panel: Server list (1fr = 20%)
            with Vertical(id="server-list-panel"):
                yield Static("Servers", id="server-list-title")
                # Create ListView with server items
                with ListView(id="server-list") as server_list:
                    for idx, server in enumerate(self._servers):
                        # Yield items during compose (don't use mount)
                        yield self._create_server_item(server, idx)
                self._server_list = server_list

            # Right panel: Server configuration form (4fr = 80%)
            with Vertical(id="form-panel"):
                self._form_container = Vertical(id="form-container")
                # Form will be added in on_mount
                yield self._form_container

        # Command bar at bottom (reuse existing widget)
        command_bar = CommandBar(id="command-bar")
        command_bar.update(
            "a-Add | d-Del | </>-Move | Space-Set | i-Edit | w-Save | Enter-Test | s-Start | t-Stop | r-Restart | ^S-SaveSession"
        )
        yield command_bar

    def _create_server_item(self, server: dict[str, Any], index: int) -> ListItem:
        """Create a server list item (for compose stage).

        Args:
            server: Server data dict
            index: Server index

        Returns:
            ListItem widget
        """
        # Get server state from RPCManager
        server_name = server["name"]
        state = self.service.rpc_mgr.get_server_state(server_name)

        # Determine protocol from URL
        url = server["url"]
        if url.startswith(("ws://", "wss://")):
            protocol = "WS"
        elif url.startswith(("http://", "https://")):
            protocol = "HTTP"
        else:
            protocol = "?"

        # Determine connection status
        if state:
            state_str = state.state.value
            if state_str == "connected":
                status_icon = "✓"
            elif state_str == "connecting":
                status_icon = "⋯"
            elif state_str == "failed":
                status_icon = "✗"
            else:
                status_icon = "○"
        else:
            status_icon = "○"

        # Check local process status
        process_status = ""
        if server.get("is_local", False):
            process_info = self.service.get_local_process_info(server_name)
            if process_info:
                if process_info.state.value == "running":
                    process_status = " [PROC:▶]"
                elif process_info.state.value == "stopped":
                    process_status = " [PROC:■]"
                elif process_info.state.value == "error":
                    process_status = " [PROC:✗]"
                elif process_info.state.value == "starting":
                    process_status = " [PROC:⋯]"
            else:
                process_status = " [PROC:■]"

        # Extract host from URL for compact display
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            host = parsed.hostname or "unknown"
            port = f":{parsed.port}" if parsed.port else ""
            url_short = f"{host}{port}"
        except Exception:
            url_short = url[:20]

        # Build label: "● Name [WS|✓] host:port [PROC:▶]"
        current_indicator = "● " if server.get("is_current", False) else "  "
        label_text = f"{current_indicator}{server_name}\n  [{protocol}|{status_icon}] {url_short}{process_status}"

        label = Label(label_text)
        if server.get("is_current", False):
            label.add_class("server-current")

        return ListItem(label, id=f"server-{index}")

    def _add_server_item(self, list_view: ListView, server: dict[str, Any], index: int) -> None:
        """Add a server item to the list view (for dynamic adding).

        Args:
            list_view: ListView to add to
            server: Server data dict
            index: Server index
        """
        item = self._create_server_item(server, index)
        list_view.mount(item)

    async def on_mount(self) -> None:
        """Load server configuration after mount."""
        logger.info("ServerManagementScreen.on_mount() called")

        # Get mounted widgets
        try:
            self._server_list = self.query_one("#server-list", ListView)
            self._form_container = self.query_one("#form-container", Vertical)
            logger.info("Retrieved server_list and form_container")
        except Exception as e:
            logger.error(f"Failed to query widgets: {e}")
            return

        # Create form widget with current server data
        await self._show_server_config(self._current_server_index)

        # Select first server
        if self._server_list:
            self._server_list.index = 0

    async def _show_server_config(self, server_index: int) -> None:
        """Show configuration form for selected server.

        Args:
            server_index: Index of server to show
        """
        if server_index < 0 or server_index >= len(self._servers):
            return

        server = self._servers[server_index]

        # Remove old form if exists
        if self._form_widget:
            await self._form_widget.remove()

        # Create new form with server data
        self._form_widget = FormWidget(
            fields=SERVER_FIELDS,
            initial_values=server,
            id="server-form",
        )

        # Reset field navigation index when showing new server
        self._current_field_index = 0

        # Mount new form
        if self._form_container:
            await self._form_container.mount(self._form_widget)
            logger.info(f"Mounted form for server: {server['name']}")

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle server selection in list.

        Args:
            event: ListView selected event
        """
        if not event.item or not event.item.id:
            return

        # Extract server index from item id
        try:
            server_index = int(event.item.id.split("-")[1])
            self._current_server_index = server_index
            await self._show_server_config(server_index)
            logger.info(f"Selected server index: {server_index}")
        except (IndexError, ValueError) as e:
            logger.error(f"Failed to parse server index: {e}")

    def action_add_server(self) -> None:
        """Add a new server."""
        # Create new server with defaults
        new_server = {
            "name": f"Server {len(self._servers) + 1}",
            "url": "http://localhost:6800/jsonrpc",
            "protocol": "auto",
            "secret": "",
            "username": "",
            "password": "",
            "timeout": "30",
            "is_current": False,
        }

        # Add to local list
        self._servers.append(new_server)
        new_index = len(self._servers) - 1

        # Add to service layer and save order
        self.service.add_server(
            name=new_server["name"],
            url=new_server["url"],
            secret=new_server.get("secret") or None,
        )
        # Save the complete order (ensures new server is at correct position)
        self._save_server_order()

        # Add to list view
        if self._server_list:
            self._add_server_item(self._server_list, new_server, new_index)
            self._server_list.index = new_index

        logger.info(f"Added new server: {new_server['name']}")

    def action_delete_server(self) -> None:
        """Delete the currently selected server."""
        if len(self._servers) <= 1:
            logger.warning("Cannot delete last server")
            if command_bar := self.query_one("#command-bar", CommandBar):
                command_bar.show_message("✗ Cannot delete last server")
            return

        if 0 <= self._current_server_index < len(self._servers):
            deleted_server = self._servers.pop(self._current_server_index)

            # Remove from service layer
            self.service.remove_server(deleted_server["name"])
            # Save updated order
            self._save_server_order()

            logger.info(f"Deleted server: {deleted_server['name']}")

            # Select previous server
            self._current_server_index = max(0, self._current_server_index - 1)

            # Refresh list view
            self.run_worker(self._refresh_server_list(), exclusive=False)

            if command_bar := self.query_one("#command-bar", CommandBar):
                command_bar.show_message(f"✓ Deleted server '{deleted_server['name']}'")

    def action_move_server_up(self) -> None:
        """Move the currently selected server up in the list."""
        if len(self._servers) <= 1:
            return  # Can't move if only one server

        current_idx = self._current_server_index
        if current_idx <= 0:
            # Already at top
            try:
                if command_bar := self.query_one("#command-bar", CommandBar):
                    command_bar.show_message("Already at top")
            except Exception:
                pass  # No command bar in test environment
            return

        # Swap with previous server
        self._servers[current_idx], self._servers[current_idx - 1] = (
            self._servers[current_idx - 1],
            self._servers[current_idx],
        )
        self._current_server_index = current_idx - 1

        # Save updated order to config
        self._save_server_order()

        # Refresh list (only if mounted)
        if self.is_mounted:
            self.run_worker(self._refresh_server_list(), exclusive=False)

        logger.info(f"Moved server up: {self._servers[self._current_server_index]['name']}")

    def action_move_server_down(self) -> None:
        """Move the currently selected server down in the list."""
        if len(self._servers) <= 1:
            return  # Can't move if only one server

        current_idx = self._current_server_index
        if current_idx >= len(self._servers) - 1:
            # Already at bottom
            try:
                if command_bar := self.query_one("#command-bar", CommandBar):
                    command_bar.show_message("Already at bottom")
            except Exception:
                pass  # No command bar in test environment
            return

        # Swap with next server
        self._servers[current_idx], self._servers[current_idx + 1] = (
            self._servers[current_idx + 1],
            self._servers[current_idx],
        )
        self._current_server_index = current_idx + 1

        # Save updated order to config
        self._save_server_order()

        # Refresh list (only if mounted)
        if self.is_mounted:
            self.run_worker(self._refresh_server_list(), exclusive=False)

        logger.info(f"Moved server down: {self._servers[self._current_server_index]['name']}")

    def _save_server_order(self) -> None:
        """Save the current server order to configuration."""
        # Get config and update servers list in order
        config = self.service.config_mgr.get()
        config.servers = [
            {
                "name": server["name"],
                "url": server["url"],
                "secret": server.get("secret") or None,
            }
            for server in self._servers
        ]
        self.service.config_mgr.save()
        logger.debug("Server order saved to config")

    async def _refresh_server_list(self) -> None:
        """Refresh the server list display."""
        if not self._server_list:
            return

        # Clear existing items
        await self._server_list.clear()

        # Re-add all servers
        for idx, server in enumerate(self._servers):
            self._add_server_item(self._server_list, server, idx)

        # Select current server
        if 0 <= self._current_server_index < len(self._servers):
            self._server_list.index = self._current_server_index
            await self._show_server_config(self._current_server_index)

    def on_key(self, event) -> None:
        """Global keyboard event handler for unified navigation.

        Handles:
        - t/T: Switch left panel servers (VIEW mode, global)
        - j/k: Navigate right panel form fields (VIEW mode, global)
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
                event.stop()  # Stop event propagation completely to prevent action_handle_escape
                logger.info("Exited EDIT mode")
            return

        # VIEW mode: Handle global navigation keys
        if key == "t":
            # Next server (global, regardless of focus)
            self._cycle_server(1)
            event.prevent_default()
        elif key == "T":
            # Previous server (global, regardless of focus)
            self._cycle_server(-1)
            event.prevent_default()
        elif key == "j":
            # Next field in current form (global)
            self._navigate_field(1)
            event.prevent_default()
        elif key == "k":
            # Previous field in current form (global)
            self._navigate_field(-1)
            event.prevent_default()

    def _cycle_server(self, direction: int) -> None:
        """Cycle through servers in left panel.

        Args:
            direction: 1 for next, -1 for previous
        """
        if not self._server_list or not self._servers:
            return

        # Calculate new index (wrap around)
        new_index = (self._current_server_index + direction) % len(self._servers)

        # Update current index
        self._current_server_index = new_index

        # Update ListView selection
        self._server_list.index = new_index

        # Show the new server's configuration
        self.run_worker(self._show_server_config(new_index), exclusive=False)
        logger.info(f"Cycled to server index: {new_index}")

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

    def _validate_server_config(
        self, values: dict[str, Any], current_index: int
    ) -> tuple[bool, str | None]:
        """Validate server configuration.

        Args:
            values: Server configuration values
            current_index: Index of server being edited

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate URL format
        url = values.get("url", "").strip()
        if not url:
            return False, "URL is required"

        # Check URL scheme
        valid_schemes = ("http://", "https://", "ws://", "wss://")
        if not any(url.startswith(scheme) for scheme in valid_schemes):
            return (
                False,
                "URL must start with http://, https://, ws://, or wss://",
            )

        # Validate URL format using urlparse
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            if not parsed.hostname:
                return False, "Invalid URL format (missing hostname)"
        except Exception as e:
            return False, f"Invalid URL format: {e}"

        # Check for duplicate server names (excluding current server)
        name = values.get("name", "").strip()
        if not name:
            return False, "Server name is required"

        for idx, server in enumerate(self._servers):
            if idx != current_index and server["name"] == name:
                return False, f"Server name '{name}' already exists"

        return True, None

    def action_save_server(self) -> None:
        """Save current server configuration."""
        if not self._form_widget:
            return

        # Get values from form
        values = self._form_widget.get_values()

        # Validate required fields (FormWidget validation)
        is_valid, errors = self._form_widget.validate_all()
        if not is_valid:
            logger.warning(f"Validation failed: {errors}")
            if command_bar := self.query_one("#command-bar", CommandBar):
                error_msg = ", ".join(errors.values())
                command_bar.show_message(f"✗ Validation failed: {error_msg}")
            return

        # Additional server-specific validation
        is_valid, error_msg = self._validate_server_config(values, self._current_server_index)
        if not is_valid:
            logger.warning(f"Server validation failed: {error_msg}")
            if command_bar := self.query_one("#command-bar", CommandBar):
                command_bar.show_message(f"✗ {error_msg}")
            return

        # Update server data
        if 0 <= self._current_server_index < len(self._servers):
            old_server = self._servers[self._current_server_index].copy()
            self._servers[self._current_server_index].update(values)

            try:
                # If name changed, need to remove old and add new to service layer
                if old_server["name"] != values.get("name"):
                    self.service.remove_server(old_server["name"])
                    self.service.add_server(
                        name=values["name"],
                        url=values["url"],
                        secret=values.get("secret") or None,
                    )
                else:
                    # Just update the existing server in service layer
                    # Remove and re-add to update all fields
                    self.service.remove_server(values["name"])
                    self.service.add_server(
                        name=values["name"],
                        url=values["url"],
                        secret=values.get("secret") or None,
                    )

                # Save order to ensure position is maintained
                self._save_server_order()

                logger.info(f"Saved server: {values.get('name', 'Unknown')}")

                if command_bar := self.query_one("#command-bar", CommandBar):
                    command_bar.show_message(f"✓ Saved server '{values['name']}'")

                # Refresh list to show updated name
                self.run_worker(self._refresh_server_list(), exclusive=False)

            except Exception as e:
                logger.error(f"Failed to save server: {e}")
                if command_bar := self.query_one("#command-bar", CommandBar):
                    command_bar.show_message(f"✗ Failed to save: {e}")

    def action_quit(self) -> None:
        """Quit and close screen."""
        self.dismiss(None)

    def action_test_connection(self) -> None:
        """Test connection to selected server."""

        async def _test_connection() -> None:
            """Async connection test."""
            if 0 <= self._current_server_index < len(self._servers):
                server = self._servers[self._current_server_index]

                # Import here to avoid circular dependency
                import asyncio

                from aria2rpc import Aria2Client
                from aria2rpc.websocket import WebSocketRPCClient

                try:
                    # Show testing message
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.update(f"Testing connection to {server['name']}...")

                    # Create temporary client for testing
                    client = Aria2Client(server["url"], secret=server.get("secret") or None)

                    # For WebSocket, explicitly connect
                    if isinstance(client, WebSocketRPCClient):
                        await asyncio.wait_for(
                            client.connect(), timeout=int(server.get("timeout", 30))
                        )

                    # Test with get_version
                    version = await asyncio.wait_for(
                        client.get_version(), timeout=int(server.get("timeout", 30))
                    )

                    # Cleanup WebSocket connection
                    if isinstance(client, WebSocketRPCClient):
                        await client.close()

                    # Show success message
                    protocol_type = (
                        "WebSocket" if isinstance(client, WebSocketRPCClient) else "HTTP"
                    )
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(
                            f"✓ Connected successfully! ({protocol_type}, aria2 {version.version})"
                        )

                    logger.info(f"Connection test successful: {server['name']} ({protocol_type})")

                except TimeoutError:
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message("✗ Connection timeout")
                    logger.error(f"Connection timeout: {server['name']}")

                except Exception as e:
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ Connection failed: {str(e)}")
                    logger.error(f"Connection test failed: {server['name']}, error: {e}")

        self.run_worker(_test_connection(), exclusive=False)

    def action_set_current_server(self) -> None:
        """Set the selected server as current and switch to it."""

        async def _switch_server() -> None:
            """Async server switching."""
            if 0 <= self._current_server_index < len(self._servers):
                new_current_server = self._servers[self._current_server_index]

                # Update is_current flag for all servers
                for server in self._servers:
                    server["is_current"] = False
                new_current_server["is_current"] = True

                logger.info(f"Switching to server: {new_current_server['name']}")

                try:
                    # Show switching message
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.update(f"Switching to {new_current_server['name']}...")

                    # Switch server through service layer (handles disconnect/connect/config)
                    success = await self.service.switch_server(new_current_server["name"])

                    if success:
                        # Refresh server list to update current indicator
                        await self._refresh_server_list()

                        # Show success message
                        if command_bar := self.query_one("#command-bar", CommandBar):
                            command_bar.show_message(f"✓ Switched to {new_current_server['name']}")

                        logger.info(f"Successfully switched to: {new_current_server['name']}")
                    else:
                        # Switch failed, restore previous current server
                        new_current_server["is_current"] = False
                        if command_bar := self.query_one("#command-bar", CommandBar):
                            command_bar.show_message(
                                f"✗ Failed to connect to {new_current_server['name']}"
                            )
                        logger.error(f"Failed to switch to: {new_current_server['name']}")

                except Exception as e:
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ Switch failed: {str(e)}")
                    logger.error(f"Server switch error: {e}")

        self.run_worker(_switch_server(), exclusive=False)

    def action_start_local_process(self) -> None:
        """Start local aria2c process for selected server."""

        async def _start_process() -> None:
            """Async process start."""
            if 0 <= self._current_server_index < len(self._servers):
                server = self._servers[self._current_server_index]
                server_name = server["name"]

                # Check if it's a local server
                if not server.get("is_local", False):
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ {server_name} is not a local server")
                    return

                # Check if already running
                if self.service.process_mgr.is_running(server_name):
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ Process already running for {server_name}")
                    return

                logger.info(f"Starting local process for: {server_name}")

                try:
                    # Show starting message
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.update(f"Starting aria2c for {server_name}...")

                    # Get server config
                    config = self.service.rpc_mgr.get_server_config(server_name)

                    # Extract port from URL
                    from urllib.parse import urlparse

                    parsed = urlparse(config.url)
                    port = parsed.port or 6800

                    # Start the process
                    success = await self.service.process_mgr.start_process(
                        server_name=config.name,
                        aria2c_path=config.aria2c_path,
                        rpc_port=port,
                        rpc_secret=config.secret,
                        session_file=config.managed_session_file,
                        options=config.aria2c_options,
                    )

                    if success:
                        # Refresh server list to update process status
                        await self._refresh_server_list()

                        # Show success message
                        if command_bar := self.query_one("#command-bar", CommandBar):
                            command_bar.show_message(f"✓ Started aria2c for {server_name}")

                        logger.info(f"Successfully started process: {server_name}")
                    else:
                        if command_bar := self.query_one("#command-bar", CommandBar):
                            command_bar.show_message(f"✗ Failed to start process for {server_name}")
                        logger.error(f"Failed to start process: {server_name}")

                except Exception as e:
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ Start failed: {str(e)}")
                    logger.error(f"Process start error: {e}")

        self.run_worker(_start_process(), exclusive=False)

    def action_stop_local_process(self) -> None:
        """Stop local aria2c process for selected server."""

        async def _stop_process() -> None:
            """Async process stop."""
            if 0 <= self._current_server_index < len(self._servers):
                server = self._servers[self._current_server_index]
                server_name = server["name"]

                # Check if it's a local server
                if not server.get("is_local", False):
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ {server_name} is not a local server")
                    return

                # Check if running
                if not self.service.process_mgr.is_running(server_name):
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ Process not running for {server_name}")
                    return

                logger.info(f"Stopping local process for: {server_name}")

                try:
                    # Show stopping message
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.update(f"Stopping aria2c for {server_name}...")

                    # Stop the process (graceful)
                    success = await self.service.stop_local_process(server_name, force=False)

                    if success:
                        # Refresh server list to update process status
                        await self._refresh_server_list()

                        # Show success message
                        if command_bar := self.query_one("#command-bar", CommandBar):
                            command_bar.show_message(f"✓ Stopped aria2c for {server_name}")

                        logger.info(f"Successfully stopped process: {server_name}")
                    else:
                        if command_bar := self.query_one("#command-bar", CommandBar):
                            command_bar.show_message(f"✗ Failed to stop process for {server_name}")
                        logger.error(f"Failed to stop process: {server_name}")

                except Exception as e:
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ Stop failed: {str(e)}")
                    logger.error(f"Process stop error: {e}")

        self.run_worker(_stop_process(), exclusive=False)

    def action_restart_local_process(self) -> None:
        """Restart local aria2c process for selected server."""

        async def _restart_process() -> None:
            """Async process restart."""
            if 0 <= self._current_server_index < len(self._servers):
                server = self._servers[self._current_server_index]
                server_name = server["name"]

                # Check if it's a local server
                if not server.get("is_local", False):
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ {server_name} is not a local server")
                    return

                logger.info(f"Restarting local process for: {server_name}")

                try:
                    # Show restarting message
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.update(f"Restarting aria2c for {server_name}...")

                    # Restart the process
                    success = await self.service.restart_local_process(server_name)

                    if success:
                        # Refresh server list to update process status
                        await self._refresh_server_list()

                        # Show success message
                        if command_bar := self.query_one("#command-bar", CommandBar):
                            command_bar.show_message(f"✓ Restarted aria2c for {server_name}")

                        logger.info(f"Successfully restarted process: {server_name}")
                    else:
                        if command_bar := self.query_one("#command-bar", CommandBar):
                            command_bar.show_message(
                                f"✗ Failed to restart process for {server_name}"
                            )
                        logger.error(f"Failed to restart process: {server_name}")

                except Exception as e:
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message(f"✗ Restart failed: {str(e)}")
                    logger.error(f"Process restart error: {e}")

        self.run_worker(_restart_process(), exclusive=False)

    def action_save_session(self) -> None:
        """Save current session to file."""

        async def _save_session() -> None:
            """Async session save."""
            try:
                # Show saving message
                if command_bar := self.query_one("#command-bar", CommandBar):
                    command_bar.update("Saving session...")

                # Save session
                success = await self.service.save_session()

                if success:
                    # Show success message
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message("✓ Session saved successfully")

                    logger.info("Session saved successfully")
                else:
                    if command_bar := self.query_one("#command-bar", CommandBar):
                        command_bar.show_message("✗ Failed to save session")
                    logger.error("Failed to save session")

            except Exception as e:
                if command_bar := self.query_one("#command-bar", CommandBar):
                    command_bar.show_message(f"✗ Save session failed: {str(e)}")
                logger.error(f"Session save error: {e}")

        self.run_worker(_save_session(), exclusive=False)
