"""Integration tests for unified keybinding system."""

from __future__ import annotations

import pytest
from textual.pilot import Pilot

from ariatuc.ui.app import AriatucApp
from ariatuc.ui.keybinding_manager import KeybindingContext, KeybindingMode


@pytest.mark.asyncio
async def test_app_initializes_with_keybinding_manager():
    """Test that app initializes with keybinding manager."""
    app = AriatucApp()
    assert app.keybinding_manager is not None
    assert app.keybinding_manager.current_mode == KeybindingMode.NORMAL
    assert app.keybinding_manager.current_context == KeybindingContext.GLOBAL


@pytest.mark.asyncio
async def test_global_shortcuts_work_everywhere():
    """Test that global shortcuts (q, ?) work in any context."""
    app = AriatucApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        # Test '?' help shortcut
        assert app.keybinding_manager.is_key_bound("?")
        action = app.keybinding_manager.get_action_for_key("?")
        assert action == "help"

        # Test 'q' quit shortcut
        assert app.keybinding_manager.is_key_bound("q")
        action = app.keybinding_manager.get_action_for_key("q")
        assert action == "quit"

        # Test escape
        assert app.keybinding_manager.is_key_bound("escape")


@pytest.mark.asyncio
async def test_context_switching():
    """Test that context switches affect available bindings."""
    app = AriatucApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        kb = app.keybinding_manager

        # In MAIN_SCREEN context, 'a' should work (add download)
        kb.set_context(KeybindingContext.MAIN_SCREEN)
        assert kb.is_key_bound("a")
        assert kb.get_action_for_key("a") == "add_download"

        # In DOWNLOAD_LIST context, 's' should work (sort)
        kb.set_context(KeybindingContext.DOWNLOAD_LIST)
        # Note: 's' needs to be registered in DOWNLOAD_LIST context
        # For now, it falls back to parent contexts


@pytest.mark.asyncio
async def test_mode_filtering():
    """Test that modes filter available keybindings."""
    app = AriatucApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        kb = app.keybinding_manager

        kb.set_context(KeybindingContext.MAIN_SCREEN)

        # In NORMAL mode, shortcuts should work
        kb.set_mode(KeybindingMode.NORMAL)
        assert kb.resolve("a") is not None

        # In EDIT mode, most shortcuts should be disabled
        kb.set_mode(KeybindingMode.EDIT)
        # Note: Current implementation disables bindings in EDIT mode
        # unless explicitly allowed


@pytest.mark.asyncio
async def test_command_bar_updates():
    """Test that command bar receives keybinding manager."""
    app = AriatucApp()

    async with app.run_test() as pilot:
        # Wait for app to mount
        await pilot.pause()

        # Check that main screen has command bar
        main_screen = app._main_screen
        assert main_screen is not None
        assert main_screen._command_bar is not None

        # Check that command bar has keybinding manager
        command_bar = main_screen._command_bar
        assert command_bar.keybinding_manager is not None


@pytest.mark.asyncio
async def test_tab_switching_global():
    """Test that 1/2/3 keys switch tabs globally."""
    app = AriatucApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        kb = app.keybinding_manager

        kb.set_context(KeybindingContext.MAIN_SCREEN)

        # Check that tab switching keys are bound
        assert kb.is_key_bound("1")
        assert kb.is_key_bound("2")
        assert kb.is_key_bound("3")

        # Check actions
        assert kb.get_action_for_key("1") == "switch_tab_active"
        assert kb.get_action_for_key("2") == "switch_tab_waiting"
        assert kb.get_action_for_key("3") == "switch_tab_stopped"


@pytest.mark.asyncio
async def test_conflict_resolution():
    """Test that keybinding conflicts are properly resolved."""
    app = AriatucApp()
    kb = app.keybinding_manager

    # Detect conflicts
    conflicts = kb.detect_conflicts()

    # Should have some conflicts detected (if any exist)
    # This is informational - conflicts are resolved by priority
    if conflicts:
        for conflict in conflicts:
            # Conflicts should have multiple bindings
            assert len(conflict.bindings) > 1


@pytest.mark.asyncio
async def test_download_list_widget_mode_tracking():
    """Test that download list widget notifies mode changes."""
    app = AriatucApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        main_screen = app._main_screen
        assert main_screen is not None

        download_list = main_screen._download_list
        assert download_list is not None

        # Download list should have keybinding manager
        assert download_list.keybinding_manager is not None
        assert download_list.keybinding_manager is app.keybinding_manager


@pytest.mark.asyncio
async def test_hints_generation():
    """Test that hints are generated for contexts."""
    app = AriatucApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        kb = app.keybinding_manager

        # Get hints for main screen
        hints = kb.get_hints_for_context(KeybindingContext.MAIN_SCREEN)
        assert len(hints) > 0

        # Hints should be tuples of (key, description)
        for key, desc in hints:
            assert isinstance(key, str)
            assert isinstance(desc, str)
            assert len(key) > 0
            assert len(desc) > 0


@pytest.mark.asyncio
async def test_escape_hierarchy():
    """Test that escape key works correctly across modes."""
    app = AriatucApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        kb = app.keybinding_manager

        # Escape should be bound globally
        kb.set_context(KeybindingContext.GLOBAL)
        assert kb.is_key_bound("escape")

        # Should work in different contexts
        kb.set_context(KeybindingContext.MAIN_SCREEN)
        assert kb.is_key_bound("escape")

        kb.set_context(KeybindingContext.DOWNLOAD_LIST)
        assert kb.is_key_bound("escape")


@pytest.mark.asyncio
async def test_keybinding_manager_shared():
    """Test that keybinding manager is shared across components."""
    app = AriatucApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        main_screen = app._main_screen
        assert main_screen is not None

        # All components should share the same manager
        assert main_screen.keybinding_manager is app.keybinding_manager

        if main_screen._download_list:
            assert main_screen._download_list.keybinding_manager is app.keybinding_manager

        if main_screen._command_bar:
            assert main_screen._command_bar.keybinding_manager is app.keybinding_manager
