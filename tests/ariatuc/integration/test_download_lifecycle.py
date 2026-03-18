"""Integration tests for download lifecycle operations.

These tests verify that the service layer correctly coordinates
between aria2rpc client and download manager for the complete
download lifecycle: add, pause, resume, delete.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aria2rpc.exceptions import Aria2Error
from ariatuc.core.download_manager import DownloadStatus
from ariatuc.core.service import Aria2Service, DownloadOperationError


@pytest.fixture
async def service():
    """Create a service instance with mocked RPC client for testing."""
    service = Aria2Service()
    await service.initialize()

    # Create mock client
    mock_client = AsyncMock()

    # Mock the RPC manager's get_client method
    with patch.object(service.rpc_mgr, "get_client", return_value=mock_client):
        # Add a test server
        service.add_server("test-server", "http://localhost:6800/jsonrpc")

        # Connect to the test server
        await service.connect("test-server")

        # Mock client is accessible via the patch context
        # No need to store it on the service object

        yield service

    # Cleanup
    await service.shutdown()


class TestDownloadLifecycle:
    """Test complete download lifecycle: add -> pause -> resume -> delete."""

    @pytest.mark.asyncio
    async def test_complete_download_lifecycle(self, service):
        """Test complete lifecycle: add -> pause -> resume -> delete in one test."""
        mock_client = service._test_mock_client
        test_gid = "lifecycle123"
        test_url = "http://example.com/test-file.zip"

        # Setup mocks for the complete lifecycle
        mock_client.add_uri.return_value = test_gid
        mock_client.pause.return_value = test_gid
        mock_client.unpause.return_value = test_gid
        mock_client.remove.return_value = test_gid

        # Mock tell_status to return appropriate status for each state
        status_sequence = iter(
            [
                # After add - active status
                MagicMock(
                    gid=test_gid,
                    raw={
                        "gid": test_gid,
                        "status": "active",
                        "totalLength": "1000000",
                        "completedLength": "100000",
                        "downloadSpeed": "50000",
                        "uploadSpeed": "0",
                        "files": [],
                        "connections": "4",
                        "dir": "/downloads",
                        "uris": [test_url],
                    },
                ),
                # After pause - paused status
                MagicMock(
                    gid=test_gid,
                    raw={
                        "gid": test_gid,
                        "status": "paused",
                        "totalLength": "1000000",
                        "completedLength": "300000",
                        "downloadSpeed": "0",
                        "uploadSpeed": "0",
                        "files": [],
                        "connections": "0",
                        "dir": "/downloads",
                        "uris": [test_url],
                    },
                ),
                # After resume - active status again
                MagicMock(
                    gid=test_gid,
                    raw={
                        "gid": test_gid,
                        "status": "active",
                        "totalLength": "1000000",
                        "completedLength": "500000",
                        "downloadSpeed": "60000",
                        "uploadSpeed": "0",
                        "files": [],
                        "connections": "4",
                        "dir": "/downloads",
                        "uris": [test_url],
                    },
                ),
            ]
        )

        mock_client.tell_status.side_effect = lambda _: next(status_sequence)

        # Mock refresh methods to return empty lists after delete
        mock_client.tell_active.return_value = []
        mock_client.tell_waiting.return_value = []
        mock_client.tell_stopped.return_value = []

        # Step 1: Add download
        print("\n=== Testing ADD download ===")
        gid = await service.add_download([test_url])
        assert gid == test_gid, f"Expected GID {test_gid}, got {gid}"
        mock_client.add_uri.assert_called_once()

        # Verify download is tracked in service
        download = service.get_download(gid)
        assert download is not None, "Download should be tracked after add"
        assert download.gid == test_gid
        assert download.status == DownloadStatus.ACTIVE
        print(f"✓ Added download {gid}, status: {download.status}")

        # Step 2: Pause download
        print("\n=== Testing PAUSE download ===")
        pause_result = await service.pause_download(gid)
        assert pause_result is True, "Pause should return True"
        mock_client.pause.assert_called_once_with(test_gid)

        # Verify download status updated to paused
        download = service.get_download(gid)
        assert download.status == DownloadStatus.PAUSED, f"Expected PAUSED, got {download.status}"
        print(f"✓ Paused download {gid}, status: {download.status}")

        # Step 3: Resume download
        print("\n=== Testing RESUME download ===")
        resume_result = await service.resume_download(gid)
        assert resume_result is True, "Resume should return True"
        mock_client.unpause.assert_called_once_with(test_gid)

        # Verify download status updated to active
        download = service.get_download(gid)
        assert download.status == DownloadStatus.ACTIVE, f"Expected ACTIVE, got {download.status}"
        print(f"✓ Resumed download {gid}, status: {download.status}")

        # Step 4: Delete download
        print("\n=== Testing DELETE download ===")
        delete_result = await service.remove_download(gid)
        assert delete_result is True, "Delete should return True"
        mock_client.remove.assert_called_once_with(test_gid)
        print(f"✓ Deleted download {gid}")

        print("\n=== Complete lifecycle test PASSED ===")

    @pytest.mark.asyncio
    async def test_add_download_success(self, service):
        """Test successfully adding a download."""
        mock_client = service._test_mock_client
        test_gid = "add123"
        test_url = "http://example.com/file.zip"

        # Setup mock
        mock_client.add_uri.return_value = test_gid
        mock_client.tell_status.return_value = MagicMock(
            gid=test_gid,
            raw={
                "gid": test_gid,
                "status": "active",
                "totalLength": "2000000",
                "completedLength": "0",
                "downloadSpeed": "0",
                "uploadSpeed": "0",
                "files": [],
                "connections": "0",
                "dir": "/downloads",
                "uris": [test_url],
            },
        )

        # Execute
        gid = await service.add_download([test_url])

        # Verify
        assert gid == test_gid
        mock_client.add_uri.assert_called_once()

        # Verify download is tracked
        download = service.get_download(gid)
        assert download is not None
        assert download.gid == test_gid
        assert download.status == DownloadStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_add_download_with_options(self, service):
        """Test adding download with custom options."""
        mock_client = service._test_mock_client
        test_gid = "opts456"
        test_url = "http://example.com/large-file.zip"
        test_options = {
            "dir": "/custom/path",
            "max-connection-per-server": "8",
            "split": "8",
        }

        # Setup mock
        mock_client.add_uri.return_value = test_gid
        mock_client.tell_status.return_value = MagicMock(
            gid=test_gid,
            raw={
                "gid": test_gid,
                "status": "active",
                "totalLength": "10000000",
                "completedLength": "0",
                "downloadSpeed": "0",
                "uploadSpeed": "0",
                "files": [],
                "connections": "0",
                "dir": "/custom/path",
                "uris": [test_url],
            },
        )

        # Execute with options
        gid = await service.add_download([test_url], options=test_options)

        # Verify
        assert gid == test_gid
        # Verify options were passed to add_uri
        call_args = mock_client.add_uri.call_args
        assert call_args is not None
        assert call_args[0][0] == [test_url]  # First positional arg is uris
        assert call_args[1].get("options") == test_options  # Named arg is options

    @pytest.mark.asyncio
    async def test_pause_download_success(self, service):
        """Test successfully pausing an active download."""
        mock_client = service._test_mock_client
        test_gid = "pause789"

        # Add download first
        service.download_mgr.update_download(
            test_gid,
            {
                "gid": test_gid,
                "status": "active",
                "totalLength": "1000000",
                "completedLength": "500000",
                "downloadSpeed": "10000",
                "uploadSpeed": "0",
                "files": [],
                "connections": "4",
            },
        )

        # Setup pause mock
        mock_client.pause.return_value = test_gid
        mock_client.tell_status.return_value = MagicMock(
            gid=test_gid,
            raw={
                "gid": test_gid,
                "status": "paused",
                "totalLength": "1000000",
                "completedLength": "500000",
                "downloadSpeed": "0",
                "uploadSpeed": "0",
                "files": [],
                "connections": "0",
            },
        )

        # Execute pause
        result = await service.pause_download(test_gid)

        # Verify
        assert result is True
        mock_client.pause.assert_called_once_with(test_gid)

        # Verify state updated
        download = service.get_download(test_gid)
        assert download.status == DownloadStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume_download_success(self, service):
        """Test successfully resuming a paused download."""
        mock_client = service._test_mock_client
        test_gid = "resume321"

        # Add paused download first
        service.download_mgr.update_download(
            test_gid,
            {
                "gid": test_gid,
                "status": "paused",
                "totalLength": "1000000",
                "completedLength": "700000",
                "downloadSpeed": "0",
                "uploadSpeed": "0",
                "files": [],
                "connections": "0",
            },
        )

        # Setup resume mock
        mock_client.unpause.return_value = test_gid
        mock_client.tell_status.return_value = MagicMock(
            gid=test_gid,
            raw={
                "gid": test_gid,
                "status": "active",
                "totalLength": "1000000",
                "completedLength": "700000",
                "downloadSpeed": "15000",
                "uploadSpeed": "0",
                "files": [],
                "connections": "4",
            },
        )

        # Execute resume
        result = await service.resume_download(test_gid)

        # Verify
        assert result is True
        mock_client.unpause.assert_called_once_with(test_gid)

        # Verify state updated
        download = service.get_download(test_gid)
        assert download.status == DownloadStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_delete_download_success(self, service):
        """Test successfully removing a download."""
        mock_client = service._test_mock_client
        test_gid = "delete654"

        # Add download first
        service.download_mgr.update_download(
            test_gid,
            {
                "gid": test_gid,
                "status": "active",
                "totalLength": "1000000",
                "completedLength": "200000",
                "downloadSpeed": "5000",
                "uploadSpeed": "0",
                "files": [],
                "connections": "2",
            },
        )

        # Setup remove mock
        mock_client.remove.return_value = test_gid
        mock_client.tell_active.return_value = []
        mock_client.tell_waiting.return_value = []
        mock_client.tell_stopped.return_value = []

        # Execute remove
        result = await service.remove_download(test_gid)

        # Verify
        assert result is True
        mock_client.remove.assert_called_once_with(test_gid)


class TestErrorHandling:
    """Test error handling for download operations."""

    @pytest.mark.asyncio
    async def test_add_download_not_connected(self):
        """Test add_download fails when not connected."""
        service = Aria2Service()
        await service.initialize()

        # Don't connect - service should detect no connection
        with pytest.raises(DownloadOperationError, match="Not connected"):
            await service.add_download(["http://example.com/file.zip"])

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_pause_download_not_connected(self):
        """Test pause fails when not connected."""
        service = Aria2Service()
        await service.initialize()

        with pytest.raises(DownloadOperationError, match="Not connected"):
            await service.pause_download("test-gid")

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_resume_download_not_connected(self):
        """Test resume fails when not connected."""
        service = Aria2Service()
        await service.initialize()

        with pytest.raises(DownloadOperationError, match="Not connected"):
            await service.resume_download("test-gid")

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_remove_download_not_connected(self):
        """Test remove fails when not connected."""
        service = Aria2Service()
        await service.initialize()

        with pytest.raises(DownloadOperationError, match="Not connected"):
            await service.remove_download("test-gid")

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_pause_download_invalid_gid(self, service):
        """Test pause fails with invalid GID."""
        mock_client = service._test_mock_client

        # Mock aria2 error for invalid GID
        mock_client.pause.side_effect = Aria2Error("GID not found")

        with pytest.raises(DownloadOperationError, match="Failed to pause"):
            await service.pause_download("invalid-gid")

    @pytest.mark.asyncio
    async def test_resume_download_invalid_gid(self, service):
        """Test resume fails with invalid GID."""
        mock_client = service._test_mock_client

        # Mock aria2 error for invalid GID
        mock_client.unpause.side_effect = Aria2Error("GID not found")

        with pytest.raises(DownloadOperationError, match="Failed to resume"):
            await service.resume_download("invalid-gid")

    @pytest.mark.asyncio
    async def test_add_download_aria2_error(self, service):
        """Test that Aria2Error during add is wrapped in DownloadOperationError."""
        mock_client = service._test_mock_client

        # Mock aria2 connection error
        mock_client.add_uri.side_effect = Aria2Error("Connection refused")

        with pytest.raises(DownloadOperationError, match="Failed to add download"):
            await service.add_download(["http://example.com/file.zip"])


class TestAdvancedOptions:
    """Test advanced download operations."""

    @pytest.mark.asyncio
    async def test_delete_download_force(self, service):
        """Test force removing an active download."""
        mock_client = service._test_mock_client
        test_gid = "force987"

        # Add active download
        service.download_mgr.update_download(
            test_gid,
            {
                "gid": test_gid,
                "status": "active",
                "totalLength": "5000000",
                "completedLength": "2000000",
                "downloadSpeed": "100000",
                "uploadSpeed": "0",
                "files": [],
                "connections": "8",
            },
        )

        # Setup force remove mock
        mock_client.force_remove.return_value = test_gid
        mock_client.tell_active.return_value = []
        mock_client.tell_waiting.return_value = []
        mock_client.tell_stopped.return_value = []

        # Execute force remove
        result = await service.remove_download(test_gid, force=True)

        # Verify
        assert result is True
        mock_client.force_remove.assert_called_once_with(test_gid)
        # Verify normal remove was NOT called
        mock_client.remove.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_multiple_urls(self, service):
        """Test adding download with multiple URLs (mirrors)."""
        mock_client = service._test_mock_client
        test_gid = "multi123"
        test_urls = [
            "http://mirror1.example.com/file.zip",
            "http://mirror2.example.com/file.zip",
            "http://mirror3.example.com/file.zip",
        ]

        # Setup mock - files should contain uris array for URL extraction
        mock_client.add_uri.return_value = test_gid
        mock_client.tell_status.return_value = MagicMock(
            gid=test_gid,
            raw={
                "gid": test_gid,
                "status": "active",
                "totalLength": "5000000",
                "completedLength": "0",
                "downloadSpeed": "0",
                "uploadSpeed": "0",
                "files": [
                    {
                        "index": "1",
                        "path": "/downloads/file.zip",
                        "length": "5000000",
                        "completedLength": "0",
                        "uris": [{"uri": url, "status": "used"} for url in test_urls],
                    }
                ],
                "connections": "0",
                "dir": "/downloads",
            },
        )

        # Execute with multiple URLs
        gid = await service.add_download(test_urls)

        # Verify
        assert gid == test_gid
        # Verify all URLs were passed
        call_args = mock_client.add_uri.call_args
        assert call_args[0][0] == test_urls

        # Verify download has all URLs
        download = service.get_download(gid)
        assert download is not None
        assert len(download.urls) == 3
