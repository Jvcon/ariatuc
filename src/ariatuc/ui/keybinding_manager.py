"""Unified keybinding management system for ariatuc.

This module provides centralized keybinding management with context-aware resolution,
mode tracking, and conflict detection. It implements a priority-based resolution system
where more specific contexts take precedence over general ones.

Key concepts:
- Context: The current UI location (GLOBAL, MAIN_SCREEN, DOWNLOAD_LIST, etc.)
- Mode: The current interaction mode (NORMAL, EDIT, SEARCH, SELECT, PREVIEW)
- Priority: Used to resolve conflicts when same key registered in same context
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class KeybindingMode(Enum):
    """Interaction modes that affect available keybindings."""

    NORMAL = "normal"  # Standard navigation and commands
    EDIT = "edit"  # Editing text in inputs/textareas
    SEARCH = "search"  # Active search/filter mode
    SELECT = "select"  # Multi-selection mode
    PREVIEW = "preview"  # Preview/detail view mode


class KeybindingContext(Enum):
    """Hierarchical contexts for keybinding resolution.

    Resolution order (most specific to least specific):
    DIALOG → SETTINGS → DOWNLOAD_DETAIL → DOWNLOAD_LIST → MAIN_SCREEN → GLOBAL
    """

    GLOBAL = "global"  # Always available (q, ?, Esc)
    MAIN_SCREEN = "main_screen"  # Main application screen
    DOWNLOAD_LIST = "download_list"  # Download list widget
    DOWNLOAD_DETAIL = "download_detail"  # Download detail widget
    SETTINGS = "settings"  # Settings screens (servers, aria2, app)
    DIALOG = "dialog"  # Modal dialogs


# Context hierarchy for resolution priority
CONTEXT_HIERARCHY: dict[KeybindingContext, list[KeybindingContext]] = {
    KeybindingContext.GLOBAL: [],
    KeybindingContext.MAIN_SCREEN: [KeybindingContext.GLOBAL],
    KeybindingContext.DOWNLOAD_LIST: [
        KeybindingContext.MAIN_SCREEN,
        KeybindingContext.GLOBAL,
    ],
    KeybindingContext.DOWNLOAD_DETAIL: [
        KeybindingContext.MAIN_SCREEN,
        KeybindingContext.GLOBAL,
    ],
    KeybindingContext.SETTINGS: [KeybindingContext.GLOBAL],
    KeybindingContext.DIALOG: [KeybindingContext.GLOBAL],
}


@dataclass
class Keybinding:
    """Represents a single keybinding configuration.

    Attributes:
        key: The key or key combination (e.g., "a", "ctrl+s", "g,s")
        action: Action identifier (e.g., "add_download", "cycle_tabs")
        description: Human-readable description for help/hints
        context: Where this binding is active
        priority: Higher priority wins conflicts (default: 0)
        modes: Modes where binding is active (None = all modes)
    """

    key: str
    action: str
    description: str
    context: KeybindingContext
    priority: int = 0
    modes: list[KeybindingMode] | None = None

    def is_active_in_mode(self, mode: KeybindingMode) -> bool:
        """Check if this binding is active in the given mode."""
        if self.modes is None:
            # Available in all modes except EDIT (reserved for text input)
            return mode != KeybindingMode.EDIT
        return mode in self.modes


@dataclass
class KeybindingConflict:
    """Represents a detected keybinding conflict."""

    key: str
    context: KeybindingContext
    bindings: list[Keybinding] = field(default_factory=list)

    def __str__(self) -> str:
        """Format conflict for display."""
        binding_strs = [
            f"  - {b.action} (priority={b.priority}, modes={b.modes})" for b in self.bindings
        ]
        return f"Key '{self.key}' in {self.context.value}:\n" + "\n".join(binding_strs)


class KeybindingManager:
    """Central manager for all application keybindings.

    Provides context-aware keybinding resolution with mode filtering and
    conflict detection. Supports hierarchical contexts where child contexts
    can override parent context bindings.

    Usage:
        manager = KeybindingManager()

        # Register bindings
        manager.register(Keybinding("a", "add", "Add", MAIN_SCREEN))
        manager.register(Keybinding("d", "delete", "Delete", MAIN_SCREEN))

        # Set context and mode
        manager.set_context(KeybindingContext.MAIN_SCREEN)
        manager.set_mode(KeybindingMode.NORMAL)

        # Resolve key press
        result = manager.resolve("a")  # Returns ("add", MAIN_SCREEN)

        # Get hints for command bar
        hints = manager.get_hints_for_context(MAIN_SCREEN, NORMAL)
    """

    def __init__(self) -> None:
        """Initialize the keybinding manager."""
        # Registry: context → key → list of bindings
        self._bindings: dict[KeybindingContext, dict[str, list[Keybinding]]] = {
            context: {} for context in KeybindingContext
        }

        # Current state
        self._current_context = KeybindingContext.GLOBAL
        self._current_mode = KeybindingMode.NORMAL

        # Multi-key sequence tracking
        self._pending_sequence: list[str] = []

    @property
    def current_context(self) -> KeybindingContext:
        """Get the current context."""
        return self._current_context

    @property
    def current_mode(self) -> KeybindingMode:
        """Get the current mode."""
        return self._current_mode

    def register(self, binding: Keybinding) -> None:
        """Register a keybinding.

        Args:
            binding: The keybinding to register

        Note:
            Multiple bindings with same key/context are allowed for conflict
            detection. Resolution uses priority and mode filtering.
        """
        context_bindings = self._bindings[binding.context]
        if binding.key not in context_bindings:
            context_bindings[binding.key] = []
        context_bindings[binding.key].append(binding)

    def register_batch(self, bindings: list[Keybinding]) -> None:
        """Register multiple keybindings at once.

        Args:
            bindings: List of keybindings to register
        """
        for binding in bindings:
            self.register(binding)

    def set_context(self, context: KeybindingContext) -> None:
        """Set the current keybinding context.

        Args:
            context: The new context
        """
        self._current_context = context

    def set_mode(self, mode: KeybindingMode) -> None:
        """Set the current interaction mode.

        Args:
            mode: The new mode
        """
        self._current_mode = mode

    def resolve(
        self, key: str, context: KeybindingContext | None = None
    ) -> tuple[str, KeybindingContext] | None:
        """Resolve a key press to an action.

        Resolution order:
        1. Check current context (or provided context)
        2. Check parent contexts in hierarchy
        3. Filter by current mode
        4. Select highest priority binding

        Args:
            key: The key pressed
            context: Context to resolve in (defaults to current)

        Returns:
            Tuple of (action, context) if resolved, None otherwise
        """
        resolve_context = context or self._current_context
        contexts_to_check = [resolve_context] + CONTEXT_HIERARCHY[resolve_context]

        for ctx in contexts_to_check:
            bindings = self._bindings[ctx].get(key, [])
            if not bindings:
                continue

            # Filter by mode
            active_bindings = [b for b in bindings if b.is_active_in_mode(self._current_mode)]
            if not active_bindings:
                continue

            # Select highest priority
            best = max(active_bindings, key=lambda b: b.priority)
            return (best.action, ctx)

        return None

    def get_hints_for_context(
        self,
        context: KeybindingContext,
        mode: KeybindingMode | None = None,
        max_hints: int = 10,
    ) -> list[tuple[str, str]]:
        """Get keybinding hints for display in command bar.

        Args:
            context: Context to get hints for
            mode: Mode to filter by (defaults to current mode)
            max_hints: Maximum number of hints to return

        Returns:
            List of (key, description) tuples
        """
        use_mode = mode or self._current_mode
        hints: list[tuple[str, str, int]] = []  # (key, desc, priority)
        seen_keys: set[str] = set()

        # Collect from context hierarchy
        contexts_to_check = [context] + CONTEXT_HIERARCHY[context]
        for ctx in contexts_to_check:
            for key, bindings in self._bindings[ctx].items():
                if key in seen_keys:
                    continue

                # Find best binding for this key
                active = [b for b in bindings if b.is_active_in_mode(use_mode)]
                if not active:
                    continue

                best = max(active, key=lambda b: b.priority)
                hints.append((key, best.description, best.priority))
                seen_keys.add(key)

        # Sort by priority (desc) and take top N
        hints.sort(key=lambda h: h[2], reverse=True)
        return [(key, desc) for key, desc, _ in hints[:max_hints]]

    def detect_conflicts(self) -> list[KeybindingConflict]:
        """Detect keybinding conflicts within same context.

        A conflict occurs when multiple bindings for the same key in the same
        context have the same priority and overlapping modes.

        Returns:
            List of detected conflicts
        """
        conflicts: list[KeybindingConflict] = []

        for context, key_bindings in self._bindings.items():
            for key, bindings in key_bindings.items():
                if len(bindings) <= 1:
                    continue

                # Group by priority
                by_priority: dict[int, list[Keybinding]] = {}
                for binding in bindings:
                    if binding.priority not in by_priority:
                        by_priority[binding.priority] = []
                    by_priority[binding.priority].append(binding)

                # Check for conflicts at each priority level
                for _priority, group in by_priority.items():
                    if len(group) <= 1:
                        continue

                    # Check for mode overlap
                    for i, b1 in enumerate(group):
                        for b2 in group[i + 1 :]:
                            if self._modes_overlap(b1, b2):
                                conflict = KeybindingConflict(key, context)
                                conflict.bindings = group
                                conflicts.append(conflict)
                                break

        return conflicts

    def _modes_overlap(self, b1: Keybinding, b2: Keybinding) -> bool:
        """Check if two bindings have overlapping modes."""
        modes1 = set(b1.modes) if b1.modes else set(KeybindingMode)
        modes2 = set(b2.modes) if b2.modes else set(KeybindingMode)
        return bool(modes1 & modes2)

    def get_action_for_key(self, key: str, context: KeybindingContext | None = None) -> str | None:
        """Get action for a key (convenience method).

        Args:
            key: The key to look up
            context: Context to check (defaults to current)

        Returns:
            Action name if found, None otherwise
        """
        result = self.resolve(key, context)
        return result[0] if result else None

    def is_key_bound(self, key: str, context: KeybindingContext | None = None) -> bool:
        """Check if a key is bound in the given context.

        Args:
            key: The key to check
            context: Context to check (defaults to current)

        Returns:
            True if key is bound, False otherwise
        """
        return self.resolve(key, context) is not None
