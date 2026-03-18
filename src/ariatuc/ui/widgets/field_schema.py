"""Configuration field schema for form generation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class FieldType(Enum):
    """Form field types."""

    INPUT = "input"  # Single-line text input
    TEXTAREA = "textarea"  # Multi-line text
    SELECT = "select"  # Dropdown selection
    SWITCH = "switch"  # Boolean toggle
    NUMBER = "number"  # Numeric input


@dataclass
class ConfigField:
    """Configuration field schema for form generation.

    Attributes:
        key: Configuration key (e.g., 'dir', 'max-connection-per-server')
        label: Human-readable label for display
        type: Field type (INPUT, SELECT, SWITCH, etc.)
        default: Default value if none set
        required: Whether field is required
        editable: Whether field can be modified (False for read-only fields)
        options: List of (value, label) tuples for SELECT type
        placeholder: Placeholder text for input fields
        help_text: Description/help text displayed below field
        validation: Optional validation function (value) -> (bool, error_msg)
        section: Grouping section name (e.g., "Downloads", "Network")
        unit: Unit suffix (e.g., "KB/s", "seconds", "connections")
        min_value: Minimum value for numeric fields
        max_value: Maximum value for numeric fields
    """

    key: str
    label: str
    type: FieldType
    default: Any = None
    required: bool = False
    editable: bool = True
    options: list[tuple[Any, str]] | None = None
    placeholder: str | None = None
    help_text: str | None = None
    validation: Callable[[Any], tuple[bool, str]] | None = None
    section: str | None = None
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """Validate a value against this field's rules.

        Args:
            value: Value to validate

        Returns:
            (is_valid, error_message) tuple
        """
        # Required check
        if self.required and (value is None or value == ""):
            return False, f"{self.label} is required"

        # Type-specific validation
        if self.type == FieldType.NUMBER and value:
            try:
                num_val = float(value)
                if self.min_value is not None and num_val < self.min_value:
                    return False, f"{self.label} must be >= {self.min_value}"
                if self.max_value is not None and num_val > self.max_value:
                    return False, f"{self.label} must be <= {self.max_value}"
            except (ValueError, TypeError):
                return False, f"{self.label} must be a valid number"

        # Custom validation
        if self.validation:
            return self.validation(value)

        return True, ""
