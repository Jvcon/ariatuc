"""Tests for download manager."""

from ariatuc.core.download_manager import Download, DownloadManager, DownloadStatus


def test_download_manager_initialization():
    """Test DownloadManager initialization."""
    manager = DownloadManager()
    assert len(manager.downloads) == 0


def test_update_download():
    """Test updating download from aria2 data."""
    manager = DownloadManager()

    data = {
        "status": "active",
        "totalLength": "1000000",
        "completedLength": "500000",
        "downloadSpeed": "10000",
        "uploadSpeed": "1000",
        "files": [],
        "connections": "4",
    }

    download = manager.update_download("test-gid", data)

    assert download.gid == "test-gid"
    assert download.status == DownloadStatus.ACTIVE
    assert download.total_length == 1000000
    assert download.completed_length == 500000
    assert download.progress == 50.0


def test_get_downloads_by_status():
    """Test filtering downloads by status."""
    manager = DownloadManager()

    # Add active download
    manager.update_download(
        "gid1", {"status": "active", "totalLength": "100", "completedLength": "50"}
    )

    # Add paused download
    manager.update_download(
        "gid2", {"status": "paused", "totalLength": "100", "completedLength": "30"}
    )

    active_downloads = manager.get_downloads_by_status(DownloadStatus.ACTIVE)
    assert len(active_downloads) == 1
    assert active_downloads[0].gid == "gid1"

    paused_downloads = manager.get_downloads_by_status(DownloadStatus.PAUSED)
    assert len(paused_downloads) == 1
    assert paused_downloads[0].gid == "gid2"


def test_download_progress_calculation():
    """Test download progress calculation."""
    download = Download(
        gid="test",
        status=DownloadStatus.ACTIVE,
        total_length=1000,
        completed_length=750,
        download_speed=100,
        upload_speed=10,
        files=[],
        connections=4,
    )

    assert download.progress == 75.0


def test_download_progress_zero_length():
    """Test download progress with zero total length."""
    download = Download(
        gid="test",
        status=DownloadStatus.WAITING,
        total_length=0,
        completed_length=0,
        download_speed=0,
        upload_speed=0,
        files=[],
        connections=0,
    )

    assert download.progress == 0.0


def test_remove_download():
    """Test removing a download from the manager."""
    manager = DownloadManager()

    # Add downloads
    manager.update_download(
        "gid1", {"status": "active", "totalLength": "100", "completedLength": "50"}
    )
    manager.update_download(
        "gid2", {"status": "paused", "totalLength": "100", "completedLength": "30"}
    )

    assert len(manager.downloads) == 2

    # Remove one download
    result = manager.remove_download("gid1")
    assert result is True
    assert len(manager.downloads) == 1
    assert manager.get_download("gid1") is None
    assert manager.get_download("gid2") is not None

    # Try to remove non-existent download
    result = manager.remove_download("gid-nonexistent")
    assert result is False
    assert len(manager.downloads) == 1


def test_clear_removed_downloads():
    """Test clearing downloads with REMOVED status."""
    manager = DownloadManager()

    # Add downloads with different statuses
    manager.update_download(
        "gid1", {"status": "active", "totalLength": "100", "completedLength": "50"}
    )
    manager.update_download(
        "gid2", {"status": "removed", "totalLength": "100", "completedLength": "30"}
    )
    manager.update_download(
        "gid3", {"status": "complete", "totalLength": "100", "completedLength": "100"}
    )
    manager.update_download(
        "gid4", {"status": "removed", "totalLength": "100", "completedLength": "10"}
    )

    assert len(manager.downloads) == 4

    # Clear removed downloads
    removed_count = manager.clear_removed_downloads()

    assert removed_count == 2
    assert len(manager.downloads) == 2
    assert manager.get_download("gid1") is not None
    assert manager.get_download("gid2") is None
    assert manager.get_download("gid3") is not None
    assert manager.get_download("gid4") is None
