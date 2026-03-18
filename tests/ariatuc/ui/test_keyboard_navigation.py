"""Tests for keyboard navigation and interaction system."""

import pytest

from ariatuc.ui.app import AriatucApp
from ariatuc.ui.screens.main_screen import MainScreen
from ariatuc.ui.widgets.add_download_dialog import AddDownloadDialog


def _get_download_list(main_screen: MainScreen):
    """Helper to get download_list with assertion."""
    assert main_screen._download_list is not None
    return main_screen._download_list


def _get_download_detail(main_screen: MainScreen):
    """Helper to get download_detail with assertion."""
    assert main_screen._download_detail is not None
    return main_screen._download_detail


def _get_url_input(dialog: AddDownloadDialog):
    """Helper to get url_input with assertion."""
    assert dialog._url_input is not None
    return dialog._url_input


def _get_active_table(download_list):
    """Helper to get active_table with assertion."""
    assert download_list._active_table is not None
    return download_list._active_table


@pytest.mark.asyncio
async def test_panel_switching_with_H_L():
    """Test H/L keys switch between left and right panels."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        # Get main screen reference
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Focus left panel initially
        await pilot.press("H")
        assert main_screen._get_focused_panel() == "left"

        # Press L to focus right panel
        await pilot.press("L")
        assert main_screen._get_focused_panel() == "right"

        # Press H to focus left panel
        await pilot.press("H")
        assert main_screen._get_focused_panel() == "left"


@pytest.mark.asyncio
async def test_tab_switching_global():
    """Test 1/2/3 keys work regardless of panel focus."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Focus right panel
        await pilot.press("L")
        assert main_screen._get_focused_panel() == "right"

        # Press 1 to switch left panel tab (should still work)
        await pilot.press("1")
        assert _get_download_list(main_screen)._current_tab == "active"

        # Press 2 to switch to waiting
        await pilot.press("2")
        assert _get_download_list(main_screen)._current_tab == "waiting"

        # Press 3 to switch to stopped
        await pilot.press("3")
        assert _get_download_list(main_screen)._current_tab == "stopped"


@pytest.mark.asyncio
async def test_tab_cycling_with_t_T():
    """Test t/T keys cycle tabs in focused panel."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Focus left panel
        await pilot.press("H")

        # Start on active tab
        await pilot.press("1")
        assert _get_download_list(main_screen)._current_tab == "active"

        # Press t to cycle forward
        await pilot.press("t")
        assert _get_download_list(main_screen)._current_tab == "waiting"

        # Press t to cycle forward again
        await pilot.press("t")
        assert _get_download_list(main_screen)._current_tab == "stopped"

        # Press T to cycle backward
        await pilot.press("T")
        assert _get_download_list(main_screen)._current_tab == "waiting"


@pytest.mark.asyncio
async def test_dialog_two_stage_esc():
    """Test ESC twice closes dialog, once exits edit mode."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        # Store initial screen stack length
        initial_stack_len = len(app.screen_stack)

        # Open add download dialog
        await pilot.press("a")

        # Dialog should be open, input focused
        assert len(app.screen_stack) == initial_stack_len + 1
        assert isinstance(app.screen_stack[-1], AddDownloadDialog)
        dialog: AddDownloadDialog = app.screen_stack[-1]
        assert _get_url_input(dialog).has_focus

        # First ESC - should blur input
        await pilot.press("escape")
        assert not _get_url_input(dialog).has_focus
        assert len(app.screen_stack) == initial_stack_len + 1  # Dialog still open

        # Second ESC - should close dialog
        await pilot.press("escape")
        assert len(app.screen_stack) == initial_stack_len  # Back to main screen


@pytest.mark.asyncio
async def test_edit_mode_blocks_navigation_keys():
    """Test navigation keys don't trigger while in edit mode."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Open dialog - focus on input (edit mode)
        await pilot.press("a")

        # Store initial tab
        initial_tab = _get_download_list(main_screen)._current_tab

        # Try to press navigation keys while in edit mode
        # These should be ignored since we're in edit mode
        await pilot.press("1")
        await pilot.press("H")
        await pilot.press("L")

        # Tab should NOT have changed (keys ignored in edit mode)
        assert _get_download_list(main_screen)._current_tab == initial_tab

        # Close dialog
        await pilot.press("escape")
        await pilot.press("escape")


@pytest.mark.asyncio
async def test_is_in_edit_mode_detection():
    """Test is_in_edit_mode() correctly detects edit state."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Initially should not be in edit mode
        assert not main_screen.is_in_edit_mode()

        # Open dialog - focus on input (should be in edit mode)
        await pilot.press("a")
        assert main_screen.is_in_edit_mode()

        # Press ESC to blur (should exit edit mode)
        await pilot.press("escape")
        assert not main_screen.is_in_edit_mode()

        # Close dialog
        await pilot.press("escape")
        assert not main_screen.is_in_edit_mode()


@pytest.mark.asyncio
async def test_get_focused_panel_detection():
    """Test _get_focused_panel() correctly identifies focused panel."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Focus left panel
        await pilot.press("H")
        assert main_screen._get_focused_panel() == "left"

        # Focus right panel
        await pilot.press("L")
        assert main_screen._get_focused_panel() == "right"

        # Focus left panel again
        await pilot.press("H")
        assert main_screen._get_focused_panel() == "left"


@pytest.mark.asyncio
async def test_tab_switching_with_empty_downloads():
    """Test tab switching works even when no downloads exist."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Switch tabs even with no downloads
        await pilot.press("1")
        assert _get_download_list(main_screen)._current_tab == "active"

        await pilot.press("2")
        assert _get_download_list(main_screen)._current_tab == "waiting"

        await pilot.press("3")
        assert _get_download_list(main_screen)._current_tab == "stopped"

        # Cycle tabs
        await pilot.press("t")
        assert _get_download_list(main_screen)._current_tab == "active"


@pytest.mark.asyncio
async def test_list_refresh_preserves_selection():
    """Test that list refresh preserves the selected download."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen
        download_list = _get_download_list(main_screen)

        # Wait for initial data load
        await pilot.pause(0.5)

        # If there are downloads, select one
        if _get_active_table(download_list).row_count > 0:
            # Move to second row if possible
            if _get_active_table(download_list).row_count > 1:
                await pilot.press("down")

            # Get the selected GID before refresh
            selected_gid_before = download_list.get_selected_download_gid()

            # Trigger a refresh by waiting for auto-refresh interval
            await pilot.pause(1.5)

            # Check that same download is still selected
            selected_gid_after = download_list.get_selected_download_gid()
            assert selected_gid_before == selected_gid_after


@pytest.mark.asyncio
async def test_jk_navigation_works():
    """Test that j/k keys work for navigating download list."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Focus left panel
        await pilot.press("H")

        # Wait for data
        await pilot.pause(0.5)

        download_list = _get_download_list(main_screen)

        # If there are multiple downloads, test j/k navigation
        if _get_active_table(download_list).row_count > 1:
            initial_row = _get_active_table(download_list).cursor_row

            # Press j to move down
            await pilot.press("j")
            await pilot.pause(0.1)

            # Should have moved down one row
            assert _get_active_table(download_list).cursor_row == (initial_row or 0) + 1

            # Press k to move up
            await pilot.press("k")
            await pilot.pause(0.1)

            # Should be back to initial position
            assert _get_active_table(download_list).cursor_row == initial_row


@pytest.mark.asyncio
async def test_panel_focus_blocked_in_edit_mode():
    """Test H/L panel switching is blocked in edit mode."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Focus left panel
        await pilot.press("H")
        assert main_screen._get_focused_panel() == "left"

        # Open dialog (enter edit mode)
        await pilot.press("a")

        # Try to switch panels - should be blocked
        await pilot.press("L")

        # Should still be in dialog (edit mode), not switched panels
        assert main_screen.is_in_edit_mode()

        # Close dialog
        await pilot.press("escape")
        await pilot.press("escape")

        # Now H/L should work
        await pilot.press("L")
        assert main_screen._get_focused_panel() == "right"


@pytest.mark.asyncio
async def test_preview_mode_toggle_with_enter():
    """Test Enter key toggles preview mode ON/OFF."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen

        # Focus left panel
        await pilot.press("H")
        await pilot.pause(0.5)

        # Initially preview mode should be OFF
        assert not main_screen._preview_mode

        # Press Enter to enable preview mode
        await pilot.press("enter")
        assert main_screen._preview_mode

        # Press Enter again to disable preview mode
        await pilot.press("enter")
        assert not main_screen._preview_mode


@pytest.mark.asyncio
async def test_preview_mode_shows_details_when_on():
    """Test preview mode shows download details when enabled."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen
        download_list = _get_download_list(main_screen)
        download_detail = _get_download_detail(main_screen)

        # Focus left panel and wait for data
        await pilot.press("H")
        await pilot.pause(0.5)

        # If there are downloads, test preview mode
        if _get_active_table(download_list).row_count > 0:
            # Enable preview mode
            await pilot.press("enter")
            assert main_screen._preview_mode

            # Get the selected GID
            selected_gid = download_list.get_selected_download_gid()
            assert selected_gid is not None

            # Detail panel should show this download
            assert download_detail._current_gid == selected_gid


@pytest.mark.asyncio
async def test_preview_mode_clears_details_when_off():
    """Test preview mode clears detail panel when disabled."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen
        download_detail = _get_download_detail(main_screen)

        # Focus left panel and wait for data
        await pilot.press("H")
        await pilot.pause(0.5)

        # Enable preview mode
        await pilot.press("enter")
        await pilot.pause(0.2)

        # Disable preview mode
        await pilot.press("enter")
        assert not main_screen._preview_mode

        # Detail panel should be cleared
        assert download_detail._current_gid is None


@pytest.mark.asyncio
async def test_preview_mode_updates_on_jk_navigation():
    """Test preview mode auto-updates detail panel when navigating with j/k."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen
        download_list = _get_download_list(main_screen)
        download_detail = _get_download_detail(main_screen)

        # Focus left panel and wait for data
        await pilot.press("H")
        await pilot.pause(0.5)

        # Need at least 2 downloads to test navigation
        if _get_active_table(download_list).row_count > 1:
            # Enable preview mode
            await pilot.press("enter")
            assert main_screen._preview_mode

            # Get first download GID
            first_gid = download_list.get_selected_download_gid()
            assert first_gid is not None
            assert download_detail._current_gid == first_gid

            # Navigate down with j
            await pilot.press("j")
            await pilot.pause(0.2)

            # Detail panel should update to second download
            second_gid = download_list.get_selected_download_gid()
            assert second_gid != first_gid
            assert download_detail._current_gid == second_gid


@pytest.mark.asyncio
async def test_preview_mode_disabled_on_tab_switch():
    """Test preview mode is auto-disabled when switching tabs."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen
        download_detail = _get_download_detail(main_screen)

        # Focus left panel and wait for data
        await pilot.press("H")
        await pilot.pause(0.5)

        # Enable preview mode
        await pilot.press("enter")
        assert main_screen._preview_mode

        # Switch to waiting tab
        await pilot.press("2")
        await pilot.pause(0.2)

        # Preview mode should be disabled
        assert not main_screen._preview_mode

        # Detail panel should be cleared
        assert download_detail._current_gid is None


@pytest.mark.asyncio
async def test_preview_mode_no_update_when_off():
    """Test detail panel doesn't update when preview mode is OFF."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainScreen)
        main_screen: MainScreen = app.screen
        download_list = _get_download_list(main_screen)
        download_detail = _get_download_detail(main_screen)

        # Focus left panel and wait for data
        await pilot.press("H")
        await pilot.pause(0.5)

        # Preview mode should be OFF initially
        assert not main_screen._preview_mode

        # Navigate with j/k
        if _get_active_table(download_list).row_count > 1:
            await pilot.press("j")
            await pilot.pause(0.2)

            # Detail panel should NOT be updated (no GID set)
            assert download_detail._current_gid is None
