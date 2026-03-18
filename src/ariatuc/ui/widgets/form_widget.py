"""Unified form widget with validation, change tracking, and grouping."""

from __future__ import annotations

import logging
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Input, Label, Select, Static, Switch, TextArea

from ariatuc.ui.widgets.field_schema import ConfigField, FieldType

logger = logging.getLogger(__name__)


class FormWidget(VerticalScroll):
    """Unified form widget with validation, change tracking, and grouping.

    Features:
    - Schema-driven field generation from ConfigField definitions
    - Real-time validation with error display
    - Change tracking (modified fields highlighted)
    - Field grouping by section
    - Vertical scrolling with scrollbar support
    - Help text display
    - Reset to original values
    - Get changed values only

    CSS Classes:
    - form-widget: Main container
    - form-section: Section grouping
    - form-section-header: Section title
    - form-field: Individual field container
    - form-label: Field label
    - form-help: Help text
    - form-error: Validation error
    - form-field-modified: Modified field indicator
    """

    DEFAULT_CSS = """
    FormWidget {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    FormWidget > Vertical {
        width: 100%;
        height: auto;
    }

    /* Form section - border and width only (spacing from theme) */
    .form-section {
        border: solid $primary;
        width: 100%;
    }

    /* Form section header - styling only (spacing from theme) */
    .form-section-header {
        text-style: bold;
        background: $primary;
        color: $text;
    }

    /* Form field - width only (spacing from theme) */
    .form-field {
        width: 100%;
    }

    /* Form label - color only (spacing from theme) */
    .form-label {
        color: $text;
    }

    /* Form help - color and style only (spacing from theme) */
    .form-help {
        color: $text-muted;
        text-style: italic;
    }

    /* Form error - color and style only (spacing from theme) */
    .form-error {
        color: $error;
        text-style: bold;
    }

    /* Modified field indicator - border only (spacing from theme) */
    .form-field-modified {
        border-left: thick $accent;
    }

    /* ===== VIEW MODE: Navigation highlighting (j/k keys) ===== */

    /* Highlighted field - editable */
    FormWidget Input.view-highlighted,
    FormWidget Select.view-highlighted,
    FormWidget TextArea.view-highlighted {
        border: none;
        border-bottom: solid $accent;  /* Pink underline */
        background: $boost;  /* Subtle background */
        color: $foreground;
    }

    /* Highlighted field - disabled/read-only (clear distinction) */
    FormWidget Input.view-highlighted:disabled,
    FormWidget Select.view-highlighted:disabled,
    FormWidget TextArea.view-highlighted:disabled {
        border: none;
        border-bottom: solid $surface;  /* Gray underline for disabled */
        background: $surface-darken-1;  /* Darker background */
        color: $text-muted;  /* Muted text */
        opacity: 0.7;  /* More transparent */
    }

    /* ===== EDIT MODE: Focus and interaction ===== */

    /* Focused field (active editing) */
    FormWidget Input:focus,
    FormWidget Select:focus,
    FormWidget TextArea:focus {
        border: none;
        border-bottom: solid $success;  /* Green underline when editing */
        background: $panel;  /* Clear background */
        color: $foreground;
    }

    /* Hover state (subtle feedback before focus) */
    FormWidget Input:hover,
    FormWidget Select:hover,
    FormWidget TextArea:hover {
        border-bottom: solid $secondary;  /* Cyan underline on hover */
    }

    /* Disabled state (no interaction) */
    FormWidget Input:disabled,
    FormWidget Select:disabled,
    FormWidget TextArea:disabled {
        border-bottom: solid $surface;  /* Gray underline */
        color: $text-muted;  /* Muted text */
        opacity: 0.6;
    }

    /* ===== VALIDATION: Error states ===== */

    /* Invalid field (validation failed) */
    FormWidget Input.invalid,
    FormWidget Select.invalid,
    FormWidget TextArea.invalid {
        border: none;
        border-bottom: solid $error;  /* Red underline for errors */
        background: $error 10%;  /* Light red background */
        color: $foreground;
    }

    /* Invalid field when focused (editing with error) */
    FormWidget Input.invalid:focus,
    FormWidget Select.invalid:focus,
    FormWidget TextArea.invalid:focus {
        border: none;
        border-bottom: solid $error;  /* Keep red underline */
        background: $error 20%;  /* Slightly stronger red background */
        color: $foreground;
    }

    /* ===== SWITCH: Special handling ===== */

    /* Switch in VIEW mode */
    FormWidget Switch.view-highlighted {
        border: none;
        border-bottom: solid $accent;  /* Pink underline */
        background: $boost;
    }

    /* Switch disabled state */
    FormWidget Switch:disabled {
        opacity: 0.5;
        color: $text-muted;
    }

    /* Default styles */
    FormWidget Input, FormWidget Select, FormWidget TextArea {
        width: 100%;
    }

    FormWidget Switch {
        width: auto;
    }
    """

    def __init__(
        self,
        fields: list[ConfigField],
        initial_values: dict[str, Any] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize form widget.

        Args:
            fields: List of ConfigField definitions
            initial_values: Initial field values (key -> value)
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.fields = fields
        self.initial_values = initial_values or {}
        self.current_values: dict[str, Any] = {}
        self.field_widgets: dict[str, Widget] = {}
        self.error_labels: dict[str, Label] = {}
        self.modified_fields: set[str] = set()

    def compose(self) -> ComposeResult:
        """Compose form fields grouped by section."""
        logger.info(f"FormWidget.compose() called with {len(self.fields)} fields")

        # Group fields by section
        sections: dict[str | None, list[ConfigField]] = {}
        for field in self.fields:
            section = field.section
            if section not in sections:
                sections[section] = []
            sections[section].append(field)

        logger.info(f"Grouped fields into {len(sections)} sections: {list(sections.keys())}")

        # Render sections
        for section_name, section_fields in sections.items():
            logger.info(f"Rendering section '{section_name}' with {len(section_fields)} fields")
            with Vertical(classes="form-section"):
                if section_name:
                    yield Static(section_name, classes="form-section-header")

                for field in section_fields:
                    yield from self._compose_field(field)

        logger.info("FormWidget.compose() completed")

    def _compose_field(self, field: ConfigField) -> ComposeResult:
        """Compose a single form field.

        Args:
            field: Field configuration

        Yields:
            Widgets for this field
        """
        with Vertical(classes="form-field"):
            # Label and input on same line (horizontal layout)
            with Horizontal(classes="form-field-row"):
                # Label
                label_text = field.label
                if field.required:
                    label_text += " *"
                if field.unit:
                    label_text += f" ({field.unit})"
                if not field.editable:
                    label_text += " [Read-only]"
                yield Label(label_text, classes="form-label")

                # Input widget based on field type
                initial_value = self.initial_values.get(field.key, field.default)
                self.current_values[field.key] = initial_value

                # Debug logging for value types
                if initial_value is not None:
                    logger.debug(
                        f"Field '{field.key}': value={repr(initial_value)}, type={type(initial_value).__name__}"
                    )

                widget: Widget
                if field.type == FieldType.INPUT:
                    widget = Input(
                        value=str(initial_value) if initial_value else "",
                        placeholder=field.placeholder or "",
                        id=f"field-{field.key}",
                        disabled=not field.editable,
                    )
                    self.field_widgets[field.key] = widget
                    yield widget

                elif field.type == FieldType.TEXTAREA:
                    widget = TextArea(
                        text=str(initial_value) if initial_value else "",
                        id=f"field-{field.key}",
                        disabled=not field.editable,
                    )
                    self.field_widgets[field.key] = widget
                    yield widget

                elif field.type == FieldType.SELECT:
                    options = field.options or []
                    # Convert boolean values to string for Select compatibility
                    select_value = initial_value
                    if isinstance(initial_value, bool):
                        select_value = str(initial_value).lower()
                    # Ensure value is in options, otherwise use first option or Select.BLANK
                    option_values = [value for value, _ in options]
                    if select_value not in option_values:
                        select_value = option_values[0] if option_values else Select.BLANK
                    widget = Select(
                        options=[(label, value) for value, label in options],
                        value=select_value,
                        id=f"field-{field.key}",
                        disabled=not field.editable,
                    )
                    self.field_widgets[field.key] = widget
                    yield widget

                elif field.type == FieldType.SWITCH:
                    # aria2rpc now returns proper Python bool, just use it directly
                    bool_value = bool(initial_value) if initial_value is not None else False
                    widget = Switch(
                        value=bool_value,
                        id=f"field-{field.key}",
                        disabled=not field.editable,
                    )
                    self.field_widgets[field.key] = widget
                    yield widget

                elif field.type == FieldType.NUMBER:
                    # aria2 returns numbers as strings, convert for display
                    display_value = str(initial_value) if initial_value not in (None, "") else ""
                    widget = Input(
                        value=display_value,
                        placeholder=field.placeholder or "0",
                        id=f"field-{field.key}",
                        type="number",
                        disabled=not field.editable,
                    )
                    self.field_widgets[field.key] = widget
                    yield widget

            # Help text (on separate line below)
            if field.help_text:
                yield Label(field.help_text, classes="form-help")

            # Error label (initially hidden)
            error_label = Label("", classes="form-error")
            error_label.display = False
            self.error_labels[field.key] = error_label
            yield error_label

    def on_mount(self) -> None:
        """Set up event handlers after mount."""
        # Watch for changes in all input fields
        for key, widget in self.field_widgets.items():
            if isinstance(widget, (Input, Switch, Select)):
                widget.watch(widget, "value", self._create_value_watcher(key), init=False)
            elif isinstance(widget, TextArea):
                widget.watch(widget, "text", self._create_text_watcher(key), init=False)

    def _create_value_watcher(self, field_key: str):
        """Create a watcher function for value changes.

        Args:
            field_key: Field key to watch

        Returns:
            Watcher callback function
        """

        def watcher(new_value: Any) -> None:
            self._on_field_changed(field_key, new_value)

        return watcher

    def _create_text_watcher(self, field_key: str):
        """Create a watcher function for text changes (TextArea).

        Args:
            field_key: Field key to watch

        Returns:
            Watcher callback function
        """

        def watcher(new_text: str) -> None:
            self._on_field_changed(field_key, new_text)

        return watcher

    def _on_field_changed(self, field_key: str, new_value: Any) -> None:
        """Handle field value change.

        Args:
            field_key: Field key that changed
            new_value: New field value
        """
        # Update current value
        self.current_values[field_key] = new_value

        # Track if modified from initial
        initial = self.initial_values.get(field_key)
        if new_value != initial:
            self.modified_fields.add(field_key)
            # Add visual indicator
            widget = self.field_widgets.get(field_key)
            if widget and hasattr(widget, "add_class"):
                widget.add_class("form-field-modified")
        else:
            self.modified_fields.discard(field_key)
            widget = self.field_widgets.get(field_key)
            if widget and hasattr(widget, "remove_class"):
                widget.remove_class("form-field-modified")

        # Validate field
        field = next((f for f in self.fields if f.key == field_key), None)
        if field:
            is_valid, error_msg = field.validate_value(new_value)
            error_label = self.error_labels.get(field_key)
            widget = self.field_widgets.get(field_key)

            if error_label:
                if is_valid:
                    error_label.display = False
                    # Remove invalid CSS class
                    if widget and hasattr(widget, "remove_class"):
                        widget.remove_class("invalid")
                else:
                    error_label.update(error_msg)
                    error_label.display = True
                    # Add invalid CSS class
                    if widget and hasattr(widget, "add_class"):
                        widget.add_class("invalid")

    def validate_all(self) -> tuple[bool, dict[str, str]]:
        """Validate all fields.

        Returns:
            (all_valid, errors_dict) where errors_dict maps field_key -> error_message
        """
        errors = {}
        for field in self.fields:
            value = self.current_values.get(field.key)
            is_valid, error_msg = field.validate_value(value)
            widget = self.field_widgets.get(field.key)
            error_label = self.error_labels.get(field.key)

            if not is_valid:
                errors[field.key] = error_msg
                # Show error in UI
                if error_label:
                    error_label.update(error_msg)
                    error_label.display = True
                # Add invalid CSS class
                if widget and hasattr(widget, "add_class"):
                    widget.add_class("invalid")
            else:
                # Clear error
                if error_label:
                    error_label.display = False
                # Remove invalid CSS class
                if widget and hasattr(widget, "remove_class"):
                    widget.remove_class("invalid")

        return len(errors) == 0, errors

    def get_values(self) -> dict[str, Any]:
        """Get all current field values.

        Returns:
            Dictionary mapping field keys to current values
        """
        return self.current_values.copy()

    def get_changed_values(self) -> dict[str, Any]:
        """Get only modified field values (excluding read-only fields).

        Returns:
            Dictionary mapping field keys to new values (only modified and editable fields)
        """
        # Create a map of field key -> field for quick lookup
        field_map = {f.key: f for f in self.fields}

        # Return only modified fields that are editable
        return {
            key: self.current_values[key]
            for key in self.modified_fields
            if field_map.get(key, ConfigField(key="", label="", type=FieldType.INPUT)).editable
        }

    def reset(self) -> None:
        """Reset all fields to initial values."""
        for key, widget in self.field_widgets.items():
            initial = self.initial_values.get(key)
            if isinstance(widget, Input):
                widget.value = str(initial) if initial else ""
            elif isinstance(widget, TextArea):
                widget.text = str(initial) if initial else ""
            elif isinstance(widget, Switch):
                # aria2rpc returns proper Python bool
                widget.value = bool(initial) if initial is not None else False
            elif isinstance(widget, Select):
                widget.value = initial

        self.current_values = self.initial_values.copy()
        self.modified_fields.clear()

        # Clear visual indicators and errors
        for widget in self.field_widgets.values():
            if hasattr(widget, "remove_class"):
                widget.remove_class("form-field-modified")
        for error_label in self.error_labels.values():
            error_label.display = False

    def has_changes(self) -> bool:
        """Check if any fields have been modified.

        Returns:
            True if there are unsaved changes
        """
        return len(self.modified_fields) > 0

    def highlight_field(self, field_key: str) -> None:
        """Highlight a field in VIEW mode (for j/k navigation).

        Args:
            field_key: Field key to highlight
        """
        # First clear all highlights
        self.clear_highlight()

        # Highlight the specified field
        widget = self.field_widgets.get(field_key)
        if widget and hasattr(widget, "add_class"):
            widget.add_class("view-highlighted")
            # Scroll to make it visible
            if hasattr(widget, "scroll_visible"):
                widget.scroll_visible()

    def clear_highlight(self) -> None:
        """Clear all VIEW mode highlights from fields."""
        for widget in self.field_widgets.values():
            if hasattr(widget, "remove_class"):
                widget.remove_class("view-highlighted")

    def get_field_keys(self) -> list[str]:
        """Get ordered list of field keys.

        Returns:
            List of field keys in order they were defined
        """
        return [field.key for field in self.fields]
