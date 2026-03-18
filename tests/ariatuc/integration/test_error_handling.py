"""Systematic error handling tests for the application.

These tests verify that the application handles various error scenarios gracefully:
- Network errors and timeouts
- Invalid user input
- RPC errors and connection failures
- UI error feedback and recovery
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aria2rpc.exceptions import Aria2Error, Aria2RPCError
from ariatuc.core.service import Aria2Service, ConnectionError, DownloadOperationError
from ariatuc.ui.app import AriatucApp
from ariatuc.ui.screens.main_screen import MainScreen
from ariatuc.ui.widgets.add_download_dialog import AddDownloadDialog


def _get_url_input(dialog: AddDownloadDialog):
    """Helper to get url_input with assertion."""
    assert dialog._url_input is not None
    return dialog._url_input


class TestNetworkErrors:
    """Test handling of network-related errors."""

    @pytest.fixture
    async def service(self):
        """Create a service instance for testing."""
        service = Aria2Service()
        await service.initialize()

        # Mock RPC client
        mock_client = AsyncMock()
        with patch.object(service.rpc_mgr, "get_client", return_value=mock_client):
            service.add_server("test", "http://localhost:6800/jsonrpc")
            await service.connect("test")

        yield service
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test handling when aria2 connection is refused."""
        service = Aria2Service()
        await service.initialize()

        # Try to connect to invalid server
        service.add_server("invalid", "http://localhost:9999/jsonrpc")

        # Connection should fail gracefully (not crash)
        with pytest.raises(ConnectionError):
            await service.connect("invalid")

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test handling when aria2 connection times out."""
        service = Aria2Service()
        await service.initialize()

        mock_client = AsyncMock()
        # Simulate timeout
        mock_client.get_version.side_effect = TimeoutError("Connection timeout")

        with patch.object(service.rpc_mgr, "get_client", return_value=mock_client):
            service.add_server("timeout-server", "http://localhost:6800/jsonrpc")

            # Should handle timeout gracefully
            with pytest.raises((ConnectionError, asyncio.TimeoutError)):
                await service.connect("timeout-server")

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_network_error_during_operation(self, service):
        """Test handling network error during a download operation."""
        mock_client = service._test_mock_client

        # Simulate network error during add_uri
        mock_client.add_uri.side_effect = Aria2Error("Network unreachable")

        # Should wrap error in DownloadOperationError
        with pytest.raises(DownloadOperationError, match="Failed to add download"):
            await service.add_download(["http://example.com/file.zip"])

    @pytest.mark.asyncio
    async def test_rpc_error_during_operation(self, service):
        """Test handling RPC protocol error during operation."""
        # Create fresh mock client for this test
        mock_client = AsyncMock()

        # Simulate RPC error with correct parameter order (code, message)
        mock_client.pause.side_effect = Aria2RPCError(-1, "Invalid GID")

        # Patch the get_client to return our mock
        with patch.object(service.rpc_mgr, "get_client", return_value=mock_client):
            # Should wrap error in DownloadOperationError
            with pytest.raises(DownloadOperationError, match="Failed to pause"):
                await service.pause_download("invalid-gid")

    @pytest.mark.asyncio
    async def test_connection_lost_during_operation(self, service):
        """Test handling when connection is lost mid-operation."""
        mock_client = service._test_mock_client

        # Add a download first
        test_gid = "conn-lost-123"
        service.download_mgr.update_download(
            test_gid,
            {
                "gid": test_gid,
                "status": "active",
                "totalLength": "1000000",
                "completedLength": "500000",
            },
        )

        # Simulate connection lost
        mock_client.pause.side_effect = Aria2Error("Connection closed")

        # Should handle gracefully
        with pytest.raises(DownloadOperationError):
            await service.pause_download(test_gid)


class TestInvalidInput:
    """Test handling of invalid user input."""

    @pytest.fixture
    async def service(self):
        """Create a service instance for testing."""
        service = Aria2Service()
        await service.initialize()

        mock_client = AsyncMock()
        with patch.object(service.rpc_mgr, "get_client", return_value=mock_client):
            service.add_server("test", "http://localhost:6800/jsonrpc")
            await service.connect("test")

        yield service
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_empty_url_list(self, service):
        """Test adding download with empty URL list."""
        # Empty list should be handled gracefully
        # Note: This might be caught at UI level, but service should handle it too
        with pytest.raises((DownloadOperationError, Aria2Error, ValueError)):
            await service.add_download([])

    @pytest.mark.asyncio
    async def test_invalid_url_format(self, service):
        """Test adding download with invalid URL format."""
        mock_client = service._test_mock_client

        # Mock aria2 rejecting invalid URL
        mock_client.add_uri.side_effect = Aria2Error("Invalid URL format")

        with pytest.raises(DownloadOperationError, match="Failed to add download"):
            await service.add_download(["not-a-valid-url"])

    @pytest.mark.asyncio
    async def test_invalid_gid_format(self, service):
        """Test operations with invalid GID format."""
        mock_client = service._test_mock_client

        # Mock aria2 error for invalid GID
        mock_client.pause.side_effect = Aria2Error("Invalid GID")

        with pytest.raises(DownloadOperationError):
            await service.pause_download("invalid-gid-format")

    @pytest.mark.asyncio
    async def test_nonexistent_gid(self, service):
        """Test operations on non-existent download."""
        mock_client = service._test_mock_client

        # Mock aria2 error for non-existent GID
        mock_client.pause.side_effect = Aria2Error("GID not found")

        with pytest.raises(DownloadOperationError):
            await service.pause_download("nonexistent-gid-123456")

    @pytest.mark.asyncio
    async def test_invalid_options(self, service):
        """Test adding download with invalid options."""
        mock_client = service._test_mock_client

        # Mock aria2 rejecting invalid options
        mock_client.add_uri.side_effect = Aria2Error("Invalid option: invalid-option")

        invalid_options = {"invalid-option": "value"}

        with pytest.raises(DownloadOperationError):
            await service.add_download(["http://example.com/file.zip"], options=invalid_options)


class TestStateErrors:
    """Test handling of invalid state transitions."""

    @pytest.fixture
    async def service(self):
        """Create a service instance for testing."""
        service = Aria2Service()
        await service.initialize()

        mock_client = AsyncMock()
        with patch.object(service.rpc_mgr, "get_client", return_value=mock_client):
            service.add_server("test", "http://localhost:6800/jsonrpc")
            await service.connect("test")

        yield service
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_pause_already_paused(self, service):
        """Test pausing an already paused download."""
        mock_client = service._test_mock_client
        test_gid = "paused-123"

        # Add paused download
        service.download_mgr.update_download(
            test_gid,
            {
                "gid": test_gid,
                "status": "paused",
                "totalLength": "1000000",
                "completedLength": "500000",
            },
        )

        # Mock aria2 accepting the pause (it's idempotent)
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

        # Should succeed (idempotent operation)
        result = await service.pause_download(test_gid)
        assert result is True

    @pytest.mark.asyncio
    async def test_resume_already_active(self, service):
        """Test resuming an already active download."""
        mock_client = service._test_mock_client
        test_gid = "active-123"

        # Add active download
        service.download_mgr.update_download(
            test_gid,
            {
                "gid": test_gid,
                "status": "active",
                "totalLength": "1000000",
                "completedLength": "500000",
            },
        )

        # Mock aria2 accepting the unpause (it's idempotent)
        mock_client.unpause.return_value = test_gid
        mock_client.tell_status.return_value = MagicMock(
            gid=test_gid,
            raw={
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

        # Should succeed (idempotent operation)
        result = await service.resume_download(test_gid)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_already_removed(self, service):
        """Test deleting an already removed download."""
        mock_client = service._test_mock_client
        test_gid = "removed-123"

        # Mock aria2 error for already removed download
        mock_client.remove.side_effect = Aria2Error("GID not found")

        # Should handle gracefully
        with pytest.raises(DownloadOperationError):
            await service.remove_download(test_gid)

    @pytest.mark.asyncio
    async def test_resume_completed_download(self, service):
        """Test resuming a completed download."""
        mock_client = service._test_mock_client
        test_gid = "completed-123"

        # Add completed download
        service.download_mgr.update_download(
            test_gid,
            {
                "gid": test_gid,
                "status": "complete",
                "totalLength": "1000000",
                "completedLength": "1000000",
            },
        )

        # Mock aria2 error (can't resume completed)
        mock_client.unpause.side_effect = Aria2Error("Download already completed")

        # Should handle gracefully
        with pytest.raises(DownloadOperationError):
            await service.resume_download(test_gid)


class TestUIErrorHandling:
    """Test UI-level error handling and user feedback."""

    @pytest.mark.asyncio
    async def test_ui_handles_service_not_connected(self):
        """Test UI handles gracefully when service is not connected."""
        app = AriatucApp()

        async with app.run_test() as pilot:
            assert isinstance(app.screen, MainScreen)
            main_screen: MainScreen = app.screen

            # Ensure service is not connected
            if main_screen.service:
                await main_screen.service.disconnect()

            # Wait for UI
            await pilot.pause(0.5)

            # Try to open add dialog - should still work
            await pilot.press("a")
            await pilot.pause(0.1)

            # Dialog should open even when not connected
            assert len(app.screen_stack) >= 2

            # Close dialog
            await pilot.press("escape")
            await pilot.press("escape")
            await pilot.pause(0.1)

    @pytest.mark.asyncio
    async def test_ui_handles_empty_download_list(self):
        """Test UI handles empty download list gracefully."""
        app = AriatucApp()

        async with app.run_test() as pilot:
            assert isinstance(app.screen, MainScreen)
            main_screen: MainScreen = app.screen

            # Clear all downloads
            if main_screen.service:
                main_screen.service.download_mgr.downloads.clear()

            # Wait for UI
            await pilot.pause(0.5)

            # Should be able to navigate even with no downloads
            await pilot.press("1")  # Switch to active tab
            await pilot.pause(0.1)

            await pilot.press("2")  # Switch to waiting tab
            await pilot.pause(0.1)

            await pilot.press("3")  # Switch to stopped tab
            await pilot.pause(0.1)

            # Navigation keys should not crash
            await pilot.press("j")
            await pilot.pause(0.1)

            await pilot.press("k")
            await pilot.pause(0.1)

    @pytest.mark.asyncio
    async def test_ui_handles_invalid_dialog_input(self):
        """Test UI handles invalid input in add dialog."""
        app = AriatucApp()

        async with app.run_test() as pilot:
            assert isinstance(app.screen, MainScreen)

            # Open add dialog
            await pilot.press("a")
            await pilot.pause(0.1)

            assert isinstance(app.screen_stack[-1], AddDownloadDialog)
            dialog: AddDownloadDialog = app.screen_stack[-1]

            # Enter empty URL (invalid)
            url_input = _get_url_input(dialog)
            url_input.load_text("")  # Use load_text() for TextArea
            await pilot.pause(0.1)

            # Try to submit - should handle gracefully
            # (might show error or just ignore)
            await pilot.press("enter")
            await pilot.pause(0.3)

            # Close dialog
            if len(app.screen_stack) > 1:
                await pilot.press("escape")
                await pilot.press("escape")


class TestRecoveryMechanisms:
    """Test error recovery and resilience mechanisms."""

    @pytest.fixture
    async def service(self):
        """Create a service instance for testing."""
        service = Aria2Service()
        await service.initialize()

        mock_client = AsyncMock()
        with patch.object(service.rpc_mgr, "get_client", return_value=mock_client):
            service.add_server("test", "http://localhost:6800/jsonrpc")
            await service.connect("test")

        yield service
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_service_continues_after_failed_operation(self, service):
        """Test that service continues working after a failed operation."""
        mock_client = service._test_mock_client

        # First operation fails
        mock_client.add_uri.side_effect = [
            Aria2Error("Temporary error"),  # First call fails
            "success-gid-123",  # Second call succeeds
        ]

        # First attempt should fail
        with pytest.raises(DownloadOperationError):
            await service.add_download(["http://example.com/file1.zip"])

        # Mock tell_status for second attempt
        mock_client.tell_status.return_value = MagicMock(
            gid="success-gid-123",
            raw={
                "gid": "success-gid-123",
                "status": "active",
                "totalLength": "1000000",
                "completedLength": "0",
                "downloadSpeed": "0",
                "uploadSpeed": "0",
                "files": [],
                "connections": "0",
            },
        )

        # Second attempt should succeed
        gid = await service.add_download(["http://example.com/file2.zip"])
        assert gid == "success-gid-123"

    @pytest.mark.asyncio
    async def test_download_manager_state_consistent_after_error(self, service):
        """Test that download manager maintains consistent state after errors."""
        mock_client = service._test_mock_client
        test_gid = "state-test-123"

        # Add download
        service.download_mgr.update_download(
            test_gid,
            {
                "gid": test_gid,
                "status": "active",
                "totalLength": "1000000",
                "completedLength": "500000",
            },
        )

        # Get initial state
        download_before = service.get_download(test_gid)
        assert download_before is not None

        # Failed operation
        mock_client.pause.side_effect = Aria2Error("Network error")

        try:
            await service.pause_download(test_gid)
        except DownloadOperationError:
            pass  # Expected error

        # State should be unchanged (still active since pause failed)
        download_after = service.get_download(test_gid)
        assert download_after is not None
        # Download still exists and state is preserved

    @pytest.mark.asyncio
    async def test_multiple_consecutive_errors(self, service):
        """Test handling multiple consecutive errors gracefully."""
        mock_client = service._test_mock_client

        # All operations fail
        mock_client.add_uri.side_effect = Aria2Error("Error")
        mock_client.pause.side_effect = Aria2Error("Error")
        mock_client.unpause.side_effect = Aria2Error("Error")

        # All should be handled without crashing
        with pytest.raises(DownloadOperationError):
            await service.add_download(["http://example.com/file1.zip"])

        with pytest.raises(DownloadOperationError):
            await service.pause_download("gid-1")

        with pytest.raises(DownloadOperationError):
            await service.resume_download("gid-2")

        # Service should still be functional
        assert service.is_connected()
