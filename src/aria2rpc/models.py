"""Data models for aria2 RPC responses.

These models provide type-safe representations of aria2 RPC data structures.
They are lightweight wrappers around the raw JSON responses from aria2.
"""

from typing import Any


class RPCResponse:
    """Base class for RPC responses."""

    def __init__(self, data: dict[str, Any]):
        """Initialize from raw aria2 response data.

        Args:
            data: Raw dictionary from aria2 RPC response
        """
        self._data = data

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access to raw data."""
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default fallback."""
        return self._data.get(key, default)

    @property
    def raw(self) -> dict[str, Any]:
        """Get the raw response data."""
        return self._data


class DownloadStatus(RPCResponse):
    """Represents download status information from aria2.

    Provides convenient access to common fields while maintaining
    access to all raw data from aria2.
    """

    @property
    def gid(self) -> str:
        """GID of the download."""
        return self._data.get("gid", "")

    @property
    def status(self) -> str:
        """Status: active, waiting, paused, error, complete, removed."""
        return self._data.get("status", "")

    @property
    def total_length(self) -> int:
        """Total length of the download in bytes."""
        return int(self._data.get("totalLength", 0))

    @property
    def completed_length(self) -> int:
        """Completed length of the download in bytes."""
        return int(self._data.get("completedLength", 0))

    @property
    def upload_length(self) -> int:
        """Uploaded length in bytes (for BitTorrent)."""
        return int(self._data.get("uploadLength", 0))

    @property
    def download_speed(self) -> int:
        """Download speed in bytes/sec."""
        return int(self._data.get("downloadSpeed", 0))

    @property
    def upload_speed(self) -> int:
        """Upload speed in bytes/sec."""
        return int(self._data.get("uploadSpeed", 0))

    @property
    def connections(self) -> int:
        """Number of active connections."""
        return int(self._data.get("connections", 0))

    @property
    def num_seeders(self) -> int:
        """Number of seeders (BitTorrent only)."""
        return int(self._data.get("numSeeders", 0))

    @property
    def files(self) -> list[dict[str, Any]]:
        """List of files in the download."""
        return self._data.get("files", [])

    @property
    def error_code(self) -> str | None:
        """Error code if status is 'error'."""
        return self._data.get("errorCode")

    @property
    def error_message(self) -> str | None:
        """Error message if status is 'error'."""
        return self._data.get("errorMessage")


class GlobalStat(RPCResponse):
    """Represents global statistics from aria2."""

    @property
    def download_speed(self) -> int:
        """Overall download speed in bytes/sec."""
        return int(self._data.get("downloadSpeed", 0))

    @property
    def upload_speed(self) -> int:
        """Overall upload speed in bytes/sec."""
        return int(self._data.get("uploadSpeed", 0))

    @property
    def num_active(self) -> int:
        """Number of active downloads."""
        return int(self._data.get("numActive", 0))

    @property
    def num_waiting(self) -> int:
        """Number of waiting downloads."""
        return int(self._data.get("numWaiting", 0))

    @property
    def num_stopped(self) -> int:
        """Number of stopped downloads."""
        return int(self._data.get("numStopped", 0))

    @property
    def num_stopped_total(self) -> int:
        """Total number of stopped downloads (including removed)."""
        return int(self._data.get("numStoppedTotal", 0))


class Version(RPCResponse):
    """Represents aria2 version information."""

    @property
    def version(self) -> str:
        """aria2 version string."""
        return self._data.get("version", "")

    @property
    def enabled_features(self) -> list[str]:
        """List of enabled features."""
        return self._data.get("enabledFeatures", [])


class Peer(RPCResponse):
    """Represents a BitTorrent peer.

    Contains information about a peer in a BitTorrent download.
    """

    @property
    def peer_id(self) -> str:
        """Peer ID of the peer."""
        return self._data.get("peerId", "")

    @property
    def ip(self) -> str:
        """IP address of the peer."""
        return self._data.get("ip", "")

    @property
    def port(self) -> str:
        """Port number of the peer."""
        return self._data.get("port", "")

    @property
    def bitfield(self) -> str:
        """Hex representation of the bitfield."""
        return self._data.get("bitfield", "")

    @property
    def am_choking(self) -> bool:
        """Whether we are choking this peer."""
        return self._data.get("amChoking", "false") == "true"

    @property
    def peer_choking(self) -> bool:
        """Whether this peer is choking us."""
        return self._data.get("peerChoking", "false") == "true"

    @property
    def download_speed(self) -> int:
        """Download speed from this peer in bytes/sec."""
        return int(self._data.get("downloadSpeed", 0))

    @property
    def upload_speed(self) -> int:
        """Upload speed to this peer in bytes/sec."""
        return int(self._data.get("uploadSpeed", 0))

    @property
    def seeder(self) -> bool:
        """Whether this peer is a seeder."""
        return self._data.get("seeder", "false") == "true"


class Server(RPCResponse):
    """Represents a server/URI used in a download.

    Contains information about servers (HTTP/FTP) or trackers (BitTorrent).
    """

    @property
    def uri(self) -> str:
        """Original URI."""
        return self._data.get("uri", "")

    @property
    def current_uri(self) -> str:
        """Currently used URI (after redirects)."""
        return self._data.get("currentUri", "")

    @property
    def download_speed(self) -> int:
        """Download speed from this server in bytes/sec."""
        return int(self._data.get("downloadSpeed", 0))


class FileServer(RPCResponse):
    """Represents servers for a specific file in a download.

    Contains the file index and list of servers for that file.
    """

    @property
    def index(self) -> int:
        """Index of the file (1-based)."""
        return int(self._data.get("index", 0))

    @property
    def servers(self) -> list[Server]:
        """List of servers for this file."""
        servers_data = self._data.get("servers", [])
        return [Server(server) for server in servers_data]
