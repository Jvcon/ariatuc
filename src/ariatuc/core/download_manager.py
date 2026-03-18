"""Download state management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ariatuc.core.speed_tracker import SpeedTracker


class DownloadStatus(Enum):
    """Download status enumeration."""

    ACTIVE = "active"
    WAITING = "waiting"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETE = "complete"
    REMOVED = "removed"


@dataclass
class Download:
    """Represents a download item."""

    gid: str
    status: DownloadStatus
    total_length: int
    completed_length: int
    download_speed: int  # Instantaneous speed from aria2 (bytes/s)
    upload_speed: int
    files: list[dict[str, Any]]
    connections: int
    name: str = ""  # Download name (filename or first file name)
    dir: str = ""  # Download directory
    urls: list[str] = field(default_factory=list)  # Download URLs
    # BitTorrent specific fields
    num_seeders: int = 0  # Number of seeders
    upload_length: int = 0  # Total uploaded bytes
    info_hash: str = ""  # BitTorrent info hash
    is_torrent: bool = False  # Whether this is a torrent download
    # EMA smoothed speed (updated by DownloadManager)
    smoothed_download_speed: float = 0.0  # EMA smoothed download speed (bytes/s)
    smoothed_upload_speed: float = 0.0  # EMA smoothed upload speed (bytes/s)

    @property
    def progress(self) -> float:
        """Calculate download progress percentage."""
        if self.total_length == 0:
            return 0.0
        return (self.completed_length / self.total_length) * 100

    @property
    def share_ratio(self) -> float:
        """Calculate share ratio (uploaded / downloaded)."""
        if self.completed_length == 0:
            return 0.0
        return self.upload_length / self.completed_length


class DownloadManager:
    """Manages download state and operations with EMA speed smoothing."""

    def __init__(self):
        """Initialize the download manager."""
        self.downloads: dict[str, Download] = {}
        # Speed tracker for EMA smoothing (alpha=0.3 as recommended by Surge)
        self._download_speed_tracker = SpeedTracker(alpha=0.3)
        self._upload_speed_tracker = SpeedTracker(alpha=0.3)

    def update_download(self, gid: str, data: dict[str, Any]) -> Download:
        """Update or create a download from aria2 data.

        Args:
            gid: The download GID
            data: Download data from aria2

        Returns:
            The updated Download object
        """
        status_map = {
            "active": DownloadStatus.ACTIVE,
            "waiting": DownloadStatus.WAITING,
            "paused": DownloadStatus.PAUSED,
            "error": DownloadStatus.ERROR,
            "complete": DownloadStatus.COMPLETE,
            "removed": DownloadStatus.REMOVED,
        }

        # Extract download name (from first file or bittorrent info or URL)
        name = ""
        files = data.get("files", [])
        if files and len(files) > 0:
            # Try to get filename from first file's path
            file_path = files[0].get("path", "")
            if file_path:
                name = file_path.split("/")[-1]  # Get filename from path

            # If no path, try to extract from first URI
            if not name:
                file_uris = files[0].get("uris", [])
                if file_uris:
                    first_uri = file_uris[0].get("uri", "")
                    if first_uri:
                        # Extract filename from URL (last part of path)
                        uri_path = first_uri.split("?")[0]  # Remove query parameters
                        name = uri_path.split("/")[-1] or "download"

        # If no filename from files, try bittorrent info
        if not name:
            bt_info = data.get("bittorrent", {})
            if bt_info:
                name = bt_info.get("info", {}).get("name", "")

        # Fallback: use GID if still no name
        if not name:
            name = f"download-{gid[:8]}"

        # Extract download directory
        dir_path = data.get("dir", "")

        # Extract URLs from files
        urls = []
        for file_data in files:
            file_uris = file_data.get("uris", [])
            for uri_data in file_uris:
                uri = uri_data.get("uri", "")
                if uri and uri not in urls:
                    urls.append(uri)

        # Extract BitTorrent specific fields
        bt_info = data.get("bittorrent", {})
        is_torrent = bool(bt_info)
        info_hash = ""
        if is_torrent:
            info_hash = bt_info.get("info", {}).get("infoHash", "")

        # Get aria2's instantaneous speeds
        instant_download_speed = int(data.get("downloadSpeed", 0))
        instant_upload_speed = int(data.get("uploadSpeed", 0))
        completed_length = int(data.get("completedLength", 0))

        # Calculate EMA smoothed speeds
        smoothed_download_speed = self._download_speed_tracker.update(gid, completed_length)
        smoothed_upload_speed = self._upload_speed_tracker.update(
            gid, int(data.get("uploadLength", 0))
        )

        download = Download(
            gid=gid,
            status=status_map.get(data.get("status", "waiting"), DownloadStatus.WAITING),
            total_length=int(data.get("totalLength", 0)),
            completed_length=completed_length,
            download_speed=instant_download_speed,
            upload_speed=instant_upload_speed,
            files=files,
            connections=int(data.get("connections", 0)),
            name=name,
            dir=dir_path,
            urls=urls,
            # BitTorrent fields
            num_seeders=int(data.get("numSeeders", 0)),
            upload_length=int(data.get("uploadLength", 0)),
            info_hash=info_hash,
            is_torrent=is_torrent,
            # EMA smoothed speeds
            smoothed_download_speed=smoothed_download_speed,
            smoothed_upload_speed=smoothed_upload_speed,
        )

        self.downloads[gid] = download
        return download

    def get_download(self, gid: str) -> Download | None:
        """Get a download by GID.

        Args:
            gid: The download GID

        Returns:
            The Download object or None if not found
        """
        return self.downloads.get(gid)

    def get_all_downloads(self) -> list[Download]:
        """Get all downloads.

        Returns:
            List of all downloads
        """
        return list(self.downloads.values())

    def get_downloads_by_status(self, status: DownloadStatus) -> list[Download]:
        """Get downloads filtered by status.

        Args:
            status: The status to filter by

        Returns:
            List of downloads with the specified status
        """
        return [d for d in self.downloads.values() if d.status == status]

    def remove_download(self, gid: str) -> bool:
        """Remove a download from the manager.

        Args:
            gid: The download GID to remove

        Returns:
            True if download was removed, False if not found
        """
        if gid in self.downloads:
            del self.downloads[gid]
            # Clean up speed tracking data
            self._download_speed_tracker.remove(gid)
            self._upload_speed_tracker.remove(gid)
            return True
        return False

    def clear_removed_downloads(self) -> int:
        """Remove all downloads with REMOVED status from the manager.

        Returns:
            Number of downloads removed
        """
        removed_gids = [
            gid
            for gid, download in self.downloads.items()
            if download.status == DownloadStatus.REMOVED
        ]
        for gid in removed_gids:
            del self.downloads[gid]
        return len(removed_gids)
