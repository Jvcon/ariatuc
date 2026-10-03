"""Base class for aria2 RPC clients.

This module provides the abstract base class that contains all common RPC method
implementations. Protocol-specific clients (HTTP, WebSocket) inherit from this
base and only need to implement the _call() method.
"""

from abc import ABC, abstractmethod
from typing import Any

from aria2rpc.models import DownloadStatus, FileServer, GlobalStat, Peer, Version


class BaseRPCClient(ABC):
    """Abstract base class for aria2 RPC clients.

    This class contains all RPC method implementations that are common across
    different protocol implementations (HTTP, WebSocket). Subclasses only need
    to implement the _call() method with their protocol-specific logic.

    The _call() method should handle:
    - Authentication (token injection)
    - Request serialization
    - Network communication
    - Response deserialization
    - Error handling

    Example subclass:
        class MyRPCClient(BaseRPCClient):
            async def _call(self, method: str, params: list[Any] | None = None) -> Any:
                # Protocol-specific implementation
                pass
    """

    @abstractmethod
    async def _call(
        self, method: str, params: list[Any] | None = None, timeout: float | None = None
    ) -> Any:
        """Make a JSON-RPC call to aria2.

        This is the only method that subclasses must implement. It should handle
        all protocol-specific details of making an RPC call.

        Args:
            method: The RPC method name (e.g., 'aria2.addUri')
            params: List of parameters for the method
            timeout: Optional timeout for this specific call (overrides default)

        Returns:
            The result from the RPC call

        Raises:
            Aria2ConnectionError: If connection to aria2 fails
            Aria2TimeoutError: If request times out
            Aria2AuthenticationError: If authentication fails
            Aria2RPCError: If aria2 returns an error
        """
        pass

    # Download Control Methods

    async def add_uri(
        self,
        uris: list[str],
        options: dict[str, Any] | None = None,
        position: int | None = None,
    ) -> str:
        """Add a new download with URIs.

        Args:
            uris: List of HTTP/FTP URIs
            options: Download options (see aria2 documentation)
            position: Position in queue

        Returns:
            GID (download ID) of the newly added download

        Raises:
            Aria2RPCError: If adding download fails
        """
        params: list[Any] = [uris]
        if options:
            params.append(options)
        if position is not None:
            params.append(position)

        return await self._call("aria2.addUri", params)

    async def add_torrent(
        self,
        torrent: bytes,
        uris: list[str] | None = None,
        options: dict[str, Any] | None = None,
        position: int | None = None,
    ) -> str:
        """Add a BitTorrent download.

        Args:
            torrent: The content of the .torrent file (raw bytes)
            uris: List of web seed URIs (optional)
            options: Download options (see aria2 documentation)
            position: Position in queue

        Returns:
            GID (download ID) of the newly added download

        Raises:
            Aria2RPCError: If adding download fails

        Example:
            with open("file.torrent", "rb") as f:
                torrent_data = f.read()
            gid = await client.add_torrent(torrent_data)
        """
        import base64

        # Encode torrent file to base64
        torrent_b64 = base64.b64encode(torrent).decode("ascii")

        params: list[Any] = [torrent_b64]
        if uris:
            params.append(uris)
        elif options or position is not None:
            # If uris not provided but options/position are, add empty list
            params.append([])

        if options:
            params.append(options)
        if position is not None:
            if not options:
                # If options not provided but position is, add empty dict
                params.append({})
            params.append(position)

        return await self._call("aria2.addTorrent", params)

    async def add_metalink(
        self,
        metalink: bytes,
        options: dict[str, Any] | None = None,
        position: int | None = None,
    ) -> list[str]:
        """Add a Metalink download.

        Args:
            metalink: The content of the .metalink file (raw bytes)
            options: Download options (see aria2 documentation)
            position: Position in queue

        Returns:
            List of GIDs (one for each file in the metalink)

        Raises:
            Aria2RPCError: If adding download fails

        Example:
            with open("file.metalink", "rb") as f:
                metalink_data = f.read()
            gids = await client.add_metalink(metalink_data)
        """
        import base64

        # Encode metalink file to base64
        metalink_b64 = base64.b64encode(metalink).decode("ascii")

        params: list[Any] = [metalink_b64]
        if options:
            params.append(options)
        if position is not None:
            if not options:
                # If options not provided but position is, add empty dict
                params.append({})
            params.append(position)

        return await self._call("aria2.addMetalink", params)

    async def remove(self, gid: str) -> str:
        """Remove a download.

        Args:
            gid: The GID of the download

        Returns:
            The GID of the removed download

        Raises:
            Aria2RPCError: If removing download fails
        """
        return await self._call("aria2.remove", [gid])

    async def force_remove(self, gid: str) -> str:
        """Force remove a download.

        Args:
            gid: The GID of the download

        Returns:
            The GID of the removed download

        Raises:
            Aria2RPCError: If removing download fails
        """
        return await self._call("aria2.forceRemove", [gid])

    async def pause(self, gid: str) -> str:
        """Pause a download.

        Args:
            gid: The GID of the download

        Returns:
            The GID of the paused download

        Raises:
            Aria2RPCError: If pausing download fails
        """
        return await self._call("aria2.pause", [gid])

    async def pause_all(self) -> str:
        """Pause all active/waiting downloads.

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If pausing downloads fails
        """
        return await self._call("aria2.pauseAll")

    async def force_pause(self, gid: str) -> str:
        """Force pause a download.

        Args:
            gid: The GID of the download

        Returns:
            The GID of the paused download

        Raises:
            Aria2RPCError: If pausing download fails
        """
        return await self._call("aria2.forcePause", [gid])

    async def force_pause_all(self) -> str:
        """Force pause all active/waiting downloads.

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If pausing downloads fails
        """
        return await self._call("aria2.forcePauseAll")

    async def unpause(self, gid: str) -> str:
        """Unpause a download.

        Args:
            gid: The GID of the download

        Returns:
            The GID of the unpaused download

        Raises:
            Aria2RPCError: If unpausing download fails
        """
        return await self._call("aria2.unpause", [gid])

    async def unpause_all(self) -> str:
        """Unpause all paused downloads.

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If unpausing downloads fails
        """
        return await self._call("aria2.unpauseAll")

    # Status & Information Methods

    async def tell_status(self, gid: str, keys: list[str] | None = None) -> DownloadStatus:
        """Get status of a download.

        Args:
            gid: The GID of the download
            keys: List of keys to retrieve (None for all)

        Returns:
            Download status information

        Raises:
            Aria2RPCError: If fetching status fails
        """
        params: list[Any] = [gid]
        if keys:
            params.append(keys)

        result = await self._call("aria2.tellStatus", params)
        return DownloadStatus(result)

    async def tell_active(self, keys: list[str] | None = None) -> list[DownloadStatus]:
        """Get list of active downloads.

        Args:
            keys: List of keys to retrieve (None for all)

        Returns:
            List of active downloads

        Raises:
            Aria2RPCError: If fetching downloads fails
        """
        params = [keys] if keys else []
        result = await self._call("aria2.tellActive", params)
        return [DownloadStatus(item) for item in result]

    async def tell_waiting(
        self, offset: int, num: int, keys: list[str] | None = None
    ) -> list[DownloadStatus]:
        """Get list of waiting downloads.

        Args:
            offset: Offset from the start
            num: Number of downloads to retrieve
            keys: List of keys to retrieve (None for all)

        Returns:
            List of waiting downloads

        Raises:
            Aria2RPCError: If fetching downloads fails
        """
        params: list[Any] = [offset, num]
        if keys:
            params.append(keys)

        result = await self._call("aria2.tellWaiting", params)
        return [DownloadStatus(item) for item in result]

    async def tell_stopped(
        self, offset: int, num: int, keys: list[str] | None = None
    ) -> list[DownloadStatus]:
        """Get list of stopped downloads.

        Args:
            offset: Offset from the start
            num: Number of downloads to retrieve
            keys: List of keys to retrieve (None for all)

        Returns:
            List of stopped downloads

        Raises:
            Aria2RPCError: If fetching downloads fails
        """
        params: list[Any] = [offset, num]
        if keys:
            params.append(keys)

        result = await self._call("aria2.tellStopped", params)
        return [DownloadStatus(item) for item in result]

    async def get_uris(self, gid: str) -> list[dict[str, Any]]:
        """Get URIs used in a download.

        Args:
            gid: The GID of the download

        Returns:
            List of URI information

        Raises:
            Aria2RPCError: If fetching URIs fails
        """
        return await self._call("aria2.getUris", [gid])

    async def get_files(self, gid: str) -> list[dict[str, Any]]:
        """Get file list of a download.

        Args:
            gid: The GID of the download

        Returns:
            List of file information

        Raises:
            Aria2RPCError: If fetching files fails
        """
        return await self._call("aria2.getFiles", [gid])

    async def get_peers(self, gid: str) -> list[Peer]:
        """Get peer list of a BitTorrent download.

        Args:
            gid: The GID of the download

        Returns:
            List of peer information (BitTorrent only)

        Raises:
            Aria2RPCError: If fetching peers fails

        Note:
            This method only works for BitTorrent downloads.
            For non-BitTorrent downloads, it returns an empty list.
        """
        result = await self._call("aria2.getPeers", [gid])
        return [Peer(peer) for peer in result]

    async def get_servers(self, gid: str) -> list[FileServer]:
        """Get server/tracker list of a download.

        Args:
            gid: The GID of the download

        Returns:
            List of servers grouped by file index

        Raises:
            Aria2RPCError: If fetching servers fails

        Note:
            For BitTorrent downloads, this returns tracker information.
            For HTTP/FTP downloads, this returns mirror/source server information.
        """
        result = await self._call("aria2.getServers", [gid])
        return [FileServer(item) for item in result]

    async def get_global_stat(self) -> GlobalStat:
        """Get global statistics.

        Returns:
            Global statistics including download/upload speeds

        Raises:
            Aria2RPCError: If fetching statistics fails
        """
        result = await self._call("aria2.getGlobalStat")
        return GlobalStat(result)

    async def get_version(self) -> Version:
        """Get aria2 version.

        Returns:
            Version information

        Raises:
            Aria2RPCError: If fetching version fails
        """
        result = await self._call("aria2.getVersion")
        return Version(result)

    async def get_session_info(self) -> dict[str, Any]:
        """Get session information.

        Returns:
            Session information including session ID

        Raises:
            Aria2RPCError: If fetching session info fails
        """
        return await self._call("aria2.getSessionInfo")

    # Configuration Management Methods

    async def get_option(self, gid: str) -> dict[str, Any]:
        """Get options of a download.

        Args:
            gid: The GID of the download

        Returns:
            Dictionary of option name-value pairs with proper Python types

        Raises:
            Aria2RPCError: If fetching options fails
        """
        from aria2rpc.option_types import parse_options_dict

        raw_options = await self._call("aria2.getOption", [gid])
        return parse_options_dict(raw_options)

    async def change_option(self, gid: str, options: dict[str, Any]) -> str:
        """Change options of a download dynamically.

        Args:
            gid: The GID of the download
            options: Dictionary of options to change (can use Python native types)

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If changing options fails

        Note:
            Not all options can be changed after download is added.
            See aria2 documentation for changeable options.
        """
        from aria2rpc.option_types import format_options_dict

        formatted_options = format_options_dict(options)
        return await self._call("aria2.changeOption", [gid, formatted_options])

    async def get_global_option(self) -> dict[str, Any]:
        """Get global options.

        Returns:
            Dictionary of global option name-value pairs with proper Python types
            (booleans as True/False, integers as int, etc.)

        Raises:
            Aria2RPCError: If fetching global options fails
        """
        from aria2rpc.option_types import parse_options_dict

        raw_options = await self._call("aria2.getGlobalOption")
        return parse_options_dict(raw_options)

    async def change_global_option(self, options: dict[str, Any]) -> str:
        """Change global options dynamically.

        Args:
            options: Dictionary of global options to change (can use Python native types:
                    booleans as True/False, integers as int, etc. - will be converted
                    automatically to aria2 string format)

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If changing global options fails
        """
        from aria2rpc.option_types import format_options_dict

        # Convert Python types to aria2 string format
        formatted_options = format_options_dict(options)
        return await self._call("aria2.changeGlobalOption", [formatted_options])

    # Queue Management Methods

    async def change_position(self, gid: str, pos: int, how: str) -> int:
        """Change the position of a download in the queue.

        Args:
            gid: The GID of the download
            pos: Position to move the download to
            how: How to interpret pos:
                - 'POS_SET': Set position to pos (absolute)
                - 'POS_CUR': Move pos positions relative to current
                - 'POS_END': Move pos positions from the end

        Returns:
            The resulting position (0-indexed)

        Raises:
            Aria2RPCError: If changing position fails
        """
        return await self._call("aria2.changePosition", [gid, pos, how])

    async def change_uri(
        self,
        gid: str,
        file_index: int,
        del_uris: list[str],
        add_uris: list[str],
        position: int | None = None,
    ) -> tuple[int, int]:
        """Change URIs for a download.

        Args:
            gid: The GID of the download
            file_index: Index of the file (1-based)
            del_uris: URIs to remove
            add_uris: URIs to add
            position: Position to insert new URIs (optional)

        Returns:
            Tuple of (deleted_count, added_count)

        Raises:
            Aria2RPCError: If changing URIs fails
        """
        params: list[Any] = [gid, file_index, del_uris, add_uris]
        if position is not None:
            params.append(position)

        result = await self._call("aria2.changeUri", params)
        return (result[0], result[1])

    # Download Result Management Methods

    async def purge_download_result(self) -> str:
        """Purge completed/error/removed downloads from memory.

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If purging fails

        Note:
            This method removes download results from memory to free space.
            It does not affect active or waiting downloads.
        """
        return await self._call("aria2.purgeDownloadResult")

    async def remove_download_result(self, gid: str) -> str:
        """Remove a completed/error/removed download from memory.

        Args:
            gid: The GID of the download

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If removing result fails
        """
        return await self._call("aria2.removeDownloadResult", [gid])

    # Session Management Methods

    async def save_session(self) -> str:
        """Save the current session to a file.

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If saving session fails

        Note:
            This method saves the current session to the file specified
            by the --save-session option. The session file contains
            information about downloads to resume after restart.
        """
        return await self._call("aria2.saveSession")

    # System Control Methods

    async def shutdown(self) -> str:
        """Shutdown aria2 gracefully.

        This method shuts down aria2. Active downloads are saved to session file
        if --save-session option is configured.

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If shutdown fails

        Note:
            For local aria2c managed by ariatuc, prefer using LocalProcessManager
            to ensure proper process cleanup.
        """
        return await self._call("aria2.shutdown")

    async def force_shutdown(self) -> str:
        """Forcefully shutdown aria2 immediately.

        Similar to shutdown() but does not wait for downloads to complete.

        Returns:
            'OK' on success

        Raises:
            Aria2RPCError: If forced shutdown fails

        Warning:
            Active downloads may not be saved to session file.
        """
        return await self._call("aria2.forceShutdown")

    async def list_methods(self) -> list[str]:
        """List all available RPC methods.

        Returns:
            List of method names (e.g., ['aria2.addUri', 'aria2.getVersion', ...])

        Raises:
            Aria2RPCError: If listing methods fails

        Note:
            Useful for debugging and feature detection.
        """
        return await self._call("system.listMethods")

    async def multicall(self, calls: list[dict[str, Any]]) -> list[Any]:
        """Execute multiple RPC methods in a single request.

        Args:
            calls: List of method call dicts, each with:
                - methodName: str (e.g., "aria2.tellStatus")
                - params: list (method parameters)

        Returns:
            List of results corresponding to each call

        Raises:
            Aria2RPCError: If multicall fails or any method fails

        Example:
            >>> calls = [
            ...     {"methodName": "aria2.tellStatus", "params": ["gid1"]},
            ...     {"methodName": "aria2.tellStatus", "params": ["gid2"]},
            ... ]
            >>> results = await client.multicall(calls)
        """
        return await self._call("system.multicall", [calls])

    # aria2-next extensions
    #
    # These methods are only available when the connected server is
    # aria2-next (https://github.com/AnInsomniacy/aria2-next). They expose
    # native HLS / DASH media control. Capability checks live in
    # ``aria2rpc.client.is_aria2_next``; on vanilla aria2c these calls will
    # raise ``Aria2RPCError`` from the server.

    async def finish_media(self, gid: str) -> str:
        """Finish an active or paused live recording (aria2-next only).

        Ends an active or paused live recording and finalizes its completed
        media. Pause retains the task; remove cancels it and discards its
        recovery state. Finishing and deleting are separate operations.

        Args:
            gid: GID of the media task.

        Returns:
            GID of the finished task.

        Raises:
            Aria2RPCError: If the task is not a media task, or the server is
                not aria2-next.

        See Also:
            ``aria2rpc.client.is_aria2_next``: detect support before calling.
        """
        return await self._call("aria2.finishMedia", [gid])

    async def retry_media(
        self,
        gid: str,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Retry a failed media task (aria2-next only).

        Requeues a failed media task with the same GID and retained native
        recovery data. Does not delete the stopped result until queue
        insertion succeeds. Invalid or non-media results are rejected without
        mutation.

        Use this instead of removing the result and submitting a new GID:
        ``removeDownloadResult`` intentionally discards media recovery data.

        Args:
            gid: GID of the failed media task.
            options: Optional option overrides applied via the paused-task
                option validator. Must be a paused task.

        Returns:
            GID of the retried task.

        Raises:
            Aria2RPCError: If the task is invalid, not a media task, or the
                server is not aria2-next.

        See Also:
            ``aria2rpc.client.is_aria2_next``: detect support before calling.
        """
        params: list[Any] = [gid]
        if options:
            params.append(options)
        return await self._call("aria2.retryMedia", params)
