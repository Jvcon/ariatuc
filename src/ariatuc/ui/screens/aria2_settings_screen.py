"""Aria2 global configuration settings screen."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static

from ariatuc.ui.widgets.aria2_field_definitions import (
    ARIA2_FIELDS_ADVANCED,
    ARIA2_FIELDS_BASIC,
    ARIA2_FIELDS_BITTORRENT,
    ARIA2_FIELDS_FTP_SFTP,
    ARIA2_FIELDS_HTTP,
    ARIA2_FIELDS_HTTP_FTP_SFTP,
    ARIA2_FIELDS_METALINK,
    ARIA2_FIELDS_RPC,
)
from ariatuc.ui.widgets.command_bar import CommandBar
from ariatuc.ui.widgets.form_widget import FormWidget

if TYPE_CHECKING:
    from ariatuc.core.service import Aria2Service

logger = logging.getLogger(__name__)


class Aria2SettingsScreen(ModalScreen[dict[str, Any] | None]):
    """Aria2 global settings configuration screen.

    Layout: 20% section list + 80% form
    ┌────────────────────────────────────────┐
    │ Aria2 Settings                         │
    ├──────────┬─────────────────────────────┤
    │ Sections │ Configuration Form          │
    │ (20%)    │ (80%)                       │
    │          │                             │
    │ • Basic  │ [FormWidget with scroll]    │
    │   HTTP   │                             │
    │   FTP    │                             │
    │   BitTor │                             │
    │   Advanc │                             │
    │          │                             │
    │          │ [Save] [Reset] [Cancel]     │
    └──────────┴─────────────────────────────┘

    Sections:
    - Basic: Download directory, concurrent downloads, integrity check
    - HTTP/FTP/SFTP: Common protocol options (proxy, timeout, retry, split)
    - HTTP: HTTP-specific authentication, headers, cookies
    - FTP/SFTP: FTP/SFTP authentication and options
    - BitTorrent: DHT, peers, seeding, trackers, encryption
    - Metalink: Metalink processing and preferences
    - RPC: RPC-specific options
    - Advanced: Speed limits, disk cache, logging, file management

    Returns:
        Dict of changed options, or None if cancelled
    """

    DEFAULT_CSS = """
    Aria2SettingsScreen {
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

    /* Section list panel (left, 1fr = 20% width) */
    #section-list-panel {
        border: solid $primary;
        width: 100%;
        height: 100%;
    }

    #section-list-title {
        dock: top;
        height: 1;
        text-style: bold;
        background: $primary;
        color: $text;
        content-align: left middle;
        padding: 0 1;
    }

    #section-list {
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

    /* Section list items */
    #section-list > ListItem {
        padding: 0 1;
        height: 1;
    }

    #section-list > ListItem:hover {
        background: $primary-darken-2;
    }

    #section-list > ListItem > Label {
        width: 100%;
    }
    """

    BINDINGS = [
        ("escape", "handle_escape", "Cancel"),
        ("ctrl+s", "save", "Save"),
        ("i", "enter_edit_mode", "Edit"),
        ("w", "save", "Save"),
    ]

    # Section definitions matching AriaNg structure
    SECTIONS = [
        ("basic", "Basic"),
        ("http_ftp_sftp", "HTTP/FTP/SFTP"),
        ("http", "HTTP"),
        ("ftp_sftp", "FTP/SFTP"),
        ("bittorrent", "BitTorrent"),
        ("metalink", "Metalink"),
        ("rpc", "RPC"),
        ("advanced", "Advanced"),
    ]

    def __init__(
        self,
        service: Aria2Service,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize aria2 settings screen.

        Args:
            service: Aria2Service instance
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service = service
        self._form_widgets: dict[str, FormWidget] = {}
        self._initial_options: dict[str, Any] = {}
        self._current_section = "basic"
        self._section_list: ListView | None = None
        self._form_container: Vertical | None = None

        # VIEW/EDIT mode tracking
        self._mode = "VIEW"  # "VIEW" or "EDIT"
        self._current_field_index = 0  # Track current field in VIEW mode navigation

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        # Title bar at top (like StatusBar)
        yield Static("Aria2 Settings", id="title")

        # Main content area with two panels
        with Horizontal(id="main-content"):
            # Left panel: Section list (2fr, matching download-list)
            with Vertical(id="section-list-panel"):
                yield Static("Sections", id="section-list-title")
                # Create ListView with section items
                with ListView(id="section-list") as section_list:
                    for section_id, section_name in self.SECTIONS:
                        item = ListItem(Label(section_name), id=f"section-{section_id}")
                        yield item
                self._section_list = section_list

            # Right panel: Form (1fr, matching download-detail)
            with Vertical(id="form-panel"):
                self._form_container = Vertical(id="form-container")
                # Initial form will be added in on_mount
                yield self._form_container

        # Command bar at bottom (reuse existing widget)
        command_bar = CommandBar(id="command-bar")
        command_bar.update("ctrl+s-Save | Esc-Cancel | ↑↓-Navigate")
        yield command_bar

    async def on_mount(self) -> None:
        """Load options from aria2 after mount."""
        logger.info("Aria2SettingsScreen.on_mount() called")

        # Get mounted widgets via query_one
        try:
            self._section_list = self.query_one("#section-list", ListView)
            self._form_container = self.query_one("#form-container", Vertical)
            logger.info("Retrieved section_list and form_container via query_one")
            logger.info(f"Section list has {len(list(self._section_list.children))} items")
        except Exception as e:
            logger.error(f"Failed to query widgets: {e}")
            return

        try:
            # Fetch current global options from aria2
            logger.info("Fetching global options from aria2")
            try:
                self._initial_options = await self.service.get_global_options()
                logger.info(f"Got {len(self._initial_options)} options from aria2")
            except Exception as e:
                # If fetching fails (e.g., not connected), use empty dict
                # Forms will fall back to field defaults
                logger.warning(f"Failed to fetch options from aria2: {e}")
                self._initial_options = {}

            # Create all form widgets
            logger.info(f"Creating form for 'basic' with {len(ARIA2_FIELDS_BASIC)} fields")
            self._form_widgets["basic"] = FormWidget(
                fields=ARIA2_FIELDS_BASIC,
                initial_values=self._initial_options,
                id="form-basic",
            )

            logger.info(
                f"Creating form for 'http_ftp_sftp' with {len(ARIA2_FIELDS_HTTP_FTP_SFTP)} fields"
            )
            self._form_widgets["http_ftp_sftp"] = FormWidget(
                fields=ARIA2_FIELDS_HTTP_FTP_SFTP,
                initial_values=self._initial_options,
                id="form-http-ftp-sftp",
            )

            logger.info(f"Creating form for 'http' with {len(ARIA2_FIELDS_HTTP)} fields")
            self._form_widgets["http"] = FormWidget(
                fields=ARIA2_FIELDS_HTTP,
                initial_values=self._initial_options,
                id="form-http",
            )

            logger.info(f"Creating form for 'ftp_sftp' with {len(ARIA2_FIELDS_FTP_SFTP)} fields")
            self._form_widgets["ftp_sftp"] = FormWidget(
                fields=ARIA2_FIELDS_FTP_SFTP,
                initial_values=self._initial_options,
                id="form-ftp-sftp",
            )

            logger.info(
                f"Creating form for 'bittorrent' with {len(ARIA2_FIELDS_BITTORRENT)} fields"
            )
            self._form_widgets["bittorrent"] = FormWidget(
                fields=ARIA2_FIELDS_BITTORRENT,
                initial_values=self._initial_options,
                id="form-bittorrent",
            )

            logger.info(f"Creating form for 'metalink' with {len(ARIA2_FIELDS_METALINK)} fields")
            self._form_widgets["metalink"] = FormWidget(
                fields=ARIA2_FIELDS_METALINK,
                initial_values=self._initial_options,
                id="form-metalink",
            )

            logger.info(f"Creating form for 'rpc' with {len(ARIA2_FIELDS_RPC)} fields")
            self._form_widgets["rpc"] = FormWidget(
                fields=ARIA2_FIELDS_RPC,
                initial_values=self._initial_options,
                id="form-rpc",
            )

            logger.info(f"Creating form for 'advanced' with {len(ARIA2_FIELDS_ADVANCED)} fields")
            self._form_widgets["advanced"] = FormWidget(
                fields=ARIA2_FIELDS_ADVANCED,
                initial_values=self._initial_options,
                id="form-advanced",
            )

            # Show initial section
            logger.info("Showing initial section: basic")
            await self._show_section("basic")

            # Select first item in list
            if self._section_list:
                self._section_list.index = 0
                logger.info("Selected first item in section list")

        except Exception as e:
            # If loading fails, forms will use defaults
            logger.error(f"Error in on_mount: {e}", exc_info=True)

    async def _show_section(self, section_id: str) -> None:
        """Show the form for a specific section.

        Args:
            section_id: Section identifier (basic, http_ftp_sftp, http, ftp_sftp, bittorrent, metalink, rpc, advanced)
        """
        logger.info(f"_show_section called with section_id={section_id}")

        if not self._form_container:
            logger.warning("form_container is None")
            return

        self._current_section = section_id
        form = self._form_widgets.get(section_id)
        if not form:
            logger.warning(f"No form found for section {section_id}")
            return

        logger.info(f"Found form for {section_id}, clearing current content")
        # Clear current content
        await self._form_container.remove_children()

        # Reset field navigation index when showing new section
        self._current_field_index = 0

        # Mount new form
        logger.info(f"Mounting form for {section_id}")
        await self._form_container.mount(form)
        logger.info(f"Form mounted successfully for {section_id}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle section selection.

        Args:
            event: List view selected event
        """
        # Extract section ID from list item ID
        item_id = event.item.id
        if item_id and item_id.startswith("section-"):
            section_id = item_id.replace("section-", "")
            self.run_worker(self._show_section(section_id))

    async def action_save(self) -> None:
        """Save all changed options to aria2."""
        # Validate all forms
        all_valid = True
        for form in self._form_widgets.values():
            is_valid, _ = form.validate_all()
            if not is_valid:
                all_valid = False

        if not all_valid:
            return

        # Collect all changed values across all sections
        # aria2rpc will handle type conversion automatically
        all_changes = {}
        for form in self._form_widgets.values():
            all_changes.update(form.get_changed_values())

        if all_changes:
            try:
                # Apply changes to aria2 via RPC
                # aria2rpc automatically converts Python types to aria2 string format
                logger.info(f"Saving {len(all_changes)} changed options to aria2: {all_changes}")
                await self.service.change_global_option(all_changes)
                self.dismiss(all_changes)
            except Exception:
                # If save fails, stay in dialog
                pass
        else:
            self.dismiss({})

    def action_cancel(self) -> None:
        """Cancel without saving."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Global keyboard event handler for unified navigation.

        Handles:
        - t/T: Switch left panel sections (VIEW mode, global)
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
                event.prevent_default()
                logger.info("Exited EDIT mode")
            return

        # VIEW mode: Handle global navigation keys
        if key == "t":
            # Next section (global, regardless of focus)
            self._cycle_section(1)
            event.prevent_default()
        elif key == "T":
            # Previous section (global, regardless of focus)
            self._cycle_section(-1)
            event.prevent_default()
        elif key == "j":
            # Next field in current form (global)
            self._navigate_field(1)
            event.prevent_default()
        elif key == "k":
            # Previous field in current form (global)
            self._navigate_field(-1)
            event.prevent_default()

    def _cycle_section(self, direction: int) -> None:
        """Cycle through sections in left panel.

        Args:
            direction: 1 for next, -1 for previous
        """
        if not self._section_list or not self.SECTIONS:
            return

        # Find current section index
        current_idx = next(
            (
                i
                for i, (section_id, _) in enumerate(self.SECTIONS)
                if section_id == self._current_section
            ),
            0,
        )

        # Calculate new index (wrap around)
        new_idx = (current_idx + direction) % len(self.SECTIONS)
        new_section_id = self.SECTIONS[new_idx][0]

        # Update ListView selection
        self._section_list.index = new_idx

        # Show new section
        self.run_worker(self._show_section(new_section_id))
        logger.info(f"Cycled to section: {new_section_id}")

    def _navigate_field(self, direction: int) -> None:
        """Navigate form fields in VIEW mode (highlight field for visual feedback).

        Args:
            direction: 1 for next, -1 for previous
        """
        current_form = self._form_widgets.get(self._current_section)
        if not current_form:
            return

        # Get ordered list of field keys
        field_keys = current_form.get_field_keys()
        if not field_keys:
            return

        # Update field index (wrap around)
        self._current_field_index = (self._current_field_index + direction) % len(field_keys)

        # Highlight the field at current index
        current_field_key = field_keys[self._current_field_index]
        current_form.highlight_field(current_field_key)
        logger.debug(
            f"Navigated to field: {current_field_key} (index: {self._current_field_index})"
        )

    def action_enter_edit_mode(self) -> None:
        """Enter EDIT mode by focusing on first form field."""
        current_form = self._form_widgets.get(self._current_section)
        if not current_form:
            return

        # Clear VIEW mode highlights
        current_form.clear_highlight()

        # Focus on the first editable field
        for field_widget in current_form.field_widgets.values():
            if hasattr(field_widget, "focus") and not field_widget.disabled:
                field_widget.focus()
                self._mode = "EDIT"
                logger.info("Entered EDIT mode")
                break

    def action_handle_escape(self) -> None:
        """Handle Escape key - exit EDIT mode or cancel."""
        if self._mode == "EDIT":
            # Blur focused field and return to VIEW mode
            self.set_focus(None)
            self._mode = "VIEW"
            logger.info("Exited EDIT mode via action")
        else:
            # VIEW mode: cancel and close
            self.action_cancel()
