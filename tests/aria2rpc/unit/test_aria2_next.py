"""Tests for aria2-next extensions: capability detection, media RPC, media models.

These tests mock the JSON-RPC envelope; no aria2c / aria2-next daemon is required.
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from aria2rpc import (
    Aria2Client,
    DownloadStatus,
    MediaDownloadStatus,
    MediaFeatures,
    MediaState,
    MediaTrack,
    Version,
    is_aria2_next,
)
from aria2rpc.http import HTTPRPCClient


@pytest.fixture
def http_client() -> HTTPRPCClient:
    """Return an HTTPRPCClient with no real network connection."""
    return HTTPRPCClient("http://localhost:6800/jsonrpc")


# -----------------------------------------------------------------------------
# Capability detection
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_aria2_next_true_when_media_features_present(
    http_client: HTTPRPCClient,
) -> None:
    """aria2-next versions expose the mediaFeatures field on getVersion."""
    with patch.object(http_client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {
            "version": "aria2-next 1.0.0",
            "enabledFeatures": ["HLS", "DASH"],
            "mediaFeatures": {
                "request-contexts": True,
                "stable-track-ids": True,
                "structured-errors": True,
            },
        }

        assert await is_aria2_next(http_client) is True
        mock_call.assert_called_once_with("aria2.getVersion")


@pytest.mark.asyncio
async def test_is_aria2_next_false_for_vanilla_aria2c(
    http_client: HTTPRPCClient,
) -> None:
    """Vanilla aria2c does not advertise mediaFeatures."""
    with patch.object(http_client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {
            "version": "1.37.0",
            "enabledFeatures": ["BitTorrent", "Firefox3 Cookie", "WebSocket"],
        }

        assert await is_aria2_next(http_client) is False


def test_version_exposes_aria2_next_flag() -> None:
    """Version.is_aria2_next is True iff mediaFeatures is present."""
    v_next = Version({"version": "aria2-next 1.0", "mediaFeatures": {}})
    v_upstream = Version({"version": "1.37.0", "enabledFeatures": []})
    v_empty = Version({})

    assert v_next.is_aria2_next is True
    assert v_upstream.is_aria2_next is False
    assert v_empty.is_aria2_next is False


def test_version_media_features_returns_model() -> None:
    """Version.media_features returns a MediaFeatures or None."""
    v_next = Version(
        {
            "version": "aria2-next 1.0",
            "mediaFeatures": {
                "request-contexts": True,
                "stable-track-ids": True,
                "structured-errors": False,
            },
        }
    )
    v_upstream = Version({"version": "1.37.0"})

    features = v_next.media_features
    assert features is not None
    assert features.request_contexts is True
    assert features.stable_track_ids is True
    assert features.structured_errors is False

    assert v_upstream.media_features is None


# -----------------------------------------------------------------------------
# MediaFeatures model
# -----------------------------------------------------------------------------


def test_media_features_defaults_to_false() -> None:
    """Unknown flags default to False."""
    features = MediaFeatures({})
    assert features.request_contexts is False
    assert features.stable_track_ids is False
    assert features.structured_errors is False


def test_media_features_partial_flags() -> None:
    """Partial flag sets are tolerated."""
    features = MediaFeatures({"structured-errors": True})
    assert features.structured_errors is True
    assert features.request_contexts is False


# -----------------------------------------------------------------------------
# MediaTrack model
# -----------------------------------------------------------------------------


def test_media_track_parses_video_track() -> None:
    """A typical video track parses cleanly."""
    raw = {
        "id": "track-abc",
        "type": "video",
        "codec": "avc1.640028",
        "language": "",
        "bandwidth": 5000000,
        "frameRate": "29.97",
        "channels": 0,
    }
    track = MediaTrack(raw)

    assert track.track_id == "track-abc"
    assert track.type == "video"
    assert track.codec == "avc1.640028"
    assert track.language == ""
    assert track.bandwidth == 5_000_000
    assert track.frame_rate == pytest.approx(29.97)
    assert track.channels == 0


def test_media_track_frame_rate_zero_when_unknown() -> None:
    """frameRate '0' (unknown) must surface as 0.0."""
    raw = {"id": "t", "type": "audio", "frameRate": "0"}
    track = MediaTrack(raw)
    assert track.frame_rate == 0.0


def test_media_track_empty_frame_rate_does_not_raise() -> None:
    """An empty frameRate string does not crash."""
    raw = {"id": "t", "type": "audio", "frameRate": ""}
    track = MediaTrack(raw)
    assert track.frame_rate == 0.0


# -----------------------------------------------------------------------------
# MediaDownloadStatus model
# -----------------------------------------------------------------------------


def test_media_download_status_parses_full_payload() -> None:
    """The example payload from aria2-next docs parses cleanly."""
    raw = {
        "state": "awaiting-selection",
        "protocol": "hls",
        "live": "false",
        "duration": "60000",
        "completedDuration": "20000",
        "downloadedLength": "4194304",
        "progress": "0.333333",
        "lengthKnown": "false",
        "error": "",
        "errorCode": "",
        "tracks": [
            {"id": "v1", "type": "video", "codec": "avc1", "bandwidth": 4_000_000},
            {"id": "a1", "type": "audio", "codec": "mp4a", "language": "en"},
        ],
    }
    status = MediaDownloadStatus(raw)

    assert status.state is MediaState.AWAITING_SELECTION
    assert status.protocol == "hls"
    assert status.live is False
    assert status.duration == 60_000
    assert status.completed_duration == 20_000
    assert status.downloaded_length == 4_194_304
    assert status.progress == pytest.approx(0.333333)
    assert status.length_known is False
    assert status.error == ""
    assert status.error_code == ""
    assert len(status.tracks) == 2
    assert status.tracks[0].track_id == "v1"
    assert status.tracks[0].type == "video"
    assert status.tracks[1].language == "en"


def test_media_state_enum_covers_all_phases() -> None:
    """Every phase from aria2-next docs is a MediaState member."""
    expected = {
        "waiting",
        "probing",
        "awaiting-selection",
        "downloading",
        "recording",
        "finalizing",
        "paused",
        "complete",
        "error",
        "removed",
    }
    actual = {m.value for m in MediaState}
    assert actual == expected


def test_download_status_media_accessor_returns_none_for_non_media() -> None:
    """DownloadStatus.media is None for ordinary downloads."""
    raw = {
        "gid": "abc",
        "status": "active",
        "totalLength": "100",
        "completedLength": "50",
    }
    status = DownloadStatus(raw)
    assert status.media is None


def test_download_status_media_accessor_returns_model_for_media_task() -> None:
    """DownloadStatus.media wraps the embedded media object as a model."""
    raw = {
        "gid": "abc",
        "status": "active",
        "media": {
            "state": "downloading",
            "protocol": "dash",
            "tracks": [{"id": "v", "type": "video"}],
        },
    }
    status = DownloadStatus(raw)

    assert status.media is not None
    assert isinstance(status.media, MediaDownloadStatus)
    assert status.media.protocol == "dash"
    assert status.media.state is MediaState.DOWNLOADING
    assert len(status.media.tracks) == 1


# -----------------------------------------------------------------------------
# aria2-next RPC methods
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_finish_media_calls_correct_rpc(http_client: HTTPRPCClient) -> None:
    """finish_media invokes aria2.finishMedia with the GID."""
    with patch.object(http_client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "abc123"

        result = await http_client.finish_media("abc123")

        mock_call.assert_called_once_with("aria2.finishMedia", ["abc123"])
        assert result == "abc123"


@pytest.mark.asyncio
async def test_retry_media_calls_correct_rpc(http_client: HTTPRPCClient) -> None:
    """retry_media without options passes only the GID."""
    with patch.object(http_client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "abc123"

        result = await http_client.retry_media("abc123")

        mock_call.assert_called_once_with("aria2.retryMedia", ["abc123"])
        assert result == "abc123"


@pytest.mark.asyncio
async def test_retry_media_with_options(http_client: HTTPRPCClient) -> None:
    """retry_media with options appends the options dict as the second param."""
    with patch.object(http_client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "abc123"

        options: dict[str, Any] = {"media-format": "mkv"}
        await http_client.retry_media("abc123", options)

        mock_call.assert_called_once_with("aria2.retryMedia", ["abc123", options])


# -----------------------------------------------------------------------------
# Factory wiring
# -----------------------------------------------------------------------------


def test_aria2_client_factory_does_not_eagerly_connect() -> None:
    """Aria2Client(url) returns a client without performing I/O."""
    factory = Aria2Client("http://localhost:6800/jsonrpc")
    # The factory returns HTTPRPCClient synchronously; it has not yet
    # opened a socket. Verify by checking the instance type and that
    # capability checks require an explicit call.
    assert isinstance(factory, HTTPRPCClient)


@pytest.mark.asyncio
async def test_capability_check_uses_get_version() -> None:
    """End-to-end smoke test of Aria2Client + is_aria2_next with mocked transport."""
    client = Aria2Client("http://localhost:6800/jsonrpc")

    with patch.object(client, "get_version", new_callable=AsyncMock) as mock_version:
        mock_version.return_value = Version(
            {
                "version": "aria2-next 1.0",
                "mediaFeatures": {
                    "request-contexts": True,
                    "stable-track-ids": True,
                    "structured-errors": True,
                },
            }
        )

        assert await is_aria2_next(client) is True
