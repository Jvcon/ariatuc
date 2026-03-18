"""Download detail widget showing detailed information about a selected download."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.widgets import Label, ListItem, ListView, Static, TabbedContent, TabPane

from ariatuc.ui.widgets.chunk_map import ChunkMap

if TYPE_CHECKING:
    from ariatuc.core.download_manager import Download, DownloadStatus
    from ariatuc.core.service import Aria2Service

logger = logging.getLogger(__name__)


class DownloadDetailWidget(Container):
    """Download detail widget with tabbed interface.

    Tabs (P0 includes Overview only, P1+ adds more):
    - Overview: Basic info, progress, speed, connections
    - Files: File list for multi-file downloads (P1)
    - Peers: BitTorrent peer information (P2)
    - Trackers: BitTorrent tracker information (P2)
    - Servers: HTTP/FTP server information (P2)

    Keyboard shortcuts:
    - h/l or [/]: Switch tabs
    - Esc: Close details
    """

    # Make this widget focusable for H/L panel switching
    can_focus = True

    DEFAULT_CSS = """
    DownloadDetailWidget {
        width: 100%;
        height: 100%;
    }

    DownloadDetailWidget VerticalScroll {
        height: 1fr;
        padding: 1;
    }

    /* Files tab layout: 60% file list + 40% chunk map */
    #files-container {
        height: 1fr;
        layout: grid;
        grid-size: 1 2;
        grid-rows: 3fr 2fr;
    }

    #files-list-wrapper {
        height: 100%;
        border: solid $primary;
        padding: 0;
    }

    #files-list {
        height: 1fr;
        padding: 0;
    }

    #chunk-map-wrapper {
        height: 100%;
        border: solid $primary;
        padding: 0 1;
        margin-top: 1;
    }

    .files-no-selection {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }

    .detail-row {
        height: auto;
        margin-bottom: 1;
    }

    .detail-label {
        color: $text-muted;
        width: 15;
        text-style: bold;
    }

    .detail-value {
        color: $text;
    }

    .no-selection {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    """

    BINDINGS = [
        ("h", "previous_tab", "Previous Tab"),
        ("l", "next_tab", "Next Tab"),
        ("[", "previous_tab", "Previous Tab"),
        ("]", "next_tab", "Next Tab"),
    ]

    def __init__(
        self,
        service: Aria2Service | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize download detail widget.

        Args:
            service: Aria2Service instance
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service = service
        self._current_gid: str | None = None
        self._tabbed_content: TabbedContent | None = None
        self._overview_content: VerticalScroll | None = None
        self._files_list: ListView | None = None
        self._chunk_map: ChunkMap | None = None
        self._files_container: Vertical | None = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with TabbedContent(id="detail-tabs"):
            with TabPane("Overview", id="tab-overview"):
                self._overview_content = VerticalScroll()
                with self._overview_content:
                    yield Static(
                        "Select a download to view details",
                        classes="no-selection",
                    )

            with TabPane("Files", id="tab-files"):
                self._files_container = Vertical(id="files-container")
                with self._files_container:
                    # Upper 60%: File list
                    with Vertical(id="files-list-wrapper"):
                        self._files_list = ListView(id="files-list")
                        yield self._files_list

                    # Lower 40%: Chunk map
                    with Vertical(id="chunk-map-wrapper"):
                        self._chunk_map = ChunkMap(id="chunk-map")
                        yield self._chunk_map

            # TODO: P2 - Add Peers tab (BitTorrent peer information)
            # TODO: P2 - Add Trackers tab (BitTorrent tracker information)
            # TODO: P2 - Add Servers tab (HTTP/FTP server information)

    def on_mount(self) -> None:
        """Set up after mounting."""
        self._tabbed_content = self.query_one(TabbedContent)

        # Refresh every second if a download is selected
        self.set_interval(1.0, self.refresh_details)

    def set_service(self, service: Aria2Service) -> None:
        """Set or update the service instance.

        Args:
            service: Aria2Service instance
        """
        self.service = service

    def show_download(self, gid: str) -> None:
        """Show details for a specific download.

        Args:
            gid: Download GID to display
        """
        logger.debug(f"show_download called with gid: {gid}")
        self._current_gid = gid
        self.refresh_details()

    def clear_selection(self) -> None:
        """Clear the current selection and show placeholder."""
        self._current_gid = None
        self._show_no_selection()

    def refresh_details(self) -> None:
        """Refresh the displayed download details."""
        if not self._current_gid or not self.service:
            logger.debug(
                f"refresh_details: no gid ({self._current_gid}) or service ({self.service})"
            )
            self._show_no_selection()
            return

        # Get download from service
        download = self.service.get_download(self._current_gid)
        if not download:
            logger.debug(f"refresh_details: download not found for gid {self._current_gid}")
            self._show_no_selection()
            return

        logger.debug(
            f"refresh_details: updating tabs for download {download.gid}, name={download.name}, dir={download.dir}"
        )
        # Update overview tab
        self._update_overview(download)
        # Update files tab (includes chunk map)
        self._update_files(download)

    def _show_no_selection(self) -> None:
        """Show the 'no selection' message."""
        if not self._overview_content:
            return

        # Clear and show placeholder in overview
        self._overview_content.remove_children()
        self._overview_content.mount(
            Static(
                "Select a download to view details",
                classes="no-selection",
            )
        )

        # Clear files list and show placeholder
        if self._files_list:
            self._files_list.clear()
            item = ListItem(
                Label("Select a download to view files", classes="files-no-selection"),
                disabled=True,
            )
            self._files_list.append(item)

        # Clear chunk map
        if self._chunk_map:
            self._chunk_map.clear()

    def _update_overview(self, download: Download) -> None:
        """Update the Overview tab with download information.

        Args:
            download: Download object to display
        """
        if not self._overview_content:
            logger.warning("_update_overview: _overview_content is None")
            return

        from ariatuc.core.download_manager import DownloadStatus

        logger.debug(
            f"_update_overview: download.gid={download.gid}, name={download.name}, dir={download.dir}, urls={download.urls}, files_count={len(download.files)}"
        )

        # Clear existing content
        self._overview_content.remove_children()

        # Build overview content
        lines = []

        # Name (filename)
        if download.name:
            lines.append(f"[bold]Name:[/bold] {download.name}")
        else:
            logger.debug("_update_overview: download.name is empty")

        # Status
        status_color = self._get_status_color(download.status)
        lines.append(
            f"[bold]Status:[/bold] [{status_color}]{download.status.value}[/{status_color}]"
        )

        # Progress
        if download.total_length > 0:
            percentage = (download.completed_length / download.total_length) * 100
            bar_width = 30
            filled = int((percentage / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            lines.append(f"[bold]Progress:[/bold] {bar} {percentage:.1f}%")
        else:
            lines.append("[bold]Progress:[/bold] --")

        # Size and Files Count
        completed = self._format_bytes(download.completed_length)
        total = self._format_bytes(download.total_length)
        files_count = len(download.files) if download.files else 0
        if files_count > 0:
            lines.append(
                f"[bold]Size:[/bold] {completed} / {total} ({files_count} file{'s' if files_count > 1 else ''})"
            )
        else:
            lines.append(f"[bold]Size:[/bold] {completed} / {total}")

        # Speed (for active downloads) - use EMA smoothed speeds
        if download.status == DownloadStatus.ACTIVE:
            # Use smoothed speeds for display (more stable)
            dl_speed = self._format_speed(int(download.smoothed_download_speed))
            ul_speed = self._format_speed(int(download.smoothed_upload_speed))
            lines.append(f"[bold]Speed:[/bold] ⬇ {dl_speed} | ⬆ {ul_speed}")

            # ETA - use smoothed download speed for more accurate estimation
            if download.smoothed_download_speed > 0:
                remaining = download.total_length - download.completed_length
                seconds = remaining / download.smoothed_download_speed
                eta = self._format_time(seconds)
                lines.append(f"[bold]ETA:[/bold] {eta}")
            elif download.download_speed > 0:
                # Fallback to instantaneous speed if smoothed speed not available
                remaining = download.total_length - download.completed_length
                seconds = remaining / download.download_speed
                eta = self._format_time(seconds)
                lines.append(f"[bold]ETA:[/bold] {eta}")

        # Connections
        lines.append(f"[bold]Connections:[/bold] {download.connections}")

        # BitTorrent specific fields
        if download.is_torrent:
            lines.append("")  # Blank line for separation
            lines.append("[bold][cyan]BitTorrent Information[/cyan][/bold]")

            # Seeders
            if download.num_seeders > 0:
                lines.append(f"[bold]Seeders:[/bold] {download.num_seeders}")

            # Upload stats (for active/complete torrents) - use EMA smoothed upload speed
            if download.upload_length > 0 or download.smoothed_upload_speed > 0:
                uploaded = self._format_bytes(download.upload_length)
                ul_speed = self._format_speed(int(download.smoothed_upload_speed))
                lines.append(f"[bold]Uploaded:[/bold] {uploaded} ({ul_speed})")

            # Share ratio (only if something has been downloaded)
            if download.completed_length > 0:
                share_ratio = download.share_ratio
                ratio_color = "green" if share_ratio >= 1.0 else "yellow"
                lines.append(
                    f"[bold]Share Ratio:[/bold] [{ratio_color}]{share_ratio:.2f}[/{ratio_color}]"
                )

            # Info hash
            if download.info_hash:
                lines.append(f"[bold]Info Hash:[/bold] [dim]{download.info_hash[:16]}...[/dim]")

        # Download directory
        if download.dir:
            lines.append("")  # Blank line for separation
            lines.append(f"[bold]Dir:[/bold] {download.dir}")

        # URLs (show first URL if available, with indication if there are more)
        if download.urls and not download.is_torrent:
            if len(download.urls) == 1:
                lines.append(f"[bold]URL:[/bold] {download.urls[0]}")
            else:
                lines.append(f"[bold]URL:[/bold] {download.urls[0]}")
                lines.append(
                    f"[dim](+{len(download.urls) - 1} more URL{'s' if len(download.urls) > 2 else ''})[/dim]"
                )

        # GID (at the bottom for reference)
        lines.append("")  # Blank line for separation
        lines.append(f"[dim][bold]GID:[/bold] {download.gid}[/dim]")

        # Mount the content as a single Static widget
        content_text = "\n\n".join(lines)
        self._overview_content.mount(Static(content_text))

    def _update_files(self, download: Download) -> None:
        """Update the Files tab with file list information and chunk map.

        Args:
            download: Download object to display
        """
        if not self._files_list:
            logger.warning("_update_files: _files_list is None")
            return

        # Update chunk map
        if self._chunk_map:
            self._chunk_map.set_download(download)

        # Clear existing items
        self._files_list.clear()

        # Check if download has files
        if not download.files or len(download.files) == 0:
            item = ListItem(Label("No files to display"), disabled=True)
            self._files_list.append(item)
            return

        # Display each file as a ListItem
        for idx, file_data in enumerate(download.files, 1):
            # Extract file info
            file_path = file_data.get("path", "")
            file_length = int(file_data.get("length", 0))
            file_completed = int(file_data.get("completedLength", 0))

            # Get filename from path
            filename = file_path.split("/")[-1] if file_path else f"File {idx}"

            # Calculate file progress
            if file_length > 0:
                file_progress = (file_completed / file_length) * 100
            else:
                file_progress = 0.0

            # Format sizes
            size_completed = self._format_bytes(file_completed)
            size_total = self._format_bytes(file_length)

            # Build file entry text
            file_text = (
                f"{idx}. {filename}\n   {size_completed}/{size_total} ({file_progress:.1f}%)"
            )

            # Progress bar for active files
            if file_progress > 0:
                bar_width = 30
                filled = int((file_progress / 100) * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                file_text += f"\n   {bar}"

            label = Label(file_text)
            item = ListItem(label, id=f"file-{idx}")
            self._files_list.append(item)

    @staticmethod
    def _get_status_color(status: DownloadStatus) -> str:
        """Get color for download status.

        Args:
            status: Download status

        Returns:
            Color name for status
        """
        from ariatuc.core.download_manager import DownloadStatus

        color_map = {
            DownloadStatus.ACTIVE: "green",
            DownloadStatus.WAITING: "yellow",
            DownloadStatus.PAUSED: "blue",
            DownloadStatus.ERROR: "red",
            DownloadStatus.COMPLETE: "bright_green",
            DownloadStatus.REMOVED: "dim",
        }
        return color_map.get(status, "white")

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

    @staticmethod
    def _format_speed(speed_bytes: int) -> str:
        """Format speed in bytes/s to human readable.

        Args:
            speed_bytes: Speed in bytes per second

        Returns:
            Formatted speed string
        """
        if speed_bytes == 0:
            return "0 B/s"

        units = ["B/s", "KB/s", "MB/s", "GB/s"]
        unit_index = 0
        speed = float(speed_bytes)

        while speed >= 1024 and unit_index < len(units) - 1:
            speed /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(speed)} {units[unit_index]}"
        return f"{speed:.1f} {units[unit_index]}"

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time in seconds to HH:MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def action_previous_tab(self) -> None:
        """Switch to previous tab."""
        if self._tabbed_content:
            # Get current tab index
            tabs = list(self._tabbed_content.query(TabPane))
            if not tabs:
                return

            current_tab = self._tabbed_content.active
            current_index = next((i for i, tab in enumerate(tabs) if tab.id == current_tab), 0)

            # Move to previous tab (wrap around)
            previous_index = (current_index - 1) % len(tabs)
            self._tabbed_content.active = tabs[previous_index].id or ""

    def action_next_tab(self) -> None:
        """Switch to next tab."""
        if self._tabbed_content:
            # Get current tab index
            tabs = list(self._tabbed_content.query(TabPane))
            if not tabs:
                return

            current_tab = self._tabbed_content.active
            current_index = next((i for i, tab in enumerate(tabs) if tab.id == current_tab), 0)

            # Move to next tab (wrap around)
            next_index = (current_index + 1) % len(tabs)
            self._tabbed_content.active = tabs[next_index].id or ""
