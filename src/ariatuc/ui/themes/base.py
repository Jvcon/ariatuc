"""Base theme class for ariatuc.

This module defines the abstract interface that all themes must implement.
Themes provide color palettes using Textual's ColorSystem.
"""

from abc import ABC, abstractmethod

from textual.design import ColorSystem


class Theme(ABC):
    """Abstract base class for ariatuc themes.

    A theme provides:
    1. Color system configuration via Textual's ColorSystem
    2. Optional component-specific CSS overrides

    Example:
        >>> class MyTheme(Theme):
        ...     @property
        ...     def name(self) -> str:
        ...         return "My Theme"
        ...
        ...     @property
        ...     def color_system(self) -> ColorSystem:
        ...         return ColorSystem(
        ...             primary="#FF0000",
        ...             background="#000000",
        ...             # ... more colors
        ...         )
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Theme display name.

        Returns:
            Human-readable theme name (e.g., "Dracula", "Solarized Dark")
        """
        pass

    @property
    @abstractmethod
    def color_system(self) -> ColorSystem:
        """Color system configuration.

        Returns:
            Textual ColorSystem instance with all theme colors defined.
            Required colors:
                - primary: Primary color (main borders, titles)
                - accent: Accent color (focus, highlights)
                - background: Main background color
                - surface: Surface/panel background
                - success: Success state color (green)
                - error: Error state color (red)
                - warning: Warning state color (orange/yellow)

        Example:
            ColorSystem(
                primary="#bd93f9",
                accent="#ff79c6",
                background="#282a36",
                surface="#44475a",
                # ...
            )
        """
        pass

    @property
    def component_overrides(self) -> str:
        """Optional component-specific CSS overrides.

        Override this property to provide theme-specific styling for
        individual components (Tabs, Buttons, etc.) that need more than
        just color variables.

        Returns:
            CSS string with component overrides, or empty string if none.
        """
        return ""
