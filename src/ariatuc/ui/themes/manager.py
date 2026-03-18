"""Theme manager for ariatuc.

Handles theme loading from multiple sources:
1. Built-in themes (src/ariatuc/ui/themes/colors/)
2. User themes (~/.config/ariatuc/themes/)

Provides:
- Theme discovery and listing
- Theme loading with fallback
- Default theme restoration
- User config directory management
"""

import logging
import shutil
from pathlib import Path
from typing import Any

from ariatuc.ui.themes.base import Theme
from ariatuc.ui.themes.toml_theme import load_toml_theme

logger = logging.getLogger(__name__)


class ThemeManager:
    """Manage theme loading and configuration."""

    def __init__(self, user_config_dir: Path | None = None) -> None:
        """Initialize theme manager.

        Args:
            user_config_dir: User config directory path
                           (defaults to ~/.config/ariatuc/themes)
        """
        # Determine user config directory
        if user_config_dir is None:
            # Use XDG_CONFIG_HOME if available, otherwise ~/.config
            import os

            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config:
                base_dir = Path(xdg_config) / "ariatuc"
            else:
                base_dir = Path.home() / ".config" / "ariatuc"

            self.user_themes_dir = base_dir / "themes"
        else:
            self.user_themes_dir = user_config_dir

        # Built-in themes directory (relative to this file)
        self.builtin_themes_dir = Path(__file__).parent / "colors"

        # Cache for loaded themes
        self._theme_cache: dict[str, Theme] = {}

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create user themes directory if it doesn't exist.

        Also copies default themes if user directory is empty.
        """
        # Create user themes directory
        if not self.user_themes_dir.exists():
            logger.info(f"Creating user themes directory: {self.user_themes_dir}")
            self.user_themes_dir.mkdir(parents=True, exist_ok=True)

            # Copy default themes on first run
            self._copy_default_themes()
        else:
            # Check if empty and restore defaults
            user_themes = list(self.user_themes_dir.glob("*.toml"))
            if not user_themes:
                logger.info("User themes directory empty, restoring defaults")
                self._copy_default_themes()

    def _copy_default_themes(self) -> None:
        """Copy built-in themes to user directory.

        This allows users to customize default themes.
        """
        if not self.builtin_themes_dir.exists():
            logger.warning(f"Built-in themes directory not found: {self.builtin_themes_dir}")
            return

        # Copy all .toml files
        for theme_file in self.builtin_themes_dir.glob("*.toml"):
            dest = self.user_themes_dir / theme_file.name
            if not dest.exists():
                logger.info(f"Copying default theme: {theme_file.name}")
                shutil.copy2(theme_file, dest)

    def list_themes(self) -> list[str]:
        """List available theme names.

        Returns:
            List of theme names (without .toml extension)
        """
        themes = set()

        # Add built-in themes
        if self.builtin_themes_dir.exists():
            for theme_file in self.builtin_themes_dir.glob("*.toml"):
                themes.add(theme_file.stem)

        # Add user themes (may override built-in)
        if self.user_themes_dir.exists():
            for theme_file in self.user_themes_dir.glob("*.toml"):
                themes.add(theme_file.stem)

        return sorted(themes)

    def load_theme(self, theme_name: str) -> Theme:
        """Load a theme by name.

        Search order:
        1. User themes directory
        2. Built-in themes directory

        Args:
            theme_name: Theme name (without .toml extension)

        Returns:
            Loaded Theme instance

        Raises:
            FileNotFoundError: If theme not found
            ValueError: If theme file is invalid
        """
        # Check cache first
        if theme_name in self._theme_cache:
            return self._theme_cache[theme_name]

        # Try user themes first
        user_theme_path = self.user_themes_dir / f"{theme_name}.toml"
        if user_theme_path.exists():
            logger.info(f"Loading user theme: {theme_name}")
            theme = load_toml_theme(user_theme_path)
            self._theme_cache[theme_name] = theme
            return theme

        # Try built-in themes
        builtin_theme_path = self.builtin_themes_dir / f"{theme_name}.toml"
        if builtin_theme_path.exists():
            logger.info(f"Loading built-in theme: {theme_name}")
            theme = load_toml_theme(builtin_theme_path)
            self._theme_cache[theme_name] = theme
            return theme

        # Theme not found
        msg = f"Theme not found: {theme_name}"
        raise FileNotFoundError(msg)

    def get_default_theme(self) -> Theme:
        """Get the default theme (Dracula).

        Returns:
            Default Theme instance

        Raises:
            None - Always returns a valid theme (fallback to DefaultTheme if needed)
        """
        try:
            return self.load_theme("dracula")
        except (FileNotFoundError, ValueError) as e:
            logger.warning(
                f"Failed to load dracula theme: {e}. Using hardcoded DefaultTheme as fallback."
            )
            # Last resort fallback - use hardcoded default theme from base_styles
            from ariatuc.ui.themes.base_styles import DefaultTheme

            return DefaultTheme()

    def restore_defaults(self) -> None:
        """Restore default themes to user directory.

        Overwrites any existing user themes.
        """
        logger.info("Restoring default themes")
        self._copy_default_themes()
        # Clear cache to reload themes
        self._theme_cache.clear()

    def get_theme_info(self, theme_name: str) -> dict[str, Any]:
        """Get metadata about a theme without fully loading it.

        Args:
            theme_name: Theme name

        Returns:
            Dictionary with theme metadata

        Raises:
            FileNotFoundError: If theme not found
        """
        theme = self.load_theme(theme_name)

        info: dict[str, Any] = {
            "name": theme.name,
        }

        # Add extra info if available (from TOMLTheme)
        if hasattr(theme, "description"):
            info["description"] = theme.description
        if hasattr(theme, "is_dark"):
            info["is_dark"] = theme.is_dark

        return info


# Global theme manager instance
_theme_manager: ThemeManager | None = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance.

    Returns:
        ThemeManager instance
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
