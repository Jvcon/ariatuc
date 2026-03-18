"""Download list widget with tabbed interface for Active/Waiting/Stopped downloads."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.widgets import DataTable, TabbedContent, TabPane

if TYPE_CHECKING:
    from ariatuc.core.download_manager import Download, DownloadStatus
    from ariatuc.core.service import Aria2Service
    from ariatuc.ui.keybinding_manager import KeybindingManager


class DownloadListWidget(Container):
    """Download list widget displaying downloads in three tabs.

    Tabs:
    - Active: Currently downloading
    - Waiting: Queued downloads
    - Stopped: Paused/completed/error downloads

    Columns:
    - Status: Icon indicator (⬇/⏸/✓/✗)
    - Name: Download filename (with sort indicator if sorted)
    - Progress: Progress bar and percentage
    - Speed: Download speed
    - Size: Current/Total size
    - ETA: Estimated time remaining

    Keyboard shortcuts:
    - j/k or ↑/↓: Navigate
    - 1/2/3: Switch tabs
    - s: Cycle through sort options (Name, Size, Progress, Speed, ETA, Added Time)
    - /: Enter search mode to filter downloads
    - Esc: Exit search mode
    - Enter: View details
    - Space: Select for batch operations

    Sorting:
    - Press 's' to cycle through sort criteria
    - Each press cycles: Name → Size → Progress → Speed → ETA → Added Time
    - Sort indicator (↑/↓) shown in table header
    - Sort direction toggles when cycling back to same field

    Search:
    - Press '/' to enter search mode
    - Type to filter downloads by name, GID, or file path
    - Match count shown in status bar
    - Press Esc to exit search and show all downloads
    """

    class TabSwitched(Message):
        """Message sent when tab is switched."""

        def __init__(self, tab_id: str) -> None:
            """Initialize message with tab ID."""
            self.tab_id = tab_id
            super().__init__()

    # Make this widget focusable for H/L panel switching
    can_focus = True

    DEFAULT_CSS = """
    DownloadListWidget {
        width: 100%;
        height: 100%;
    }

    DownloadListWidget DataTable {
        height: 1fr;
    }

    DownloadListWidget .datatable--header {
        background: $primary;
        color: $text;
    }

    DownloadListWidget .datatable--cursor {
        background: $secondary;
    }
    """

    # Note: Keybindings now managed by KeybindingManager
    # Keeping BINDINGS for backward compatibility during migration
    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("s", "open_sort_menu", "Sort"),
        ("S", "reverse_sort_menu", "Sort Rev"),
        ("slash", "enter_search_mode", "Search"),
        ("escape", "handle_escape", ""),
        # Selection mode
        ("v", "toggle_selection_mode", "Select Mode"),
        ("space", "toggle_current_selection", "Toggle"),
        ("ctrl+a", "select_all", "Select All"),
        # Queue operations - CONFLICT RESOLVED: removed 't' (conflicts with tab cycling)
        ("b", "move_to_bottom", "Move Bottom"),
        # Use uppercase K/J for queue position changes
        ("K", "move_up_in_queue", "Queue Up"),
        ("J", "move_down_in_queue", "Queue Down"),
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
        """Initialize download list widget.

        Args:
            service: Aria2Service instance
            keybinding_manager: Keybinding manager instance
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service = service
        self.keybinding_manager = keybinding_manager
        self._tabbed_content: TabbedContent | None = None
        self._active_table: DataTable | None = None
        self._waiting_table: DataTable | None = None
        self._stopped_table: DataTable | None = None
        self._current_tab = "active"

        # Sorting state
        self._sort_by: str = (
            "progress"  # Current sort field: progress, speed, eta, added_time, name, size
        )
        self._sort_ascending: bool = True  # Sort direction (default: progress ascending)

        # Search state
        self._search_mode: bool = False  # Whether search mode is active
        self._search_keyword: str = ""  # Current search keyword

        # Selection state
        self._selection_mode: bool = False  # Whether selection mode is active
        self._selected_gids: set[str] = set()  # Set of selected download GIDs

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with TabbedContent(id="download-tabs"):
            with TabPane("Active", id="tab-active"):
                self._active_table = DataTable(id="table-active")
                self._setup_table(self._active_table)
                yield self._active_table

            with TabPane("Waiting", id="tab-waiting"):
                self._waiting_table = DataTable(id="table-waiting")
                self._setup_table(self._waiting_table)
                yield self._waiting_table

            with TabPane("Stopped", id="tab-stopped"):
                self._stopped_table = DataTable(id="table-stopped")
                self._setup_table(self._stopped_table)
                yield self._stopped_table

    def _setup_table(self, table: DataTable) -> None:
        """Set up table columns.

        Args:
            table: DataTable to configure
        """
        table.add_columns(
            "✓",  # Selection indicator
            "S",  # Status icon
            "ID",  # Download ID (short GID)
            "Name",
            "Progress",
            "Speed",
            "Size",
            "ETA",
        )
        table.cursor_type = "row"
        table.zebra_stripes = True

    def on_mount(self) -> None:
        """Set up auto-refresh when mounted."""
        # Store reference to TabbedContent
        self._tabbed_content = self.query_one(TabbedContent)

        # Update table headers to show initial sort indicator (progress↑)
        self._update_table_headers()

        # Initial refresh
        self.refresh_downloads()

        # Refresh every second
        self.set_interval(1.0, self.refresh_downloads)

        # Focus the current tab's table to enable j/k navigation
        self._focus_current_table()

    def on_focus(self) -> None:
        """When this widget gains focus, pass it to the current table."""
        self._focus_current_table()

    def _focus_current_table(self) -> None:
        """Focus the DataTable of the currently active tab."""
        # Get current tab's table
        if self._current_tab == "active" and self._active_table:
            self._active_table.focus()
        elif self._current_tab == "waiting" and self._waiting_table:
            self._waiting_table.focus()
        elif self._current_tab == "stopped" and self._stopped_table:
            self._stopped_table.focus()

    def action_cursor_down(self) -> None:
        """Move cursor down in the current table (j key)."""
        table = self._get_current_table()
        if table and table.row_count > 0:
            if table.cursor_row is None:
                table.move_cursor(row=0)
            elif table.cursor_row < table.row_count - 1:
                table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the current table (k key)."""
        table = self._get_current_table()
        if table and table.row_count > 0:
            if table.cursor_row is None:
                table.move_cursor(row=0)
            elif table.cursor_row > 0:
                table.action_cursor_up()

    def _get_current_table(self) -> DataTable | None:
        """Get the currently active tab's table.

        Returns:
            Current DataTable or None
        """
        if self._current_tab == "active":
            return self._active_table
        if self._current_tab == "waiting":
            return self._waiting_table
        if self._current_tab == "stopped":
            return self._stopped_table
        return None

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Handle tab activation to track current tab.

        Args:
            event: Tab activation event
        """
        # Update current tab based on the activated pane ID
        pane_id = str(event.pane.id) if event.pane.id else ""
        if pane_id == "tab-active":
            self._current_tab = "active"
        elif pane_id == "tab-waiting":
            self._current_tab = "waiting"
        elif pane_id == "tab-stopped":
            self._current_tab = "stopped"

        # Immediately refresh when tab becomes visible
        self.refresh_downloads()

        # Focus the new tab's table for j/k navigation
        self._focus_current_table()

        # Notify parent screen that tab was switched
        self.post_message(self.TabSwitched(self._current_tab))

    def set_service(self, service: Aria2Service) -> None:
        """Set or update the service instance.

        Args:
            service: Aria2Service instance
        """
        self.service = service
        self.refresh_downloads()

    def refresh_downloads(self) -> None:
        """Refresh all download lists."""
        if not self.service:
            return

        # Refresh each tab's data
        self._refresh_active()
        self._refresh_waiting()
        self._refresh_stopped()

    def _refresh_active(self) -> None:
        """Refresh active downloads table."""
        if not self._active_table or not self.service:
            return

        downloads = self.service.get_active_downloads()
        self._update_table(self._active_table, downloads)

    def _refresh_waiting(self) -> None:
        """Refresh waiting downloads table."""
        if not self._waiting_table or not self.service:
            return

        downloads = self.service.get_waiting_downloads()
        self._update_table(self._waiting_table, downloads)

    def _refresh_stopped(self) -> None:
        """Refresh stopped downloads table."""
        if not self._stopped_table or not self.service:
            return

        downloads = self.service.get_stopped_downloads()
        self._update_table(self._stopped_table, downloads)

    def _sort_downloads(self, downloads: list[Download]) -> list[Download]:
        """Sort downloads based on current sort settings.

        Args:
            downloads: List of downloads to sort

        Returns:
            Sorted list of downloads
        """
        if not downloads:
            return downloads

        # Define sort key functions
        def get_sort_key(download: Download):
            if self._sort_by == "name":
                return self._get_download_name(download).lower()
            if self._sort_by == "size":
                return download.total_length
            if self._sort_by == "progress":
                if download.total_length == 0:
                    return 0.0
                return (download.completed_length / download.total_length) * 100
            if self._sort_by == "speed":
                return download.smoothed_download_speed
            if self._sort_by == "eta":
                # Calculate ETA in seconds for sorting (use smoothed speed for stability)
                if download.smoothed_download_speed == 0:
                    return float("inf")  # Put zero-speed downloads at the end
                remaining = download.total_length - download.completed_length
                return remaining / download.smoothed_download_speed
            if self._sort_by == "added_time":
                # Use GID as proxy for added time (GIDs are sequential)
                return download.gid
            return self._get_download_name(download).lower()

        # Sort with specified direction
        return sorted(downloads, key=get_sort_key, reverse=not self._sort_ascending)

    def _filter_downloads(self, downloads: list[Download]) -> list[Download]:
        """Filter downloads based on search keyword.

        Args:
            downloads: List of downloads to filter

        Returns:
            Filtered list of downloads matching search keyword
        """
        if not self._search_mode or not self._search_keyword:
            return downloads

        keyword_lower = self._search_keyword.lower()
        filtered = []

        for download in downloads:
            # Search in download name
            name = self._get_download_name(download).lower()
            if keyword_lower in name:
                filtered.append(download)
                continue

            # Search in GID
            if keyword_lower in download.gid.lower():
                filtered.append(download)
                continue

            # Search in file paths
            if download.files:
                for file in download.files:
                    if keyword_lower in file.get("path", "").lower():
                        filtered.append(download)
                        break

        return filtered

    def _update_table(self, table: DataTable, downloads: list[Download]) -> None:
        """Update a table with download data while preserving selection.

        Args:
            table: DataTable to update
            downloads: List of downloads
        """
        import logging

        logger = logging.getLogger(__name__)

        # Apply filtering first (if search is active)
        downloads = self._filter_downloads(downloads)

        # Apply sorting
        downloads = self._sort_downloads(downloads)

        # Save current selection (GID and row index)
        selected_gid: str | None = None
        selected_row_index: int | None = None

        if table.cursor_row is not None:
            try:
                # Get currently selected GID
                row_keys = list(table.rows.keys())
                if table.cursor_row < len(row_keys):
                    # Extract GID string from RowKey object
                    row_key = row_keys[table.cursor_row]
                    selected_gid = str(row_key.value) if hasattr(row_key, "value") else str(row_key)
                    selected_row_index = table.cursor_row
                    logger.debug(
                        f"_update_table: saved selection gid={selected_gid}, row={selected_row_index}"
                    )
            except (IndexError, AttributeError) as e:
                logger.warning(f"_update_table: failed to get selection: {e}")

        # Clear existing rows
        table.clear()

        # Add rows for each download
        for download in downloads:
            # Selection indicator
            selected = "[✓]" if download.gid in self._selected_gids else "[ ]"
            status_icon = self._get_status_icon(download.status)
            name = self._get_download_name(download)
            progress = self._format_progress(download)
            speed = self._format_speed(int(download.smoothed_download_speed))
            size = self._format_size(download)
            eta = self._format_eta(download)
            gid_short = self._format_gid(download)

            table.add_row(
                selected,
                status_icon,
                gid_short,
                name,
                progress,
                speed,
                size,
                eta,
                key=download.gid,
            )

        # Restore selection after refresh
        if selected_gid is not None and table.row_count > 0:
            # Try to find the same GID in the new data
            try:
                row_keys = list(table.rows.keys())
                # Convert RowKey objects to strings for comparison
                row_gids = [
                    str(key.value) if hasattr(key, "value") else str(key) for key in row_keys
                ]

                if selected_gid in row_gids:
                    # Found the same download, restore to that row
                    new_index = row_gids.index(selected_gid)
                    table.move_cursor(row=new_index)
                elif selected_row_index is not None and selected_row_index < table.row_count:
                    # GID not found, try to keep same row index
                    table.move_cursor(row=selected_row_index)
                else:
                    # Neither GID nor index valid, select last valid row
                    target_row = min(selected_row_index or 0, table.row_count - 1)
                    table.move_cursor(row=target_row)
            except (IndexError, AttributeError, ValueError, Exception):
                # If anything fails, just select first row
                if table.row_count > 0:
                    try:
                        table.move_cursor(row=0)
                    except Exception:
                        pass  # Silently fail if even this doesn't work

    @staticmethod
    def _get_status_icon(status: DownloadStatus) -> str:
        """Get status icon for download status.

        Args:
            status: Download status enum

        Returns:
            Status icon character
        """
        from ariatuc.core.download_manager import DownloadStatus

        icons = {
            DownloadStatus.ACTIVE: "⬇",
            DownloadStatus.WAITING: "⏳",
            DownloadStatus.PAUSED: "⏸",
            DownloadStatus.ERROR: "✗",
            DownloadStatus.COMPLETE: "✓",
            DownloadStatus.REMOVED: "🗑",
        }
        return icons.get(status, "?")

    @staticmethod
    def _get_download_name(download: Download) -> str:
        """Extract download name from files or use GID.

        Args:
            download: Download object

        Returns:
            Download name or GID
        """
        # Try to get filename from first file
        if download.files and len(download.files) > 0:
            file_path = download.files[0].get("path", "")
            if file_path:
                # Extract filename from path
                return file_path.split("/")[-1] or download.gid[:8]

        # Fallback to shortened GID
        return download.gid[:8]

    def _format_progress(self, download: Download) -> str:
        """Format progress as percentage with bar.

        Args:
            download: Download object

        Returns:
            Formatted progress string
        """
        if download.total_length == 0:
            return "-- %"

        percentage = (download.completed_length / download.total_length) * 100

        # Create simple text-based progress bar
        bar_width = 10
        filled = int((percentage / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)

        return f"{bar} {percentage:.1f}%"

    @staticmethod
    def _format_speed(speed_bytes: int) -> str:
        """Format speed in bytes/s to human readable.

        Args:
            speed_bytes: Speed in bytes per second

        Returns:
            Formatted speed string
        """
        if speed_bytes == 0:
            return "---"

        units = ["B/s", "KB/s", "MB/s", "GB/s"]
        unit_index = 0
        speed = float(speed_bytes)

        while speed >= 1024 and unit_index < len(units) - 1:
            speed /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(speed)} {units[unit_index]}"
        return f"{speed:.1f} {units[unit_index]}"

    def _format_size(self, download: Download) -> str:
        """Format download size.

        Args:
            download: Download object

        Returns:
            Formatted size string (e.g., "450MB/1GB")
        """
        completed = self._format_bytes(download.completed_length)
        total = self._format_bytes(download.total_length)
        return f"{completed}/{total}"

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes to human readable.

        Args:
            bytes_value: Size in bytes

        Returns:
            Formatted size string
        """
        if bytes_value == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(bytes_value)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        return f"{size:.1f} {units[unit_index]}"

    def _format_eta(self, download: Download) -> str:
        """Format estimated time remaining.

        Args:
            download: Download object

        Returns:
            Formatted ETA string
        """
        from ariatuc.core.download_manager import DownloadStatus

        # If download is not active, no ETA
        if download.status != DownloadStatus.ACTIVE or download.smoothed_download_speed == 0:
            if download.status == DownloadStatus.COMPLETE:
                return "Done"
            return "---"

        # Calculate ETA (use smoothed speed for more stable estimates)
        remaining = download.total_length - download.completed_length
        seconds = remaining / download.smoothed_download_speed

        # Format as HH:MM:SS
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _format_gid(self, download: Download) -> str:
        """Format GID as a short identifier for display.

        GID is a 16-digit hex string. We show the first 8 characters for brevity.

        Args:
            download: Download object

        Returns:
            Formatted GID string (e.g., "1a2b3c4d")
        """
        try:
            # Show first 8 characters of GID
            return download.gid[:8] if len(download.gid) >= 8 else download.gid
        except (AttributeError, TypeError):
            # Fallback if GID is invalid
            return "--------"

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab.

        Args:
            tab_id: Tab identifier ('active', 'waiting', 'stopped')
        """
        if not self._tabbed_content:
            return

        self._current_tab = tab_id
        self._tabbed_content.active = f"tab-{tab_id}"

    def action_cycle_tab_forward(self) -> None:
        """Cycle to the next tab (right): Active → Waiting → Stopped → Active."""
        if not self._tabbed_content:
            return

        tab_order = ["active", "waiting", "stopped"]
        current_index = tab_order.index(self._current_tab)
        next_index = (current_index + 1) % len(tab_order)
        next_tab = tab_order[next_index]

        self.action_switch_tab(next_tab)

    def action_cycle_tab_backward(self) -> None:
        """Cycle to the previous tab (left): Stopped → Waiting → Active → Stopped."""
        if not self._tabbed_content:
            return

        tab_order = ["active", "waiting", "stopped"]
        current_index = tab_order.index(self._current_tab)
        prev_index = (current_index - 1) % len(tab_order)
        prev_tab = tab_order[prev_index]

        self.action_switch_tab(prev_tab)

    def get_selected_download_gid(self) -> str | None:
        """Get the GID of the currently selected download.

        Returns:
            Download GID, or None if no selection
        """
        import logging

        logger = logging.getLogger(__name__)

        # Get current tab's table
        if self._current_tab == "active" and self._active_table:
            table = self._active_table
        elif self._current_tab == "waiting" and self._waiting_table:
            table = self._waiting_table
        elif self._current_tab == "stopped" and self._stopped_table:
            table = self._stopped_table
        else:
            logger.debug(f"get_selected_download_gid: no table for tab '{self._current_tab}'")
            return None

        # Get selected row key (GID)
        if table.cursor_row is not None and table.row_count > 0:
            try:
                # Get row keys (GIDs were stored as keys when adding rows)
                row_keys = list(table.rows.keys())
                logger.debug(
                    f"get_selected_download_gid: cursor_row={table.cursor_row}, row_count={table.row_count}, keys_count={len(row_keys)}"
                )

                if table.cursor_row < len(row_keys):
                    row_key = row_keys[table.cursor_row]
                    # RowKey objects have a 'value' attribute that contains the actual key
                    gid = str(row_key.value) if hasattr(row_key, "value") else str(row_key)
                    logger.debug(f"get_selected_download_gid: returning gid={gid}")
                    return gid
                logger.warning(
                    f"get_selected_download_gid: cursor_row {table.cursor_row} out of range (len={len(row_keys)})"
                )
            except (IndexError, AttributeError) as e:
                logger.error(f"get_selected_download_gid: exception {e}", exc_info=True)

        logger.debug(
            f"get_selected_download_gid: no valid selection (cursor_row={table.cursor_row}, row_count={table.row_count})"
        )
        return None

    def action_open_sort_menu(self) -> None:
        """Open sort menu to cycle sort criteria forward (s key).

        Cycles through field+direction pairs:
        progress↑ -> progress↓ -> speed↑ -> speed↓ -> eta↑ -> eta↓ ->
        added_time↑ -> added_time↓ -> name↑ -> name↓ -> size↑ -> size↓ -> progress↑ ...
        """
        sort_options = ["progress", "speed", "eta", "added_time", "name", "size"]

        if self._sort_ascending:
            # Currently ascending -> switch to descending (same field)
            self._sort_ascending = False
        else:
            # Currently descending -> switch to next field ascending
            try:
                current_index = sort_options.index(self._sort_by)
                next_index = (current_index + 1) % len(sort_options)
                self._sort_by = sort_options[next_index]
                self._sort_ascending = True
            except ValueError:
                # Fallback if current sort field is invalid
                self._sort_by = "progress"
                self._sort_ascending = True

        # Update table headers to show sort indicator
        self._update_table_headers()

        # Refresh to apply new sort
        self.refresh_downloads()

        # Notify user of current sort (via parent screen's command bar)
        self._show_sort_status()

    def action_reverse_sort_menu(self) -> None:
        """Open sort menu to cycle sort criteria backward (S key).

        Cycles through field+direction pairs in reverse:
        progress↑ -> size↓ -> size↑ -> name↓ -> name↑ -> added_time↓ ->
        added_time↑ -> eta↓ -> eta↑ -> speed↓ -> speed↑ -> progress↓ -> progress↑ ...
        """
        sort_options = ["progress", "speed", "eta", "added_time", "name", "size"]

        if not self._sort_ascending:
            # Currently descending -> switch to ascending (same field)
            self._sort_ascending = True
        else:
            # Currently ascending -> switch to previous field descending
            try:
                current_index = sort_options.index(self._sort_by)
                prev_index = (current_index - 1) % len(sort_options)
                self._sort_by = sort_options[prev_index]
                self._sort_ascending = False
            except ValueError:
                # Fallback if current sort field is invalid
                self._sort_by = "progress"
                self._sort_ascending = True

        # Update table headers to show sort indicator
        self._update_table_headers()

        # Refresh to apply new sort
        self.refresh_downloads()

        # Notify user of current sort (via parent screen's command bar)
        self._show_sort_status()

    def action_enter_search_mode(self) -> None:
        """Enter search mode (/ key)."""
        if self._search_mode:
            return  # Already in search mode

        self._search_mode = True
        self._search_keyword = ""

        # Notify keybinding manager of mode change
        if self.keybinding_manager:
            from ariatuc.ui.keybinding_manager import KeybindingMode

            self.keybinding_manager.set_mode(KeybindingMode.SEARCH)

        # Notify parent to show search input
        self._show_search_status()

    def action_handle_escape(self) -> None:
        """Handle Escape key - exit search/selection mode or let it propagate.

        Priority:
        1. Exit search mode if active
        2. Clear selection if any items selected
        3. Exit selection mode if active
        4. Otherwise, let Esc propagate (handled by parent)
        """
        # Priority 1: Exit search mode
        if self._search_mode:
            self._search_mode = False
            self._search_keyword = ""

            # Notify keybinding manager back to NORMAL mode
            if self.keybinding_manager:
                from ariatuc.ui.keybinding_manager import KeybindingMode

                self.keybinding_manager.set_mode(KeybindingMode.NORMAL)

            self.refresh_downloads()
            self._show_search_status()
            return

        # Priority 2: Clear selection if any items selected
        if self._selected_gids:
            self._selected_gids.clear()
            self.refresh_downloads()
            self._show_selection_status()
            return

        # Priority 3: Exit selection mode
        if self._selection_mode:
            self._selection_mode = False

            # Notify keybinding manager back to NORMAL mode
            if self.keybinding_manager:
                from ariatuc.ui.keybinding_manager import KeybindingMode

                self.keybinding_manager.set_mode(KeybindingMode.NORMAL)

            self._show_selection_status()
            return

        # Otherwise, let Esc propagate to parent (not preventing default)

    def handle_search_input(self, char: str) -> None:
        """Handle character input in search mode.

        Args:
            char: Character to add to search keyword
        """
        if not self._search_mode:
            return

        if char == "backspace":
            self._search_keyword = self._search_keyword[:-1]
        elif len(char) == 1 and char.isprintable():
            self._search_keyword += char

        # Refresh to apply new filter
        self.refresh_downloads()

        # Update search status display
        self._show_search_status()

    def _update_table_headers(self) -> None:
        """Update table headers to show sort indicator.

        Note: Textual DataTable doesn't support updating column headers after creation,
        so we need to recreate the table. This is called before refresh_downloads()
        which will repopulate the data.
        """
        # Column name mapping to header labels
        # Note: added_time sorts by GID and shows indicator on ID column
        column_map = {
            "name": "Name",
            "size": "Size",
            "progress": "Progress",
            "speed": "Speed",
            "eta": "ETA",
            "added_time": "ID",  # added_time sort shows on ID column (GID-based)
        }

        # Get the header label for current sort field
        sort_header = column_map.get(self._sort_by)

        # Direction indicator
        direction = "↑" if self._sort_ascending else "↓"

        # Update all three tables
        for table in [self._active_table, self._waiting_table, self._stopped_table]:
            if table:
                # Clear all data AND columns to prevent duplication
                # columns=True ensures both rows and columns are cleared
                table.clear(columns=True)

                # Add headers with sort indicator
                for col_name in ["✓", "S", "ID", "Name", "Progress", "Speed", "Size", "ETA"]:
                    if sort_header and col_name == sort_header:
                        label = f"{col_name} {direction}"
                    else:
                        label = col_name
                    table.add_column(label)

    def _show_sort_status(self) -> None:
        """Show current sort status in command bar."""
        # This will be picked up by MainScreen to display in CommandBar
        sort_label = {
            "name": "Name",
            "size": "Size",
            "progress": "Progress",
            "speed": "Speed",
            "eta": "ETA",
            "added_time": "Added Time",
        }.get(self._sort_by, "Name")

        direction = "Ascending" if self._sort_ascending else "Descending"
        message = f"Sort: {sort_label} ({direction})"

        # Try to access parent screen's command bar
        try:
            from ariatuc.ui.widgets.command_bar import CommandBar

            if command_bar := self.app.query_one("#command-bar", CommandBar):
                command_bar.show_message(message)
        except Exception:
            pass  # Silently fail if command bar not available

    def _show_search_status(self) -> None:
        """Show current search status in command bar."""
        if self._search_mode:
            # Count matching downloads
            all_downloads = []
            if self.service:
                all_downloads = (
                    self.service.get_active_downloads()
                    + self.service.get_waiting_downloads()
                    + self.service.get_stopped_downloads()
                )

            filtered = self._filter_downloads(all_downloads)
            match_count = len(filtered)
            total_count = len(all_downloads)

            message = f"Search: {self._search_keyword}_ ({match_count}/{total_count} matches)"
        else:
            message = ""  # Clear message when exiting search

        # Try to access parent screen's command bar
        try:
            from ariatuc.ui.widgets.command_bar import CommandBar

            if command_bar := self.app.query_one("#command-bar", CommandBar):
                if message:
                    command_bar.show_message(message)
                else:
                    command_bar.update("")  # Clear message
        except Exception:
            pass  # Silently fail if command bar not available

    # Selection mode actions

    def action_toggle_selection_mode(self) -> None:
        """Toggle selection mode (v key)."""
        self._selection_mode = not self._selection_mode

        # Notify keybinding manager of mode change
        if self.keybinding_manager:
            from ariatuc.ui.keybinding_manager import KeybindingMode

            mode = KeybindingMode.SELECT if self._selection_mode else KeybindingMode.NORMAL
            self.keybinding_manager.set_mode(mode)

        # Clear selection when entering selection mode
        if self._selection_mode:
            self._selected_gids.clear()
            self.refresh_downloads()

        self._show_selection_status()

    def action_toggle_current_selection(self) -> None:
        """Toggle selection of current download (Space key)."""
        if not self._selection_mode:
            # Enter selection mode first
            self._selection_mode = True

        gid = self.get_selected_download_gid()
        if gid:
            if gid in self._selected_gids:
                self._selected_gids.remove(gid)
            else:
                self._selected_gids.add(gid)

            self.refresh_downloads()
            self._show_selection_status()

    def action_select_all(self) -> None:
        """Select all downloads in current tab (Ctrl+A)."""
        if not self._selection_mode:
            self._selection_mode = True

        # Get all downloads in current tab
        if not self.service:
            return

        if self._current_tab == "active":
            downloads = self.service.get_active_downloads()
        elif self._current_tab == "waiting":
            downloads = self.service.get_waiting_downloads()
        elif self._current_tab == "stopped":
            downloads = self.service.get_stopped_downloads()
        else:
            return

        # Apply current filter and sort
        downloads = self._filter_downloads(downloads)
        downloads = self._sort_downloads(downloads)

        # Select all visible downloads
        self._selected_gids = {d.gid for d in downloads}

        self.refresh_downloads()
        self._show_selection_status()

    def _show_selection_status(self) -> None:
        """Show current selection status in command bar."""
        if self._selection_mode and self._selected_gids:
            count = len(self._selected_gids)
            message = f"Selection Mode: {count} selected | Space-Toggle | Ctrl+A-All | Esc-Clear"
        elif self._selection_mode:
            message = "Selection Mode: 0 selected | Space-Toggle | Ctrl+A-Select All"
        else:
            message = ""

        try:
            from ariatuc.ui.widgets.command_bar import CommandBar

            if command_bar := self.app.query_one("#command-bar", CommandBar):
                if message:
                    command_bar.show_message(message)
                else:
                    command_bar.update("")
        except Exception:
            pass

    # Queue operations

    def action_move_to_top(self) -> None:
        """Move selected download(s) to top of queue (t key)."""
        if self._selected_gids:
            gids = list(self._selected_gids)
        else:
            current_gid = self.get_selected_download_gid()
            gids = [current_gid] if current_gid else []

        if not gids or not self.service:
            return

        # Move to position 0 (top)
        for gid in gids:
            self.run_worker(self._move_position(gid, 0, "POS_SET"))

    def action_move_to_bottom(self) -> None:
        """Move selected download(s) to bottom of queue (b key)."""
        if self._selected_gids:
            gids = list(self._selected_gids)
        else:
            current_gid = self.get_selected_download_gid()
            gids = [current_gid] if current_gid else []

        if not gids or not self.service:
            return

        # Move to position -1 (bottom) using POS_END
        for gid in gids:
            self.run_worker(self._move_position(gid, 0, "POS_END"))

    def action_move_up_in_queue(self) -> None:
        """Move selected download(s) up one position in queue (K key)."""
        if self._selected_gids:
            gids = list(self._selected_gids)
        else:
            current_gid = self.get_selected_download_gid()
            gids = [current_gid] if current_gid else []

        if not gids or not self.service:
            return

        # Move up by -1 position (relative)
        for gid in gids:
            self.run_worker(self._move_position(gid, -1, "POS_CUR"))

    def action_move_down_in_queue(self) -> None:
        """Move selected download(s) down one position in queue (J key)."""
        if self._selected_gids:
            gids = list(self._selected_gids)
        else:
            current_gid = self.get_selected_download_gid()
            gids = [current_gid] if current_gid else []

        if not gids or not self.service:
            return

        # Move down by +1 position (relative)
        for gid in gids:
            self.run_worker(self._move_position(gid, 1, "POS_CUR"))

    async def _move_position(self, gid: str, pos: int, how: str) -> None:
        """Move download position in queue.

        Args:
            gid: Download GID
            pos: Position or offset
            how: How to interpret pos (POS_SET, POS_CUR, POS_END)
        """
        if not self.service:
            return

        try:
            await self.service.change_position(gid, pos, how)
            self.refresh_downloads()

            # Show success message
            action_msg = {
                "POS_SET": f"top (position {pos})" if pos == 0 else f"position {pos}",
                "POS_CUR": f"up {-pos}" if pos < 0 else f"down {pos}",
                "POS_END": "bottom",
            }.get(how, "")

            from ariatuc.ui.widgets.command_bar import CommandBar

            if command_bar := self.app.query_one("#command-bar", CommandBar):
                command_bar.show_message(f"✓ Moved to {action_msg}")
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Failed to move position: {e}")

            from ariatuc.ui.widgets.command_bar import CommandBar

            if command_bar := self.app.query_one("#command-bar", CommandBar):
                command_bar.show_message(f"✗ Failed to move: {e}")

    def get_selected_gids(self) -> list[str]:
        """Get list of selected download GIDs.

        Returns:
            List of selected GIDs, or list with current GID if no selection
        """
        if self._selected_gids:
            return list(self._selected_gids)

        current_gid = self.get_selected_download_gid()
        return [current_gid] if current_gid else []
