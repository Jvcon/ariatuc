"""TOML-based theme loader for ariatuc.

This module implements dynamic theme loading from TOML configuration files.
Themes can be loaded from:
1. Built-in themes (packaged with the application)
2. User themes (~/.config/ariatuc/themes/)
"""

import logging
import tomllib  # Python 3.11+ standard library
from pathlib import Path
from typing import Any

from textual.design import ColorSystem

from ariatuc.ui.themes.base import Theme
from ariatuc.ui.themes.base_styles import get_base_css

logger = logging.getLogger(__name__)


class TOMLTheme(Theme):
    """Theme loaded from TOML configuration file.

    TOML format:
        [metadata]
        name = "Theme Name"
        description = "Theme description"
        dark = true

        [colors]
        primary = "#RRGGBB"
        accent = "#RRGGBB"
        # ... (required ColorSystem colors)

        [extra_colors]
        custom_color = "#RRGGBB"
        # ... (theme-specific extra colors)
    """

    def __init__(self, toml_path: Path) -> None:
        """Initialize theme from TOML file.

        Args:
            toml_path: Path to TOML configuration file

        Raises:
            FileNotFoundError: If TOML file doesn't exist
            ValueError: If TOML file is invalid or missing required fields
        """
        self.toml_path = toml_path
        self._config = self._load_toml(toml_path)
        self._validate_config()

    def _load_toml(self, path: Path) -> dict[str, Any]:
        """Load and parse TOML file.

        Args:
            path: Path to TOML file

        Returns:
            Parsed TOML configuration

        Raises:
            FileNotFoundError: If file doesn't exist
            tomllib.TOMLDecodeError: If TOML is invalid
        """
        if not path.exists():
            msg = f"Theme file not found: {path}"
            raise FileNotFoundError(msg)

        with open(path, "rb") as f:
            return tomllib.load(f)

    def _validate_config(self) -> None:
        """Validate TOML configuration has required fields.

        Raises:
            ValueError: If required fields are missing
        """
        # Check for required sections
        if "metadata" not in self._config:
            msg = f"Missing [metadata] section in {self.toml_path}"
            raise ValueError(msg)

        if "colors" not in self._config:
            msg = f"Missing [colors] section in {self.toml_path}"
            raise ValueError(msg)

        # Check for required metadata fields
        metadata = self._config["metadata"]
        if "name" not in metadata:
            msg = f"Missing 'name' in [metadata] section: {self.toml_path}"
            raise ValueError(msg)

        # Check for required color fields (ColorSystem requirements)
        colors = self._config["colors"]
        required_colors = [
            "primary",
            "accent",
            "background",
            "surface",
            "success",
            "error",
            "warning",
        ]

        missing = [color for color in required_colors if color not in colors]
        if missing:
            msg = f"Missing required colors in {self.toml_path}: {', '.join(missing)}"
            raise ValueError(msg)

    @property
    def name(self) -> str:
        """Theme display name from TOML metadata.

        Returns:
            Theme name
        """
        return self._config["metadata"]["name"]

    @property
    def description(self) -> str:
        """Theme description from TOML metadata.

        Returns:
            Theme description (or empty string if not provided)
        """
        return self._config["metadata"].get("description", "")

    @property
    def is_dark(self) -> bool:
        """Check if theme is dark.

        Returns:
            True if dark theme
        """
        return self._config["metadata"].get("dark", True)

    @property
    def color_system(self) -> ColorSystem:
        """Build ColorSystem from TOML colors.

        Returns:
            Textual ColorSystem instance
        """
        colors = self._config["colors"]

        # Build ColorSystem with required colors
        return ColorSystem(
            primary=colors["primary"],
            secondary=colors.get("secondary", colors["primary"]),
            accent=colors["accent"],
            foreground=colors.get("foreground", "#FFFFFF"),
            background=colors["background"],
            surface=colors["surface"],
            panel=colors.get("panel", colors["surface"]),
            boost=colors.get("boost", colors["surface"]),
            success=colors["success"],
            error=colors["error"],
            warning=colors["warning"],
            dark=self.is_dark,
        )

    @property
    def component_overrides(self) -> str:
        """Get base CSS styles (layout, sizing).

        Returns:
            Base CSS string from base_styles.py
        """
        # Return the base CSS which uses color variables
        return get_base_css()

    @property
    def extra_colors(self) -> dict[str, str]:
        """Get theme-specific extra colors.

        Returns:
            Dictionary of extra color definitions (or empty dict)
        """
        return self._config.get("extra_colors", {})


def load_toml_theme(toml_path: Path) -> TOMLTheme:
    """Load a theme from TOML file.

    Args:
        toml_path: Path to TOML theme file

    Returns:
        Loaded TOMLTheme instance

    Raises:
        FileNotFoundError: If theme file doesn't exist
        ValueError: If theme file is invalid
    """
    return TOMLTheme(toml_path)
