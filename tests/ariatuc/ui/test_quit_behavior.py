"""Tests for context-aware quit key behavior."""

import pytest

from ariatuc.ui.app import AriatucApp
from ariatuc.ui.screens.help_screen import HelpScreen
from ariatuc.ui.screens.server_management_screen import ServerManagementScreen


@pytest.mark.asyncio
async def test_quit_dismisses_help_screen():
    """Test 'q' dismisses help screen instead of quitting app."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        # Push help screen
        initial_stack_size = len(app.screen_stack)
        await app.push_screen(HelpScreen())

        # Verify screen was pushed
        assert len(app.screen_stack) == initial_stack_size + 1

        # Press 'q' should dismiss modal
        await pilot.press("q")
        await pilot.pause()

        # Verify screen was dismissed (stack size decreased)
        assert len(app.screen_stack) == initial_stack_size


@pytest.mark.asyncio
async def test_quit_dismisses_settings_screen():
    """Test 'q' dismisses settings screen instead of quitting app."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        # Push server management screen
        initial_stack_size = len(app.screen_stack)
        await app.push_screen(ServerManagementScreen(service=app.service))

        # Verify screen was pushed
        assert len(app.screen_stack) == initial_stack_size + 1

        # Press 'q' should dismiss modal
        await pilot.press("q")
        await pilot.pause()

        # Verify screen was dismissed
        assert len(app.screen_stack) == initial_stack_size


@pytest.mark.asyncio
async def test_any_key_closes_help_screen():
    """Test HelpScreen still closes on any key press (existing behavior)."""
    app = AriatucApp()
    async with app.run_test() as pilot:
        # Push help screen
        initial_stack_size = len(app.screen_stack)
        await app.push_screen(HelpScreen())

        # Press any key (not 'q') should also close
        await pilot.press("x")
        await pilot.pause()

        # Verify screen was dismissed
        assert len(app.screen_stack) == initial_stack_size
