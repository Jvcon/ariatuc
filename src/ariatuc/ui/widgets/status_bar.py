"""Status bar widget displaying server info and global statistics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

if TYPE_CHECKING:
    from ariatuc.core.service import Aria2Service


class StatusBar(Static):
    """Status bar showing server, connection status, and global stats.

    Displays:
    - Current server name and protocol (ws/http)
    - Connection status indicator (🟢/🟡/🔴)
    - Task statistics (Active/Waiting/Stopped)
    - Global download/upload speeds

    Updates automatically via set_interval.
    """

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: top;
        background: $primary;
        color: $text;
        content-align: left middle;
        padding: 0 1;
    }

    StatusBar Static {
        height: 1;
        background: transparent;
        color: $text;
    }

    .status-server {
        width: auto;
    }

    .status-stats {
        width: auto;
        margin-left: 2;
    }

    .status-speed {
        width: auto;
        margin-left: 2;
    }
    """

    def __init__(
        self,
        service: Aria2Service | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize status bar.

        Args:
            service: Aria2Service instance for fetching stats
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service = service
        self._server_widget: Static | None = None
        self._stats_widget: Static | None = None
        self._speed_widget: Static | None = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Horizontal():
            self._server_widget = Static("Server: --", classes="status-server")
            yield self._server_widget

            self._stats_widget = Static("", classes="status-stats")
            yield self._stats_widget

            self._speed_widget = Static("", classes="status-speed")
            yield self._speed_widget

    def on_mount(self) -> None:
        """Set up auto-refresh when mounted."""
        # Refresh every second
        self.set_interval(1.0, self.refresh_status)
        # Initial refresh
        self.refresh_status()

    def set_service(self, service: Aria2Service) -> None:
        """Set or update the service instance.

        Args:
            service: Aria2Service instance
        """
        self.service = service
        self.refresh_status()

    def refresh_status(self) -> None:
        """Refresh status bar with current stats."""
        if not self.service:
            self._update_disconnected()
            return

        # Update server info
        self._update_server_info()

        # Update stats asynchronously
        self.run_worker(self._fetch_and_update_stats(), exclusive=True)

    def _update_disconnected(self) -> None:
        """Update display for disconnected state."""
        if self._server_widget:
            self._server_widget.update("Server: -- | 🔴 Disconnected")
        if self._stats_widget:
            self._stats_widget.update("")
        if self._speed_widget:
            self._speed_widget.update("")

    def _update_server_info(self) -> None:
        """Update server name and connection info."""
        if not self.service or not self._server_widget:
            return

        server_name = self.service.current_server or "--"
        is_ws = self.service.is_websocket

        # Connection status indicator
        if is_ws:
            status = "🟢 ws"
        else:
            status = "🟡 http"

        # Check if local process and add process status
        process_status = ""
        if server_name and server_name != "--":
            try:
                config = self.service.rpc_mgr.get_server_config(server_name)
                if config.is_local:
                    process_info = self.service.get_local_process_info(server_name)
                    if process_info:
                        if process_info.state.value == "running":
                            process_status = " [▶]"
                        elif process_info.state.value == "stopped":
                            process_status = " [■]"
                        elif process_info.state.value == "error":
                            process_status = " [✗]"
                    else:
                        process_status = " [■]"
            except KeyError:
                pass

        self._server_widget.update(f"Server: {server_name} ({status}){process_status}")

    async def _fetch_and_update_stats(self) -> None:
        """Fetch stats from service and update display."""
        if not self.service:
            return

        try:
            # Fetch global stats
            stats_obj = await self.service.get_global_stat()
            if not stats_obj:
                # No stats available
                if self._stats_widget:
                    self._stats_widget.update("-- | -- | --")
                if self._speed_widget:
                    self._speed_widget.update("⬇ -- | ⬆ --")
                return

            # Convert GlobalStat object to dict-like access
            stats = {
                "numActive": int(stats_obj.num_active),
                "numWaiting": int(stats_obj.num_waiting),
                "numStopped": int(stats_obj.num_stopped),
                "downloadSpeed": int(stats_obj.download_speed),
                "uploadSpeed": int(stats_obj.upload_speed),
            }

            # Format task statistics
            active = stats.get("numActive", 0)
            waiting = stats.get("numWaiting", 0)
            stopped = stats.get("numStopped", 0)
            stats_text = f"{active} Active | {waiting} Waiting | {stopped} Stopped"

            # Format speeds
            download_speed = int(stats.get("downloadSpeed", 0))
            upload_speed = int(stats.get("uploadSpeed", 0))
            speed_text = (
                f"⬇ {self._format_speed(download_speed)} | ⬆ {self._format_speed(upload_speed)}"
            )

            # Update widgets
            if self._stats_widget:
                self._stats_widget.update(stats_text)
            if self._speed_widget:
                self._speed_widget.update(speed_text)

        except Exception:
            # On error, show minimal info
            if self._stats_widget:
                self._stats_widget.update("-- | -- | --")
            if self._speed_widget:
                self._speed_widget.update("⬇ -- | ⬆ --")

    @staticmethod
    def _format_speed(speed_bytes: int) -> str:
        """Format speed in bytes/s to human readable format.

        Args:
            speed_bytes: Speed in bytes per second

        Returns:
            Formatted speed string (e.g., "1.5 MB/s", "150 KB/s")
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
