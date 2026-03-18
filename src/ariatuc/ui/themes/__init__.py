"""Theme system for ariatuc.

This module provides a centralized theme management system supporting
multiple color schemes. Themes can be:
1. Built-in TOML themes (src/ariatuc/ui/themes/colors/)
2. User custom themes (~/.config/ariatuc/themes/)

Architecture:
- Base CSS (layout, sizing) defined in base_styles.py
- Color schemes defined in TOML files
- Theme manager handles loading and fallback

Available Themes:
    - Dracula: Dark theme with purple/pink accent (default)
    - (More themes can be added as TOML files)

Usage:
    >>> from ariatuc.ui.themes import get_theme_manager, DEFAULT_THEME
    >>> manager = get_theme_manager()
    >>> print(manager.list_themes())
    ['dracula']
    >>> theme = manager.load_theme('dracula')
    >>> print(theme.name)
    'Dracula'
    >>> print(DEFAULT_THEME.name)
    'Dracula'
"""

from ariatuc.ui.themes.base import Theme
from ariatuc.ui.themes.manager import ThemeManager, get_theme_manager
from ariatuc.ui.themes.toml_theme import TOMLTheme

# Get theme manager and load default theme
_manager = get_theme_manager()

# Load default theme (Dracula from TOML, or DefaultTheme as fallback)
# get_default_theme() never raises - always returns a valid theme
DEFAULT_THEME = _manager.get_default_theme()

# Legacy alias for backward compatibility
DRACULA_THEME = DEFAULT_THEME

# Export public API
__all__ = [
    "Theme",
    "TOMLTheme",
    "ThemeManager",
    "get_theme_manager",
    "DEFAULT_THEME",
    "DRACULA_THEME",  # Legacy alias for DEFAULT_THEME
]
