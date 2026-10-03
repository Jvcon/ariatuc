"""Data models for aria2 RPC responses.

These models provide type-safe representations of aria2 RPC data structures.
They are lightweight wrappers around the raw JSON responses from aria2, with
typed accessors for the fields we use.

aria2-next extends the upstream aria2 RPC with media task fields, capability
flags, and two new methods (`finishMedia`, `retryMedia`). Models for those
extensions live at the bottom of this file.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class RPCResponse:
    """Base class for RPC responses.

    Wraps the raw dictionary from aria2. Subclasses expose typed accessors.
    """

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
    access to all raw data from aria2. On aria2-next servers, the
    `media` field exposes media task details via the `media` property.
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

    @property
    def media(self) -> MediaDownloadStatus | None:
        """aria2-next media object (None on vanilla aria2c).

        Returns:
            MediaDownloadStatus when the task is an HLS / DASH media task;
            None for ordinary downloads or when the server is upstream aria2c.
        """
        media_data = self._data.get("media")
        if media_data is None:
            return None
        return MediaDownloadStatus(media_data)


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

    @property
    def media_features(self) -> MediaFeatures | None:
        """aria2-next media feature map (None on vanilla aria2c).

        Returns:
            MediaFeatures when the server is aria2-next and advertises the
            `mediaFeatures` field; None otherwise.
        """
        raw = self._data.get("mediaFeatures")
        if raw is None:
            return None
        return MediaFeatures(raw)

    @property
    def is_aria2_next(self) -> bool:
        """True when the server is aria2-next.

        Detected by presence of the `mediaFeatures` field on `getVersion`.
        aria2c does not return this field.
        """
        return "mediaFeatures" in self._data


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


# ==============================================================================
# aria2-next extensions
# ==============================================================================


class MediaState(StrEnum):
    """Lifecycle phases of an aria2-next media task.

    Per aria2-next docs/media-downloads.md. Standard RPC status retains the
    ordinary task lifecycle; only successful muxing and publishing the output
    file produce a completed task.
    """

    WAITING = "waiting"
    PROBING = "probing"
    AWAITING_SELECTION = "awaiting-selection"
    DOWNLOADING = "downloading"
    RECORDING = "recording"
    FINALIZING = "finalizing"
    PAUSED = "paused"
    COMPLETE = "complete"
    ERROR = "error"
    REMOVED = "removed"


class MediaTrack(RPCResponse):
    """A single media track in an aria2-next HLS / DASH presentation.

    Track IDs derive from native representation identity and media attributes,
    not manifest positions. Treat IDs as opaque; do not parse them.
    """

    @property
    def track_id(self) -> str:
        """Opaque native track identifier."""
        return self._data.get("id", "")

    @property
    def type(self) -> str:
        """Track type: 'video', 'audio', or 'subtitle'."""
        return self._data.get("type", "")

    @property
    def codec(self) -> str:
        """Codec identifier (e.g. 'avc1.640028', 'mp4a.40.2')."""
        return self._data.get("codec", "")

    @property
    def language(self) -> str:
        """BCP-47 language tag, empty string if unknown."""
        return self._data.get("language", "")

    @property
    def bandwidth(self) -> int:
        """Bandwidth in bits per second."""
        return int(self._data.get("bandwidth", 0))

    @property
    def frame_rate(self) -> float:
        """Frame rate as a decimal; 0 means unknown."""
        raw = self._data.get("frameRate", "0")
        return float(raw) if raw else 0.0

    @property
    def channels(self) -> int:
        """Audio channel count; 0 for non-audio tracks."""
        return int(self._data.get("channels", 0))


class MediaDownloadStatus(RPCResponse):
    """The `media` object exposed on aria2-next task status responses.

    Media progress is based on `completedDuration` (milliseconds). Output byte
    lengths remain unknown until remuxing finishes: source segment bytes are
    not the same quantity as the final container size. `downloadedLength`
    reports retained media payload independently of the standard network speed.
    """

    @property
    def state(self) -> MediaState:
        """Current media lifecycle phase."""
        return MediaState(self._data.get("state", "waiting"))

    @property
    def protocol(self) -> str:
        """'hls', 'dash', or 'file'."""
        return self._data.get("protocol", "")

    @property
    def live(self) -> bool:
        """True for live HLS / DASH streams."""
        return self._data.get("live", "false") == "true"

    @property
    def duration(self) -> int:
        """Presentation duration in milliseconds; 0 for live."""
        return int(self._data.get("duration", 0))

    @property
    def completed_duration(self) -> int:
        """Completed media duration in milliseconds."""
        return int(self._data.get("completedDuration", 0))

    @property
    def downloaded_length(self) -> int:
        """Retained media payload bytes (independent of network speed)."""
        return int(self._data.get("downloadedLength", 0))

    @property
    def progress(self) -> float:
        """Media progress as a decimal between 0 and 1."""
        return float(self._data.get("progress", 0))

    @property
    def length_known(self) -> bool:
        """False while the engine has not yet determined final length."""
        return self._data.get("lengthKnown", "false") == "true"

    @property
    def error(self) -> str:
        """Diagnostic text for the last error, empty otherwise."""
        return self._data.get("error", "")

    @property
    def error_code(self) -> str:
        """Structured error code such as 'unsupported_source' or empty on success."""
        return self._data.get("errorCode", "")

    @property
    def tracks(self) -> list[MediaTrack]:
        """Available media tracks (populated after probing)."""
        return [MediaTrack(t) for t in self._data.get("tracks", [])]


class MediaFeatures(RPCResponse):
    """Capability flags advertised by `getVersion.mediaFeatures`.

    Only present on aria2-next. Upstream docs list `request-contexts`,
    `stable-track-ids`, and `structured-errors` as the current flags. Unknown
    flags are still parsed (call `.raw`) so future extensions don't break.
    """

    @property
    def request_contexts(self) -> bool:
        """Server supports scoped HTTP request contexts for media tasks."""
        return self._data.get("request-contexts", False) is True

    @property
    def stable_track_ids(self) -> bool:
        """Track IDs remain stable across playlist refreshes."""
        return self._data.get("stable-track-ids", False) is True

    @property
    def structured_errors(self) -> bool:
        """Server returns structured `errorCode` values for media failures."""
        return self._data.get("structured-errors", False) is True
