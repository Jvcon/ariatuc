"""Unit tests for KeybindingManager."""

from __future__ import annotations

import pytest

from ariatuc.ui.keybinding_manager import (
    Keybinding,
    KeybindingContext,
    KeybindingManager,
    KeybindingMode,
)


def test_register_and_resolve():
    """Test basic registration and resolution."""
    manager = KeybindingManager()

    # Register a binding
    binding = Keybinding("a", "add", "Add", KeybindingContext.MAIN_SCREEN)
    manager.register(binding)

    # Set context
    manager.set_context(KeybindingContext.MAIN_SCREEN)

    # Resolve
    result = manager.resolve("a")
    assert result is not None
    action, context = result
    assert action == "add"
    assert context == KeybindingContext.MAIN_SCREEN


def test_context_priority():
    """Test that more specific context wins."""
    manager = KeybindingManager()

    # Register same key in different contexts
    manager.register(Keybinding("s", "search", "Search", KeybindingContext.MAIN_SCREEN))
    manager.register(Keybinding("s", "sort", "Sort", KeybindingContext.DOWNLOAD_LIST, priority=10))

    # In DOWNLOAD_LIST context, more specific binding should win
    manager.set_context(KeybindingContext.DOWNLOAD_LIST)
    result = manager.resolve("s")
    assert result is not None
    assert result[0] == "sort"

    # In MAIN_SCREEN context, only main screen binding available
    manager.set_context(KeybindingContext.MAIN_SCREEN)
    result = manager.resolve("s")
    assert result is not None
    assert result[0] == "search"


def test_mode_filtering():
    """Test that bindings are filtered by mode."""
    manager = KeybindingManager()

    # Register binding only for NORMAL mode
    binding = Keybinding(
        "a",
        "add",
        "Add",
        KeybindingContext.MAIN_SCREEN,
        modes=[KeybindingMode.NORMAL],
    )
    manager.register(binding)
    manager.set_context(KeybindingContext.MAIN_SCREEN)

    # Should work in NORMAL mode
    manager.set_mode(KeybindingMode.NORMAL)
    result = manager.resolve("a")
    assert result is not None
    assert result[0] == "add"

    # Should not work in EDIT mode
    manager.set_mode(KeybindingMode.EDIT)
    result = manager.resolve("a")
    assert result is None


def test_global_context():
    """Test that global bindings work in any context."""
    manager = KeybindingManager()

    # Register global binding
    manager.register(Keybinding("q", "quit", "Quit", KeybindingContext.GLOBAL))

    # Should work in any context
    for context in KeybindingContext:
        manager.set_context(context)
        result = manager.resolve("q")
        assert result is not None
        assert result[0] == "quit"


def test_get_hints_for_context():
    """Test getting hints for command bar."""
    manager = KeybindingManager()

    # Register several bindings
    manager.register(Keybinding("a", "add", "Add", KeybindingContext.MAIN_SCREEN))
    manager.register(Keybinding("d", "delete", "Delete", KeybindingContext.MAIN_SCREEN))
    manager.register(Keybinding("q", "quit", "Quit", KeybindingContext.GLOBAL))

    # Get hints for main screen
    manager.set_mode(KeybindingMode.NORMAL)
    hints = manager.get_hints_for_context(KeybindingContext.MAIN_SCREEN)

    # Should include main screen and global bindings
    hint_keys = [key for key, _ in hints]
    assert "a" in hint_keys
    assert "d" in hint_keys
    assert "q" in hint_keys


def test_detect_conflicts():
    """Test conflict detection."""
    manager = KeybindingManager()

    # Register conflicting bindings (same key, context, priority, overlapping modes)
    manager.register(Keybinding("s", "search", "Search", KeybindingContext.MAIN_SCREEN, priority=0))
    manager.register(Keybinding("s", "sort", "Sort", KeybindingContext.MAIN_SCREEN, priority=0))

    # Detect conflicts
    conflicts = manager.detect_conflicts()
    assert len(conflicts) > 0
    assert conflicts[0].key == "s"


def test_escape_hierarchy():
    """Test escape key resolution across modes."""
    manager = KeybindingManager()

    # Register escape for different purposes
    manager.register(
        Keybinding("escape", "exit_search", "Exit Search", KeybindingContext.MAIN_SCREEN)
    )

    manager.set_context(KeybindingContext.MAIN_SCREEN)
    manager.set_mode(KeybindingMode.NORMAL)

    result = manager.resolve("escape")
    assert result is not None
    assert result[0] == "exit_search"


def test_is_key_bound():
    """Test checking if key is bound."""
    manager = KeybindingManager()

    manager.register(Keybinding("a", "add", "Add", KeybindingContext.MAIN_SCREEN))
    manager.set_context(KeybindingContext.MAIN_SCREEN)

    assert manager.is_key_bound("a")
    assert not manager.is_key_bound("z")


def test_get_action_for_key():
    """Test convenience method to get action."""
    manager = KeybindingManager()

    manager.register(Keybinding("a", "add", "Add", KeybindingContext.MAIN_SCREEN))
    manager.set_context(KeybindingContext.MAIN_SCREEN)

    action = manager.get_action_for_key("a")
    assert action == "add"

    action = manager.get_action_for_key("z")
    assert action is None


def test_register_batch():
    """Test batch registration."""
    manager = KeybindingManager()

    bindings = [
        Keybinding("a", "add", "Add", KeybindingContext.MAIN_SCREEN),
        Keybinding("d", "delete", "Delete", KeybindingContext.MAIN_SCREEN),
        Keybinding("p", "pause", "Pause", KeybindingContext.MAIN_SCREEN),
    ]

    manager.register_batch(bindings)
    manager.set_context(KeybindingContext.MAIN_SCREEN)

    assert manager.is_key_bound("a")
    assert manager.is_key_bound("d")
    assert manager.is_key_bound("p")
