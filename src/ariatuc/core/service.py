"""Aria2 Service Layer - Business Logic Coordinator.

This service layer coordinates all managers and provides a unified API for the UI layer.
It handles:
- Download lifecycle management
- State synchronization
- Event handling
- Server connection management
- Settings management
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aria2rpc import Aria2Error, Aria2Event
from aria2rpc.models import GlobalStat, Version
from ariatuc.core import (
    ConfigManager,
    ConnectionState,
    Download,
    DownloadManager,
    DownloadStatus,
    EventManager,
    LocalProcessManager,
    RPCManager,
    ServerConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class DownloadOptions:
    """Options for adding a download."""

    dir: str | None = None  # Download directory
    out: str | None = None  # Output filename
    max_connection_per_server: int | None = None
    split: int | None = None  # Number of connections
    max_download_limit: int | None = None  # Speed limit in bytes/sec
    header: list[str] | None = None  # HTTP headers
    user_agent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to aria2 options dict."""
        options: dict[str, Any] = {}
        if self.dir:
            options["dir"] = self.dir
        if self.out:
            options["out"] = self.out
        if self.max_connection_per_server:
            options["max-connection-per-server"] = str(self.max_connection_per_server)
        if self.split:
            options["split"] = str(self.split)
        if self.max_download_limit:
            options["max-download-limit"] = str(self.max_download_limit)
        if self.header:
            options["header"] = self.header
        if self.user_agent:
            options["user-agent"] = self.user_agent
        return options


class ServiceError(Exception):
    """Base exception for service layer errors."""

    pass


class ConnectionError(ServiceError):
    """Connection-related errors."""

    pass


class DownloadOperationError(ServiceError):
    """Download operation errors."""

    pass


class Aria2Service:
    """Main service class coordinating all aria2 operations.

    This service provides a high-level API for:
    - Managing downloads (add, pause, resume, remove)
    - Managing RPC servers (connect, switch, health check)
    - Synchronizing state (auto-refresh, event-driven updates)
    - Handling notifications and events

    Example:
        service = Aria2Service()
        await service.initialize()

        # Add server and connect
        service.add_server("local", "ws://localhost:6800/jsonrpc")
        await service.connect()

        # Add download
        gid = await service.add_download(["http://example.com/file.zip"])

        # Start auto-refresh
        await service.start_auto_refresh()

        # Get downloads
        active = service.get_active_downloads()

        # Cleanup
        await service.shutdown()
    """

    def __init__(self, config_dir: Path | None = None):
        """Initialize the service.

        Args:
            config_dir: Optional custom config directory
        """
        # Managers
        self.config_mgr = ConfigManager(config_dir=config_dir)
        self.rpc_mgr = RPCManager()
        self.download_mgr = DownloadManager()
        self.event_mgr = EventManager()
        self.process_mgr = LocalProcessManager()

        # State
        self._initialized = False
        self._auto_refresh_task: asyncio.Task | None = None
        self._session_save_task: asyncio.Task | None = None
        self._refresh_interval = 1.0  # seconds

        # Track which queue each download belongs to (based on aria2 API)
        self._active_gids: set[str] = set()
        self._waiting_gids: set[str] = set()
        self._stopped_gids: set[str] = set()

        # Callbacks
        self._ui_refresh_callback: Callable[[], None] | None = None
        self._notification_callback: Callable[[dict[str, Any]], None] | None = None

        logger.info("Aria2Service created")

    # ==================== Lifecycle Management ====================

    async def initialize(self) -> None:
        """Initialize the service and load configuration.

        Raises:
            ServiceError: If initialization fails
        """
        if self._initialized:
            logger.warning("Service already initialized")
            return

        try:
            # Load configuration
            config = self.config_mgr.load()
            logger.info(f"Configuration loaded: {len(config.servers)} servers")

            # Load servers from config
            for server_data in config.servers:
                self.rpc_mgr.add_server(
                    name=server_data.get("name", "unknown"),
                    url=server_data.get("url", ""),
                    secret=server_data.get("secret"),
                )

            # Set current server if configured
            if config.current_server:
                self.rpc_mgr.switch_server(config.current_server)

            # Set refresh interval from config
            self._refresh_interval = config.refresh_interval / 1000.0  # ms to seconds

            self._initialized = True
            logger.info("Service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize service: {e}", exc_info=True)
            raise ServiceError(f"Initialization failed: {e}") from e

    async def connect(self, server_name: str | None = None) -> bool:
        """Connect to an aria2 RPC server.

        For local servers with auto_start_local enabled, automatically
        starts the aria2c process if not running.

        Args:
            server_name: Server name (uses current server if None)

        Returns:
            True if connected successfully

        Raises:
            ConnectionError: If connection fails
        """
        if not self._initialized:
            raise ServiceError("Service not initialized. Call initialize() first.")

        try:
            # Get server config
            server_config = self.rpc_mgr.get_server_config(server_name)

            # Auto-start local process if needed
            if server_config.is_local and self.config_mgr.get().auto_start_local:
                if not self.process_mgr.is_running(server_config.name):
                    logger.info(f"Auto-starting local aria2c for {server_config.name}")
                    await self._start_local_process(server_config)

            # Connect to RPC server
            connected = await self.rpc_mgr.connect(server_name)

            if not connected:
                state = self.rpc_mgr.get_server_state(server_name)
                error_msg = state.last_error if state else "Unknown error"
                raise ConnectionError(f"Failed to connect: {error_msg}")

            # Setup event manager if using WebSocket
            ws_client = self.rpc_mgr.get_websocket_client(server_name)
            if ws_client:
                self.event_mgr.set_client(ws_client)
                self._connect_event_handlers()
                logger.info("Event manager enabled (WebSocket connection)")
                # Still enable auto-refresh as backup for WebSocket
                await self.start_auto_refresh()
            else:
                self.event_mgr.disable()
                logger.info("Event manager disabled (HTTP connection)")
                # HTTP connection requires polling - start auto-refresh
                await self.start_auto_refresh()

            # Start auto-save session task
            self._start_auto_save_session()

            logger.info("Connected to server successfully")
            return True

        except Aria2Error as e:
            logger.error(f"aria2 RPC error: {e}")
            raise ConnectionError(f"RPC error: {e}") from e
        except Exception as e:
            logger.error(f"Connection error: {e}", exc_info=True)
            raise ConnectionError(f"Connection failed: {e}") from e

    async def disconnect(self, server_name: str | None = None) -> None:
        """Disconnect from an aria2 RPC server.

        Args:
            server_name: Server name (uses current server if None)
        """
        try:
            # Stop auto-save
            self._stop_auto_save_session()

            # Stop auto-refresh if running
            await self.stop_auto_refresh()

            # Disable event manager
            self.event_mgr.disable()

            # Disconnect RPC
            await self.rpc_mgr.disconnect(server_name)

            logger.info("Disconnected from server")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}", exc_info=True)

    async def _start_local_process(self, config: "ServerConfig") -> None:
        """Start local aria2c process."""
        from urllib.parse import urlparse

        # Extract port from URL
        parsed = urlparse(config.url)
        port = parsed.port or 6800

        success = await self.process_mgr.start_process(
            server_name=config.name,
            aria2c_path=config.aria2c_path,
            rpc_port=port,
            rpc_secret=config.secret,
            session_file=config.managed_session_file,
            options=config.aria2c_options,
        )

        if not success:
            raise ConnectionError(f"Failed to start local aria2c for {config.name}")

        # Wait for RPC to be ready
        await asyncio.sleep(2)

    async def stop_local_process(
        self,
        server_name: str | None = None,
        force: bool = False,
    ) -> bool:
        """Stop local aria2c process.

        Args:
            server_name: Server to stop (None = current server)
            force: Use force shutdown

        Returns:
            True if stopped successfully
        """
        name = server_name or self.rpc_mgr.current_server
        if not name:
            raise ServiceError("No server specified")

        config = self.rpc_mgr.get_server_config(name)
        if not config.is_local:
            raise ServiceError(f"Server {name} is not a local server")

        # Save session first (unless force)
        if not force:
            try:
                client = self.rpc_mgr.get_client()
                if client:
                    await client.save_session()
                    logger.info("Session saved before stopping process")
            except Exception as e:
                logger.warning(f"Failed to save session: {e}")

        return await self.process_mgr.stop_process(name, force=force)

    async def restart_local_process(self, server_name: str | None = None) -> bool:
        """Restart local aria2c process."""
        from urllib.parse import urlparse

        name = server_name or self.rpc_mgr.current_server
        if not name:
            raise ServiceError("No server specified")

        config = self.rpc_mgr.get_server_config(name)
        if not config.is_local:
            raise ServiceError(f"Server {name} is not a local server")

        # Extract port
        parsed = urlparse(config.url)
        port = parsed.port or 6800

        return await self.process_mgr.restart_process(
            server_name=config.name,
            aria2c_path=config.aria2c_path,
            rpc_port=port,
            rpc_secret=config.secret,
            session_file=config.managed_session_file,
            options=config.aria2c_options,
        )

    def get_local_process_info(self, server_name: str | None = None):
        """Get local process info."""
        name = server_name or self.rpc_mgr.current_server
        if not name:
            return None
        return self.process_mgr.get_process_info(name)

    async def save_session(self) -> bool:
        """Save current session to file.

        Returns:
            True if saved successfully
        """
        try:
            client = self.rpc_mgr.get_client()
            if not client:
                return False
            result = await client.save_session()
            logger.info(f"Session saved: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False

    def _start_auto_save_session(self) -> None:
        """Start auto-save session background task."""
        interval = self.config_mgr.get().auto_save_session_interval
        if not interval or interval <= 0:
            return

        if self._session_save_task and not self._session_save_task.done():
            return  # Already running

        async def auto_save() -> None:
            while True:
                await asyncio.sleep(interval)
                try:
                    await self.save_session()
                except Exception as e:
                    logger.error(f"Auto-save session failed: {e}")

        self._session_save_task = asyncio.create_task(auto_save())
        logger.info(f"Auto-save session started (interval: {interval}s)")

    def _stop_auto_save_session(self) -> None:
        """Stop auto-save session task."""
        if self._session_save_task:
            self._session_save_task.cancel()
            self._session_save_task = None

    async def shutdown(self) -> None:
        """Shutdown the service and cleanup resources."""
        try:
            logger.info("Shutting down service...")

            # Stop auto-save
            self._stop_auto_save_session()

            # Stop auto-refresh
            await self.stop_auto_refresh()

            # Cleanup local processes
            await self.process_mgr.cleanup()

            # Disconnect from all servers
            await self.disconnect()

            # Save configuration
            self.config_mgr.save()

            self._initialized = False
            logger.info("Service shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

    # ==================== Server Management ====================

    def add_server(self, name: str, url: str, secret: str | None = None) -> None:
        """Add a new aria2 RPC server.

        Args:
            name: Unique server name
            url: RPC endpoint URL (ws://, wss://, http://, https://)
            secret: Optional RPC secret token
        """
        self.rpc_mgr.add_server(name, url, secret)

        # Save to config
        config = self.config_mgr.get()
        config.servers.append({"name": name, "url": url, "secret": secret})
        self.config_mgr.save()

        logger.info(f"Server '{name}' added")

    def remove_server(self, name: str) -> None:
        """Remove a server.

        Args:
            name: Server name to remove
        """
        self.rpc_mgr.remove_server(name)

        # Remove from config
        config = self.config_mgr.get()
        config.servers = [s for s in config.servers if s.get("name") != name]
        self.config_mgr.save()

        logger.info(f"Server '{name}' removed")

    async def switch_server(self, name: str) -> bool:
        """Switch to a different server.

        Args:
            name: Server name to switch to

        Returns:
            True if switched and connected successfully
        """
        # Disconnect from current server
        await self.disconnect()

        # Switch server
        if not self.rpc_mgr.switch_server(name):
            return False

        # Update config
        config = self.config_mgr.get()
        config.current_server = name
        self.config_mgr.save()

        # Connect to new server
        return await self.connect(name)

    def list_servers(self) -> list[dict[str, Any]]:
        """Get list of all servers with their states.

        Returns:
            List of server info dicts
        """
        servers = []
        for server_config in self.rpc_mgr.list_servers():
            state = self.rpc_mgr.get_server_state(server_config.name)
            servers.append(
                {
                    "name": server_config.name,
                    "url": server_config.url,
                    "protocol": server_config.protocol.value,
                    "is_websocket": server_config.is_websocket,
                    "state": state.state.value if state else "unknown",
                    "last_error": state.last_error if state else None,
                    "is_current": self.rpc_mgr.current_server == server_config.name,
                }
            )
        return servers

    async def test_connection(self, name: str | None = None) -> bool:
        """Test if connection to server is healthy.

        Args:
            name: Server name (uses current server if None)

        Returns:
            True if connection is healthy
        """
        return await self.rpc_mgr.health_check(name)

    # ==================== Download Operations ====================

    async def add_download(
        self, uris: list[str], options: DownloadOptions | dict[str, Any] | None = None
    ) -> str:
        """Add a new download from URIs.

        Args:
            uris: List of URIs (HTTP/HTTPS/FTP)
            options: Optional download options (DownloadOptions object or dict)

        Returns:
            GID of the added download

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            # Convert options to dict if it's a DownloadOptions object
            if isinstance(options, DownloadOptions):
                opts = options.to_dict()
            elif isinstance(options, dict):
                opts = options
            else:
                opts = {}

            gid = await client.add_uri(uris, options=opts)

            logger.info(f"Download added: {gid} ({uris[0]})")

            # Trigger immediate refresh to update UI
            await self.refresh_download(gid)

            return gid

        except Aria2Error as e:
            logger.error(f"Failed to add download: {e}")
            raise DownloadOperationError(f"Failed to add download: {e}") from e

    async def add_torrent(
        self, torrent: bytes, uris: list[str] | None = None, options: DownloadOptions | None = None
    ) -> str:
        """Add a BitTorrent download.

        Args:
            torrent: Torrent file content (base64 encoded)
            uris: Optional web seed URIs
            options: Optional download options

        Returns:
            GID of the added download

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            opts = options.to_dict() if options else {}
            gid = await client.add_torrent(torrent, uris=uris or [], options=opts)

            logger.info(f"Torrent added: {gid}")

            # Trigger immediate refresh
            await self.refresh_download(gid)

            return gid

        except Aria2Error as e:
            logger.error(f"Failed to add torrent: {e}")
            raise DownloadOperationError(f"Failed to add torrent: {e}") from e

    async def pause_download(self, gid: str) -> bool:
        """Pause a download.

        Args:
            gid: Download GID

        Returns:
            True if paused successfully

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            result_gid = await client.pause(gid)
            logger.info(f"Download paused: {gid}")

            # Update local state
            await self.refresh_download(gid)

            return result_gid == gid

        except Aria2Error as e:
            logger.error(f"Failed to pause download: {e}")
            raise DownloadOperationError(f"Failed to pause: {e}") from e

    async def resume_download(self, gid: str) -> bool:
        """Resume a paused download.

        Args:
            gid: Download GID

        Returns:
            True if resumed successfully

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            result_gid = await client.unpause(gid)
            logger.info(f"Download resumed: {gid}")

            # Update local state
            await self.refresh_download(gid)

            return result_gid == gid

        except Aria2Error as e:
            logger.error(f"Failed to resume download: {e}")
            raise DownloadOperationError(f"Failed to resume: {e}") from e

    async def retry_download(self, gid: str) -> str:
        """Retry a failed/error download.

        This removes the failed download and re-adds it with the same URIs and options.

        Args:
            gid: Download GID to retry

        Returns:
            New GID of the retried download

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            # Get current download info
            download = self.download_mgr.get_download(gid)
            if not download:
                raise DownloadOperationError(f"Download {gid} not found")

            # Get URIs from the download
            uris = download.urls
            if not uris:
                raise DownloadOperationError(f"No URIs found for download {gid}")

            # Get current options (if available)
            try:
                options = await client.get_option(gid)
            except Aria2Error:
                options = {}

            # Remove the failed download
            try:
                await self.remove_download(gid, force=True)
            except Exception as e:
                logger.warning(f"Failed to remove download before retry: {e}")
                # Continue anyway - the download might already be removed

            # Re-add the download with same URIs and options
            new_gid = await client.add_uri(uris, options=options)
            logger.info(f"Download retried: old={gid}, new={new_gid}")

            # Trigger immediate refresh to update UI
            await self.refresh_download(new_gid)

            return new_gid

        except Aria2Error as e:
            logger.error(f"Failed to retry download: {e}")
            raise DownloadOperationError(f"Failed to retry: {e}") from e

    async def remove_download(self, gid: str, force: bool = False) -> bool:
        """Remove a download.

        This method intelligently chooses the correct aria2 RPC method based on
        the download's current state:
        - Active/Waiting downloads: use remove() or force_remove()
        - Stopped downloads (complete/error/removed): use remove_download_result()

        Args:
            gid: Download GID
            force: If True, use force_remove for active/waiting downloads

        Returns:
            True if removed successfully

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            # Determine which queue the download is in
            is_active_or_waiting = gid in self._active_gids or gid in self._waiting_gids
            is_stopped = gid in self._stopped_gids

            if is_active_or_waiting:
                # Active or waiting download - use remove/force_remove
                if force:
                    result_gid = await client.force_remove(gid)
                else:
                    result_gid = await client.remove(gid)
                logger.info(f"Download removed from active/waiting: {gid}")
            elif is_stopped:
                # Stopped download (complete/error/removed) - use remove_download_result
                result_gid = await client.remove_download_result(gid)
                logger.info(f"Download result removed: {gid}")
            else:
                # Unknown state - try both methods
                logger.warning(f"Download {gid} not in any tracked queue, trying both methods")
                try:
                    if force:
                        result_gid = await client.force_remove(gid)
                    else:
                        result_gid = await client.remove(gid)
                    logger.info(f"Download removed via remove: {gid}")
                except Aria2Error:
                    # If remove fails, try remove_download_result
                    result_gid = await client.remove_download_result(gid)
                    logger.info(f"Download removed via remove_download_result: {gid}")

            # Remove from local state immediately
            self.download_mgr.remove_download(gid)

            # Also remove from queue tracking
            self._active_gids.discard(gid)
            self._waiting_gids.discard(gid)
            self._stopped_gids.discard(gid)

            # Trigger refresh to update UI
            await self.refresh_downloads()

            return result_gid == gid

        except Aria2Error as e:
            logger.error(f"Failed to remove download {gid}: {e}")
            raise DownloadOperationError(f"Failed to remove: {e}") from e

    # ==================== Batch Operations ====================

    async def pause_all(self) -> list[str]:
        """Pause all active downloads.

        Returns:
            List of GIDs that were paused

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            result_gid = await client.pause_all()
            logger.info("All downloads paused")

            # Trigger refresh
            await self.refresh_downloads()

            return [result_gid]

        except Aria2Error as e:
            logger.error(f"Failed to pause all: {e}")
            raise DownloadOperationError(f"Failed to pause all: {e}") from e

    async def resume_all(self) -> list[str]:
        """Resume all paused downloads.

        Returns:
            List of GIDs that were resumed

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            result_gid = await client.unpause_all()
            logger.info("All downloads resumed")

            # Trigger refresh
            await self.refresh_downloads()

            return [result_gid]

        except Aria2Error as e:
            logger.error(f"Failed to resume all: {e}")
            raise DownloadOperationError(f"Failed to resume all: {e}") from e

    async def purge_completed(self) -> bool:
        """Remove completed/error/removed downloads from result list.

        Returns:
            True if successful

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            await client.purge_download_result()
            logger.info("Download results purged")

            # Trigger refresh
            await self.refresh_downloads()

            return True

        except Aria2Error as e:
            logger.error(f"Failed to purge results: {e}")
            raise DownloadOperationError(f"Failed to purge: {e}") from e

    # ==================== State Synchronization ====================

    async def refresh_downloads(self) -> None:
        """Refresh all downloads from aria2.

        This fetches the current state of all downloads from aria2 and updates
        the local DownloadManager.
        """
        client = self.rpc_mgr.get_client()
        if not client:
            return

        try:
            # Fetch all download types
            active = await client.tell_active()
            waiting = await client.tell_waiting(0, 1000)
            stopped = await client.tell_stopped(0, 1000)

            # Clear and rebuild queue tracking
            self._active_gids.clear()
            self._waiting_gids.clear()
            self._stopped_gids.clear()

            # Collect all valid GIDs from aria2
            valid_gids = set()

            # Update download manager and track queues
            # Use raw data to pass all fields including dir, files, uris, etc.
            for status in active:
                self._active_gids.add(status.gid)
                valid_gids.add(status.gid)
                self.download_mgr.update_download(status.gid, status.raw)

            for status in waiting:
                self._waiting_gids.add(status.gid)
                valid_gids.add(status.gid)
                self.download_mgr.update_download(status.gid, status.raw)

            for status in stopped:
                # Skip downloads with "removed" status
                if status.raw.get("status") == "removed":
                    logger.debug(f"Skipping removed download: {status.gid}")
                    continue
                self._stopped_gids.add(status.gid)
                valid_gids.add(status.gid)
                self.download_mgr.update_download(status.gid, status.raw)

            # Clean up downloads that are no longer in any queue
            # (e.g., removed downloads, purged downloads)
            current_gids = set(self.download_mgr.downloads.keys())
            removed_gids = current_gids - valid_gids
            for gid in removed_gids:
                self.download_mgr.remove_download(gid)
                logger.debug(f"Cleaned up removed download: {gid}")

            # Notify UI
            if self._ui_refresh_callback:
                self._ui_refresh_callback()

        except Aria2Error as e:
            logger.warning(f"Failed to refresh downloads: {e}")
        except Exception as e:
            logger.error(f"Error refreshing downloads: {e}", exc_info=True)

    async def refresh_download(self, gid: str) -> None:
        """Refresh a single download.

        Args:
            gid: Download GID to refresh
        """
        client = self.rpc_mgr.get_client()
        if not client:
            return

        try:
            status = await client.tell_status(gid)

            # Use raw data to pass all fields
            self.download_mgr.update_download(status.gid, status.raw)

            # Notify UI
            if self._ui_refresh_callback:
                self._ui_refresh_callback()

        except Aria2Error as e:
            logger.warning(f"Failed to refresh download {gid}: {e}")

    async def start_auto_refresh(self, interval: float | None = None) -> None:
        """Start automatic periodic refresh.

        Args:
            interval: Refresh interval in seconds (uses config default if None)
        """
        if self._auto_refresh_task and not self._auto_refresh_task.done():
            logger.warning("Auto-refresh already running")
            return

        if interval:
            self._refresh_interval = interval

        self._auto_refresh_task = asyncio.create_task(self._auto_refresh_loop())
        logger.info(f"Auto-refresh started (interval: {self._refresh_interval}s)")

    async def stop_auto_refresh(self) -> None:
        """Stop automatic refresh."""
        if self._auto_refresh_task:
            self._auto_refresh_task.cancel()
            try:
                await self._auto_refresh_task
            except asyncio.CancelledError:
                pass
            self._auto_refresh_task = None
            logger.info("Auto-refresh stopped")

    async def _auto_refresh_loop(self) -> None:
        """Background task for automatic refresh."""
        while True:
            try:
                await asyncio.sleep(self._refresh_interval)
                await self.refresh_downloads()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-refresh loop: {e}", exc_info=True)

    # ==================== Event Handling ====================

    def _connect_event_handlers(self) -> None:
        """Connect event manager handlers for state updates."""

        async def on_download_complete(event_data: dict[str, Any]) -> None:
            """Handle download complete event."""
            gid = event_data.get("gid")
            logger.info(f"Download completed: {gid}")

            # Refresh download state
            if gid:
                await self.refresh_download(gid)

        async def on_download_error(event_data: dict[str, Any]) -> None:
            """Handle download error event."""
            gid = event_data.get("gid")
            logger.error(f"Download error: {gid}")

            # Refresh download state
            if gid:
                await self.refresh_download(gid)

        async def on_download_start(event_data: dict[str, Any]) -> None:
            """Handle download start event."""
            gid = event_data.get("gid")
            logger.info(f"Download started: {gid}")

            # Refresh download state
            if gid:
                await self.refresh_download(gid)

        async def on_download_pause(event_data: dict[str, Any]) -> None:
            """Handle download pause event."""
            gid = event_data.get("gid")
            logger.info(f"Download paused: {gid}")

            # Refresh download state
            if gid:
                await self.refresh_download(gid)

        async def on_download_stop(event_data: dict[str, Any]) -> None:
            """Handle download stop event."""
            gid = event_data.get("gid")
            logger.info(f"Download stopped: {gid}")

            # Refresh download state
            if gid:
                await self.refresh_download(gid)

        # Register event handlers
        self.event_mgr.on(Aria2Event.DOWNLOAD_COMPLETE, on_download_complete)
        self.event_mgr.on(Aria2Event.DOWNLOAD_ERROR, on_download_error)
        self.event_mgr.on(Aria2Event.DOWNLOAD_START, on_download_start)
        self.event_mgr.on(Aria2Event.DOWNLOAD_PAUSE, on_download_pause)
        self.event_mgr.on(Aria2Event.DOWNLOAD_STOP, on_download_stop)

        # Set notification handler if callback is registered
        if self._notification_callback:
            self.event_mgr.set_notification_handler(self._notification_callback)

        logger.info("Event handlers connected")

    def set_ui_refresh_callback(self, callback: Callable[[], None]) -> None:
        """Set callback to be called when UI should refresh.

        Args:
            callback: Function to call on UI refresh
        """
        self._ui_refresh_callback = callback

    def set_notification_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Set callback for notifications.

        Args:
            callback: Function to call with notification data
        """
        self._notification_callback = callback
        if self.event_mgr.is_active():
            self.event_mgr.set_notification_handler(callback)

    # ==================== Query Methods ====================

    def get_active_downloads(self) -> list[Download]:
        """Get all active downloads (from aria2's active queue).

        Returns:
            List of Download objects
        """
        return [d for d in self.download_mgr.get_all_downloads() if d.gid in self._active_gids]

    def get_waiting_downloads(self) -> list[Download]:
        """Get all waiting downloads (from aria2's waiting queue).

        Returns:
            List of Download objects
        """
        return [d for d in self.download_mgr.get_all_downloads() if d.gid in self._waiting_gids]

    def get_paused_downloads(self) -> list[Download]:
        """Get all paused downloads.

        Returns:
            List of Download objects
        """
        return self.download_mgr.get_downloads_by_status(DownloadStatus.PAUSED)

    def get_stopped_downloads(self) -> list[Download]:
        """Get all stopped downloads (from aria2's stopped queue).

        Returns:
            List of Download objects
        """
        return [d for d in self.download_mgr.get_all_downloads() if d.gid in self._stopped_gids]

    def get_download(self, gid: str) -> Download | None:
        """Get a specific download by GID.

        Args:
            gid: Download GID

        Returns:
            Download object or None if not found
        """
        return self.download_mgr.get_download(gid)

    async def get_global_stat(self) -> GlobalStat | None:
        """Get global statistics from aria2.

        Returns:
            GlobalStat object or None if not connected
        """
        client = self.rpc_mgr.get_client()
        if not client:
            return None

        try:
            return await client.get_global_stat()
        except Aria2Error as e:
            logger.warning(f"Failed to get global stats: {e}")
            return None

    async def get_version(self) -> Version | None:
        """Get aria2 version information.

        Returns:
            Version object or None if not connected
        """
        client = self.rpc_mgr.get_client()
        if not client:
            return None

        try:
            return await client.get_version()
        except Aria2Error as e:
            logger.warning(f"Failed to get version: {e}")
            return None

    # ==================== Status Properties ====================

    @property
    def is_connected(self) -> bool:
        """Check if connected to a server."""
        state = self.rpc_mgr.get_server_state()
        return state is not None and state.state == ConnectionState.CONNECTED

    @property
    def current_server(self) -> str | None:
        """Get current server name."""
        return self.rpc_mgr.current_server

    @property
    def is_websocket(self) -> bool:
        """Check if current connection is WebSocket."""
        return self.rpc_mgr.is_websocket()

    @property
    def event_monitoring_active(self) -> bool:
        """Check if event monitoring is active."""
        return self.event_mgr.is_active()

    # ==================== Queue Management ====================

    async def change_position(self, gid: str, pos: int, how: str = "POS_SET") -> int:
        """Change the position of a download in the queue.

        Args:
            gid: Download GID
            pos: Position (0-based)
            how: How to interpret pos:
                - "POS_SET": Set to absolute position
                - "POS_CUR": Move relative to current position
                - "POS_END": Move relative to end of queue

        Returns:
            New position

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            new_pos = await client.change_position(gid, pos, how)
            logger.info(f"Download {gid} moved to position {new_pos}")

            # Trigger refresh
            await self.refresh_downloads()

            return new_pos

        except Aria2Error as e:
            logger.error(f"Failed to change position: {e}")
            raise DownloadOperationError(f"Failed to change position: {e}") from e

    async def move_to_top(self, gid: str) -> int:
        """Move a download to the top of the queue.

        Args:
            gid: Download GID

        Returns:
            New position (should be 0)

        Raises:
            DownloadOperationError: If operation fails
        """
        return await self.change_position(gid, 0, "POS_SET")

    async def move_to_bottom(self, gid: str) -> int:
        """Move a download to the bottom of the queue.

        Args:
            gid: Download GID

        Returns:
            New position

        Raises:
            DownloadOperationError: If operation fails
        """
        return await self.change_position(gid, -1, "POS_END")

    async def move_up(self, gid: str, step: int = 1) -> int:
        """Move a download up in the queue.

        Args:
            gid: Download GID
            step: Number of positions to move up

        Returns:
            New position

        Raises:
            DownloadOperationError: If operation fails
        """
        return await self.change_position(gid, -step, "POS_CUR")

    async def move_down(self, gid: str, step: int = 1) -> int:
        """Move a download down in the queue.

        Args:
            gid: Download GID
            step: Number of positions to move down

        Returns:
            New position

        Raises:
            DownloadOperationError: If operation fails
        """
        return await self.change_position(gid, step, "POS_CUR")

    # ==================== Settings Management ====================

    async def get_global_options(self) -> dict[str, Any]:
        """Get global aria2 options.

        Returns:
            Dict of option key-value pairs

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            options = await client.get_global_option()
            return options

        except Aria2Error as e:
            logger.error(f"Failed to get global options: {e}")
            raise DownloadOperationError(f"Failed to get options: {e}") from e

    async def change_global_option(self, options: dict[str, Any]) -> bool:
        """Change global aria2 options.

        Args:
            options: Dict of option key-value pairs to change

        Returns:
            True if successful

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            await client.change_global_option(options)
            logger.info(f"Global options changed: {list(options.keys())}")
            return True

        except Aria2Error as e:
            logger.error(f"Failed to change global options: {e}")
            raise DownloadOperationError(f"Failed to change options: {e}") from e

    async def get_download_options(self, gid: str) -> dict[str, Any]:
        """Get options for a specific download.

        Args:
            gid: Download GID

        Returns:
            Dict of option key-value pairs

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            options = await client.get_option(gid)
            return options

        except Aria2Error as e:
            logger.error(f"Failed to get download options: {e}")
            raise DownloadOperationError(f"Failed to get options: {e}") from e

    async def change_download_option(self, gid: str, options: dict[str, Any]) -> bool:
        """Change options for a specific download.

        Args:
            gid: Download GID
            options: Dict of option key-value pairs to change

        Returns:
            True if successful

        Raises:
            DownloadOperationError: If operation fails
        """
        client = self.rpc_mgr.get_client()
        if not client:
            raise DownloadOperationError("Not connected to any server")

        try:
            await client.change_option(gid, options)
            logger.info(f"Download {gid} options changed: {list(options.keys())}")
            return True

        except Aria2Error as e:
            logger.error(f"Failed to change download options: {e}")
            raise DownloadOperationError(f"Failed to change options: {e}") from e

    # ==================== Configuration Management ====================

    def get_app_config(self) -> Any:
        """Get current application configuration.

        Returns:
            AppConfig instance
        """
        return self.config_mgr.get()

    def update_app_config(self, **kwargs) -> None:
        """Update application configuration.

        Args:
            **kwargs: Configuration fields to update
        """
        self.config_mgr.update(**kwargs)
        logger.info(f"App config updated: {list(kwargs.keys())}")

        # If refresh_interval changed, restart auto-refresh if active
        if "refresh_interval" in kwargs and self._auto_refresh_task:
            asyncio.create_task(self._restart_auto_refresh())

    async def _restart_auto_refresh(self) -> None:
        """Restart auto-refresh with new interval."""
        await self.stop_auto_refresh()
        await self.start_auto_refresh()

    def save_config(self) -> None:
        """Explicitly save configuration to disk."""
        self.config_mgr.save()
        logger.info("Configuration saved")
