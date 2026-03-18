"""Main screen displaying download list and details."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.dom import DOMNode
from textual.screen import Screen

from ariatuc.ui.keybinding_manager import (
    Keybinding,
    KeybindingContext,
    KeybindingManager,
    KeybindingMode,
)
from ariatuc.ui.screens.app_settings_screen import AppSettingsScreen
from ariatuc.ui.screens.aria2_settings_screen import Aria2SettingsScreen
from ariatuc.ui.screens.help_screen import HelpScreen
from ariatuc.ui.widgets.add_download_dialog import AddDownloadDialog
from ariatuc.ui.widgets.command_bar import CommandBar
from ariatuc.ui.widgets.confirm_dialog import ConfirmDialog, MessageDialog
from ariatuc.ui.widgets.download_detail import DownloadDetailWidget
from ariatuc.ui.widgets.download_list import DownloadListWidget
from ariatuc.ui.widgets.status_bar import StatusBar

if TYPE_CHECKING:
    from ariatuc.core.service import Aria2Service

logger = logging.getLogger(__name__)


class MainScreen(Screen):
    """Main application screen with download list and details.

    Layout:
    ┌────────────────────────────────────────┐
    │ StatusBar                              │
    ├────────────────────────────────────────┤
    │ ┌──────────────┬────────────────────┐  │
    │ │DownloadList  │DownloadDetail      │  │
    │ │(主要区域)    │(次要区域，可折叠) │  │
    │ └──────────────┴────────────────────┘  │
    ├────────────────────────────────────────┤
    │ CommandBar                             │
    └────────────────────────────────────────┘

    Keyboard shortcuts:
    - a: Add download
    - d: Delete download
    - p: Pause/resume download
    - P: Pause all downloads
    - u: Resume download
    - U: Resume all downloads
    - r: Refresh
    - gs: Open server settings screen
    - ga: Open aria2 settings screen
    - gg: Open app settings screen
    - ?: Show help
    - q: Quit application
    """

    DEFAULT_CSS = """
    MainScreen {
        background: $surface;
    }

    #main-content {
        height: 1fr;
        layout: grid;
        grid-size: 2;
        grid-columns: 2fr 1fr;
    }

    #download-list-panel {
        border: solid $primary;
        width: 100%;
        height: 100%;
    }

    #download-detail-panel {
        border: solid $primary;
        width: 100%;
        height: 100%;
        margin-left: 1;
    }

    /* Visual feedback for focused panel - keep border width same, only change color */
    #download-list-panel:focus-within {
        border: solid $accent;  /* Changed from 'thick' to 'solid' to prevent layout shift */
    }

    #download-detail-panel:focus-within {
        border: solid $accent;  /* Changed from 'thick' to 'solid' to prevent layout shift */
    }

    .panel-title {
        background: $primary;
        color: $text;
        padding: 0 1;
        text-style: bold;
    }

    .panel-content {
        padding: 1;
    }
    """

    BINDINGS = [
        ("a", "add_download", "Add"),
        ("d", "delete_download", "Delete"),
        ("p", "pause_download", "Pause"),
        ("P", "pause_all", "Pause All"),
        ("u", "resume_download", "Resume"),
        ("U", "resume_all", "Resume All"),
        ("r", "refresh", "Refresh"),
        # Settings are now accessed via g* combinations (gs/ga/gg)
        # Handled in on_key() method
        ("?", "help", "Help"),
        ("q", "quit", "Quit"),
        ("tab", "toggle_focus", "Toggle Focus"),
        ("enter", "toggle_preview", "Toggle Preview"),
        # Panel navigation
        ("H", "focus_left_panel", "Focus List"),
        ("L", "focus_right_panel", "Focus Detail"),
    ]

    def __init__(
        self,
        service: Aria2Service | None = None,
        keybinding_manager: KeybindingManager | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize main screen.

        Args:
            service: Aria2Service instance
            keybinding_manager: Keybinding manager instance
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service = service
        self.keybinding_manager = keybinding_manager or KeybindingManager()
        self._status_bar: StatusBar | None = None
        self._command_bar: CommandBar | None = None
        self._download_list: DownloadListWidget | None = None
        self._download_detail: DownloadDetailWidget | None = None
        self._detail_visible = True
        self._preview_mode = False  # Track if preview mode is active
        self._pending_g_key = False  # Track if waiting for g* combination

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Status bar at top
        self._status_bar = StatusBar(self.service, id="status-bar")
        yield self._status_bar

        # Main content area with two panels
        with Horizontal(id="main-content"):
            # Download list panel (left side, main area)
            self._download_list = DownloadListWidget(
                self.service,
                self.keybinding_manager,
                id="download-list-panel",
            )
            yield self._download_list

            # Download detail panel (right side, secondary area)
            self._download_detail = DownloadDetailWidget(
                self.service,
                id="download-detail-panel",
            )
            yield self._download_detail

        # Command bar at bottom
        self._command_bar = CommandBar(self.keybinding_manager, id="command-bar")
        yield self._command_bar

    def on_mount(self) -> None:
        """Set up after mounting."""
        if self.service and self._status_bar:
            self._status_bar.set_service(self.service)
        if self.service and self._download_list:
            self._download_list.set_service(self.service)
        if self.service and self._download_detail:
            self._download_detail.set_service(self.service)

        # Register keybindings with manager
        self._register_keybindings()

        # Initialize command bar hints
        if self._command_bar:
            self._command_bar.update_hints(KeybindingContext.MAIN_SCREEN, KeybindingMode.NORMAL)

    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        """Handle focus changes to update command bar hints.

        Args:
            event: Focus event
        """
        from textual.widgets import Input, TextArea

        focused = event.widget

        # Determine context based on focused widget
        if isinstance(focused, DownloadListWidget):
            context = KeybindingContext.DOWNLOAD_LIST
        elif isinstance(focused, DownloadDetailWidget):
            context = KeybindingContext.DOWNLOAD_DETAIL
        elif isinstance(focused, (Input, TextArea)):
            # In edit mode
            self.keybinding_manager.set_mode(KeybindingMode.EDIT)
            if self._command_bar:
                self._command_bar.update_hints(KeybindingContext.MAIN_SCREEN, KeybindingMode.EDIT)
            return
        else:
            context = KeybindingContext.MAIN_SCREEN

        # Update context and command bar
        self.keybinding_manager.set_context(context)
        if self._command_bar:
            self._command_bar.update_hints(context, self.keybinding_manager.current_mode)

    def _register_keybindings(self) -> None:
        """Register all main screen keybindings with the manager."""
        kb = self.keybinding_manager

        # Global bindings (available everywhere)
        kb.register(Keybinding("q", "quit", "Quit", KeybindingContext.GLOBAL))
        kb.register(Keybinding("?", "help", "Help", KeybindingContext.GLOBAL))
        kb.register(Keybinding("escape", "escape", "Esc", KeybindingContext.GLOBAL))

        # Main screen bindings
        kb.register(Keybinding("a", "add_download", "Add", KeybindingContext.MAIN_SCREEN))
        kb.register(Keybinding("d", "delete_download", "Delete", KeybindingContext.MAIN_SCREEN))
        kb.register(Keybinding("p", "pause_download", "Pause", KeybindingContext.MAIN_SCREEN))
        kb.register(Keybinding("P", "pause_all", "Pause All", KeybindingContext.MAIN_SCREEN))
        kb.register(Keybinding("u", "resume_download", "Resume", KeybindingContext.MAIN_SCREEN))
        kb.register(Keybinding("U", "resume_all", "Resume All", KeybindingContext.MAIN_SCREEN))
        kb.register(Keybinding("r", "refresh", "Refresh", KeybindingContext.MAIN_SCREEN))
        kb.register(
            Keybinding(
                "enter",
                "toggle_preview",
                "Preview",
                KeybindingContext.MAIN_SCREEN,
            )
        )

        # Tab switching (global for left panel)
        kb.register(
            Keybinding(
                "1",
                "switch_tab_active",
                "Active",
                KeybindingContext.MAIN_SCREEN,
                priority=10,
            )
        )
        kb.register(
            Keybinding(
                "2",
                "switch_tab_waiting",
                "Waiting",
                KeybindingContext.MAIN_SCREEN,
                priority=10,
            )
        )
        kb.register(
            Keybinding(
                "3",
                "switch_tab_stopped",
                "Stopped",
                KeybindingContext.MAIN_SCREEN,
                priority=10,
            )
        )

        # Context-sensitive tab cycling (handled in on_key based on focus)
        kb.register(
            Keybinding(
                "t",
                "cycle_tab_forward",
                "Next Tab",
                KeybindingContext.MAIN_SCREEN,
            )
        )
        kb.register(
            Keybinding(
                "T",
                "cycle_tab_backward",
                "Prev Tab",
                KeybindingContext.MAIN_SCREEN,
            )
        )

        # Panel focus
        kb.register(
            Keybinding(
                "H",
                "focus_left_panel",
                "Focus List",
                KeybindingContext.MAIN_SCREEN,
            )
        )
        kb.register(
            Keybinding(
                "L",
                "focus_right_panel",
                "Focus Detail",
                KeybindingContext.MAIN_SCREEN,
            )
        )
        kb.register(
            Keybinding(
                "tab",
                "toggle_focus",
                "Toggle Focus",
                KeybindingContext.MAIN_SCREEN,
            )
        )

        # Navigation
        kb.register(Keybinding("j", "move_down", "Down", KeybindingContext.MAIN_SCREEN))
        kb.register(Keybinding("k", "move_up", "Up", KeybindingContext.MAIN_SCREEN))

        # Settings prefix 'g' (handled specially in on_key)
        # These are registered for documentation/hints but handled manually
        kb.register(
            Keybinding(
                "g,s",
                "open_servers",
                "Servers",
                KeybindingContext.MAIN_SCREEN,
            )
        )
        kb.register(
            Keybinding(
                "g,a",
                "aria2_settings",
                "Aria2",
                KeybindingContext.MAIN_SCREEN,
            )
        )
        kb.register(
            Keybinding(
                "g,g",
                "app_settings",
                "App",
                KeybindingContext.MAIN_SCREEN,
            )
        )

        # Set initial context
        kb.set_context(KeybindingContext.MAIN_SCREEN)
        kb.set_mode(KeybindingMode.NORMAL)

    def on_key(self, event: events.Key) -> None:
        """Intercept keys for global tab switching and preview mode.

        Handles tab switching globally regardless of which panel has focus.
        Keys: 1/2/3 (direct tab selection - global for left panel), t/T (cycle tabs within focused panel),
              Enter (toggle preview mode), g* (settings: gs/ga/gg)
        """
        # Don't intercept keys in edit mode
        if self.is_in_edit_mode():
            return

        key = event.key

        # Handle g* key combinations for settings
        if self._pending_g_key:
            # We're waiting for the second key after 'g'
            self._pending_g_key = False
            if key == "s":
                # gs - Server Settings
                self.action_open_servers()
                event.prevent_default()
                return
            if key == "a":
                # ga - Aria2 Settings
                self.action_aria2_settings()
                event.prevent_default()
                return
            if key == "g":
                # gg - App Settings
                self.action_app_settings()
                event.prevent_default()
                return
            # Invalid second key, clear pending state and fall through
            if self._command_bar:
                self._command_bar.show_message("Invalid key combination")
            return

        # First 'g' key - enter pending state
        if key == "g":
            self._pending_g_key = True
            if self._command_bar:
                self._command_bar.show_message("g (waiting: s=Servers, a=Aria2, g=App)")
            event.prevent_default()
            return

        # Check if download_list is in search mode
        if self._download_list and self._download_list._search_mode:
            # In search mode, pass printable characters and backspace to search handler
            if key == "backspace":
                self._download_list.handle_search_input("backspace")
                event.prevent_default()
                return
            if len(key) == 1 and key.isprintable():
                self._download_list.handle_search_input(key)
                event.prevent_default()
                return
            # ESC is handled by download_list's action_exit_search_mode binding
            # Other keys (arrows, etc.) pass through normally

        # Enter key toggles preview mode (needs to be intercepted before child widgets)
        if key == "enter":
            self.action_toggle_preview()
            event.prevent_default()
            return

        # 1/2/3 are ALWAYS for left panel (global), regardless of focus
        if key == "1":
            if self._download_list:
                self._download_list.action_switch_tab("active")
            event.prevent_default()
            return
        if key == "2":
            if self._download_list:
                self._download_list.action_switch_tab("waiting")
            event.prevent_default()
            return
        if key == "3":
            if self._download_list:
                self._download_list.action_switch_tab("stopped")
            event.prevent_default()
            return

        # Determine which panel has focus for t/T (context-sensitive)
        focused_panel = self._get_focused_panel()

        if focused_panel == "left":
            # Left panel (DownloadListWidget) tab cycling
            if key == "t" and self._download_list:
                self._download_list.action_cycle_tab_forward()
                event.prevent_default()
            elif key == "T" and self._download_list:
                self._download_list.action_cycle_tab_backward()
                event.prevent_default()

        elif focused_panel == "right":
            # Right panel (DownloadDetailWidget) tab cycling
            if key == "t" and self._download_detail:
                self._download_detail.action_next_tab()
                event.prevent_default()
            elif key == "T" and self._download_detail:
                self._download_detail.action_previous_tab()
                event.prevent_default()

    def on_download_list_widget_tab_switched(self, event: DownloadListWidget.TabSwitched) -> None:
        """Handle tab switch in download list.

        Args:
            event: Tab switched event
        """
        _ = event  # Tab ID available if needed

        # Reset preview mode when switching tabs
        if self._preview_mode:
            self._preview_mode = False
            if self._download_detail:
                self._download_detail.clear_selection()
            if self._command_bar:
                self._command_bar.show_message("Preview mode: OFF (tab switched)")

    def on_data_table_row_highlighted(self, event) -> None:
        """Handle row selection in download list.

        Args:
            event: Row highlighted event
        """
        _ = event  # Unused, but required by Textual event handler signature

        # Only update detail panel if preview mode is active
        if not self._preview_mode:
            return

        # Update detail panel when a download is selected
        if self._download_list and self._download_detail:
            gid = self._download_list.get_selected_download_gid()
            if gid:
                self._download_detail.show_download(gid)
            else:
                self._download_detail.clear_selection()

    def set_service(self, service: Aria2Service) -> None:
        """Set or update the service instance.

        Args:
            service: Aria2Service instance
        """
        self.service = service
        if self._status_bar:
            self._status_bar.set_service(service)

    def action_add_download(self) -> None:
        """Show add download dialog."""

        async def _add_download() -> None:
            result = await self.app.push_screen_wait(AddDownloadDialog())

            if result and self.service:
                try:
                    download_type = result.get("type", "url")

                    if download_type == "torrent":
                        # Add torrent file
                        gid = await self.service.add_torrent(
                            result["torrent_data"],
                            options=result["options"],
                        )
                    else:
                        # Add URL or magnet link
                        gid = await self.service.add_download(
                            result["urls"],
                            result["options"],
                        )

                    if self._command_bar:
                        self._command_bar.show_message(f"Download added: {gid[:8]}")
                except Exception as e:
                    await self.app.push_screen_wait(
                        MessageDialog(f"Failed to add download: {e}", title="Error")
                    )

        self.run_worker(_add_download(), exclusive=False)

    def action_delete_download(self) -> None:
        """Delete selected download(s) or current download (d key)."""
        if not self._download_list or not self.service:
            return

        gids = self._download_list.get_selected_gids()
        if not gids:
            if self._command_bar:
                self._command_bar.show_message("No download selected")
            return

        service = self.service
        count = len(gids)

        async def _delete_downloads() -> None:
            try:
                # Confirm deletion
                message = (
                    f"Are you sure you want to delete {count} download{'s' if count > 1 else ''}?"
                )
                confirmed = await self.app.push_screen_wait(
                    ConfirmDialog(
                        message,
                        title="Confirm Delete",
                        confirm_label="Delete",
                    )
                )

                if confirmed and service:
                    try:
                        for gid in gids:
                            await service.remove_download(gid, force=True)

                        if self._command_bar:
                            msg = f"Deleted {count} download{'s' if count > 1 else ''}"
                            self._command_bar.show_message(msg)
                    except Exception as e:
                        # Use call_from_thread to safely show dialog from worker
                        error_msg = str(e)
                        if self._command_bar:
                            self._command_bar.show_message(f"Delete failed: {error_msg}")
            except Exception as e:
                # Handle any unexpected errors
                if self._command_bar:
                    self._command_bar.show_message(f"Error: {str(e)}")

        self.run_worker(_delete_downloads(), exclusive=False)

    def action_pause_download(self) -> None:
        """Smart pause/resume/retry for selected download.

        Behavior based on download status:
        - PAUSED: Resume the download
        - ACTIVE/WAITING: Pause the download
        - ERROR: Retry the download (remove and re-add)
        - COMPLETE: Show message (no action needed)
        """
        if not self._download_list or not self.service:
            return

        gid = self._download_list.get_selected_download_gid()
        if not gid:
            if self._command_bar:
                self._command_bar.show_message("No download selected")
            return

        # Capture service reference for closure
        service = self.service

        async def _toggle_download_state() -> None:
            if not service:
                return

            try:
                download = service.get_download(gid)
                if not download:
                    if self._command_bar:
                        self._command_bar.show_message("Download not found")
                    return

                from ariatuc.core.download_manager import DownloadStatus

                # Smart state handling based on current status
                if download.status == DownloadStatus.PAUSED:
                    # Resume paused download
                    await service.resume_download(gid)
                    if self._command_bar:
                        self._command_bar.show_message("Download resumed")

                elif download.status == DownloadStatus.ERROR:
                    # Retry failed download
                    try:
                        new_gid = await service.retry_download(gid)
                        if self._command_bar:
                            self._command_bar.show_message(
                                f"Download retrying... (new GID: {new_gid[:8]})"
                            )
                    except Exception as e:
                        if self._command_bar:
                            self._command_bar.show_message(f"Retry failed: {str(e)}")

                elif download.status == DownloadStatus.COMPLETE:
                    # Already completed - nothing to do
                    if self._command_bar:
                        self._command_bar.show_message("Download already completed")

                elif download.status == DownloadStatus.REMOVED:
                    # Already removed - nothing to do
                    if self._command_bar:
                        self._command_bar.show_message("Download already removed")

                elif download.status in (DownloadStatus.ACTIVE, DownloadStatus.WAITING):
                    # Pause active or waiting download
                    await service.pause_download(gid)
                    if self._command_bar:
                        self._command_bar.show_message("Download paused")

                else:
                    # Unknown status
                    if self._command_bar:
                        self._command_bar.show_message(
                            f"Unknown download status: {download.status}"
                        )

            except Exception as e:
                if self._command_bar:
                    self._command_bar.show_message(f"Operation failed: {str(e)}")

        self.run_worker(_toggle_download_state(), exclusive=False)

    def action_refresh(self) -> None:
        """Refresh download list."""
        if self._download_list:
            self._download_list.refresh_downloads()
        if self._command_bar:
            self._command_bar.show_message("Refreshed")

    def action_resume_download(self) -> None:
        """Resume selected download(s) or current download (u key)."""
        if not self._download_list or not self.service:
            return

        gids = self._download_list.get_selected_gids()
        if not gids:
            if self._command_bar:
                self._command_bar.show_message("No download selected")
            return

        service = self.service

        async def _resume_downloads() -> None:
            if not service:
                return

            try:
                count = len(gids)
                for gid in gids:
                    await service.resume_download(gid)

                if self._command_bar:
                    msg = f"Resumed {count} download{'s' if count > 1 else ''}"
                    self._command_bar.show_message(msg)
            except Exception as e:
                if self._command_bar:
                    self._command_bar.show_message(f"Resume failed: {str(e)}")

        self.run_worker(_resume_downloads(), exclusive=False)

    def action_pause_all(self) -> None:
        """Pause all downloads (P key)."""
        if not self.service:
            return

        service = self.service

        async def _pause_all() -> None:
            if not service:
                return

            try:
                result = await service.pause_all()
                count = len(result) if isinstance(result, list) else 0

                if self._command_bar:
                    self._command_bar.show_message(f"Paused all downloads ({count} items)")
            except Exception as e:
                if self._command_bar:
                    self._command_bar.show_message(f"Pause all failed: {str(e)}")

        self.run_worker(_pause_all(), exclusive=False)

    def action_resume_all(self) -> None:
        """Resume all downloads (U key)."""
        if not self.service:
            return

        service = self.service

        async def _resume_all() -> None:
            if not service:
                return

            try:
                result = await service.resume_all()
                count = len(result) if isinstance(result, list) else 0

                if self._command_bar:
                    self._command_bar.show_message(f"Resumed all downloads ({count} items)")
            except Exception as e:
                if self._command_bar:
                    self._command_bar.show_message(f"Resume all failed: {str(e)}")

        self.run_worker(_resume_all(), exclusive=False)

    def action_open_servers(self) -> None:
        """Open server management screen."""

        async def _show_servers() -> None:
            from ariatuc.ui.screens.server_management_screen import ServerManagementScreen

            if not self.service:
                if self._command_bar:
                    self._command_bar.show_message("Service not available")
                return

            result = await self.app.push_screen_wait(ServerManagementScreen(service=self.service))
            if result:
                # Server changes applied
                if self._command_bar:
                    self._command_bar.show_message("Server configuration updated")

        self.run_worker(_show_servers(), exclusive=False)

    def action_app_settings(self) -> None:
        """Open app settings screen."""

        async def _show_app_settings() -> None:
            # Get config manager from service
            if not self.service:
                if self._command_bar:
                    self._command_bar.show_message("Service not available")
                return

            result = await self.app.push_screen_wait(AppSettingsScreen(self.service.config_mgr))
            if result and self._command_bar:
                num_changed = len(result)
                self._command_bar.show_message(
                    f"Saved {num_changed} app setting{'s' if num_changed > 1 else ''}"
                )

        self.run_worker(_show_app_settings(), exclusive=False)

    def action_aria2_settings(self) -> None:
        """Open aria2 settings screen."""

        async def _show_aria2_settings() -> None:
            if not self.service:
                if self._command_bar:
                    self._command_bar.show_message("Service not available")
                return

            result = await self.app.push_screen_wait(Aria2SettingsScreen(self.service))
            if result and self._command_bar:
                num_changed = len(result)
                self._command_bar.show_message(
                    f"Applied {num_changed} aria2 setting change{'s' if num_changed > 1 else ''}"
                )

        self.run_worker(_show_aria2_settings(), exclusive=False)

    def action_help(self) -> None:
        """Show help screen."""

        async def _show_help() -> None:
            await self.app.push_screen_wait(HelpScreen())

        self.run_worker(_show_help(), exclusive=False)

    def action_quit(self) -> None:
        """Quit application."""
        self.app.exit()

    def action_toggle_preview(self) -> None:
        """Toggle preview mode (Enter key).

        When enabled: j/k navigation automatically shows download details
        When disabled: right panel is cleared
        """
        self._preview_mode = not self._preview_mode
        logger.debug(f"action_toggle_preview: preview_mode={self._preview_mode}")

        if self._preview_mode:
            # Entering preview mode - show current selection
            if self._download_list and self._download_detail:
                gid = self._download_list.get_selected_download_gid()
                logger.debug(f"action_toggle_preview: got gid={gid}")
                if gid:
                    self._download_detail.show_download(gid)
                    if self._command_bar:
                        self._command_bar.show_message("Preview mode: ON")
                else:
                    logger.debug("action_toggle_preview: no gid selected")
        else:
            # Exiting preview mode - clear right panel
            if self._download_detail:
                self._download_detail.clear_selection()
                if self._command_bar:
                    self._command_bar.show_message("Preview mode: OFF")

    def action_toggle_focus(self) -> None:
        """Toggle focus between download list and detail panels."""
        # Cycle focus between download list and detail
        if self._download_list and self._download_detail:
            if self._download_list.has_focus:
                self._download_detail.focus()
            else:
                self._download_list.focus()

    def action_focus_left_panel(self) -> None:
        """Focus the left panel (download list)."""
        if self.is_in_edit_mode():
            return  # Don't switch panels while editing

        if self._download_list:
            self._download_list.focus()

    def action_focus_right_panel(self) -> None:
        """Focus the right panel (download detail)."""
        if self.is_in_edit_mode():
            return  # Don't switch panels while editing

        if self._download_detail:
            self._download_detail.focus()

    def is_in_edit_mode(self) -> bool:
        """Check if any input widget currently has focus.

        Returns:
            True if in edit mode (Input/TextArea focused)
        """
        from textual.widgets import Input, TextArea

        focused = self.app.focused
        return isinstance(focused, (Input, TextArea))

    def _get_focused_panel(self) -> str:
        """Determine which panel currently has focus.

        Returns:
            "left", "right", or "none"
        """
        if not self._download_list or not self._download_detail:
            return "none"

        focused = self.app.focused
        if not focused:
            return "none"

        # Walk up parent chain to find panel
        current: DOMNode | None = focused
        while current:
            if current is self._download_list:
                return "left"
            if current is self._download_detail:
                return "right"
            current = current.parent

        return "none"

    def toggle_detail_panel(self) -> None:
        """Show or hide the detail panel."""
        self._detail_visible = not self._detail_visible
        if self._download_detail:
            self._download_detail.display = self._detail_visible
