"""Base CSS styles for ariatuc - layout, sizing, and structure.

This module contains all CSS rules that are theme-independent:
- Layout rules (grid, flex)
- Sizing (height, width, padding, margin)
- Typography (text-align, text-style)
- Border styles (but NOT colors - those come from themes)

Color-specific rules use CSS variables ($primary, $accent, etc.)
which are defined by the active theme's ColorSystem.

This module also provides a DefaultTheme as the ultimate fallback when
no TOML theme files are available. This ensures the application can
always start, even if all theme configuration is deleted.
"""

from textual.design import ColorSystem

from ariatuc.ui.themes.base import Theme

# Default color system (Dracula colors) used as ultimate fallback
DEFAULT_COLOR_SYSTEM = ColorSystem(
    # Main colors - Dracula palette
    primary="#bd93f9",  # Purple
    secondary="#8be9fd",  # Cyan
    accent="#ff79c6",  # Pink
    foreground="#f8f8f2",  # White
    # Background colors
    background="#282a36",  # Dark background
    surface="#44475a",  # Slightly lighter surface
    panel="#282a36",  # Same as background
    boost="#44475a",  # Focus/hover background
    # Status colors
    success="#50fa7b",  # Green
    error="#ff5555",  # Red
    warning="#ffb86c",  # Orange
    # Appearance
    dark=True,
)

# Base CSS that applies to all themes
BASE_CSS = """
/* ===== GLOBAL FIX: Prevent layout shifts on focus ===== */
/* Remove outline, keep borders but ensure consistent width */
* {
    outline: none !important;
}

*:focus {
    outline: none !important;
}

/* Ensure containers don't change border on focus - they already have borders from parent styles */
DataTable:focus,
TabPane:focus,
TabPane:focus-within,
Container:focus,
Container:focus-within,
Vertical:focus,
Vertical:focus-within,
Horizontal:focus,
Horizontal:focus-within,
VerticalScroll:focus,
VerticalScroll:focus-within,
TabbedContent:focus,
TabbedContent:focus-within {
    outline: none !important;
}

/* ----- Tab Styling ----- */
/* Active tabs use accent (pink) for high visibility */
/* CRITICAL FIX: Prevent Tab layout shifts on interaction */
Tab {
    color: $text-muted;
    background: transparent !important;  /* No background color change */
    visibility: visible !important;
    display: block !important;
    opacity: 1 !important;
    border: none !important;
    outline: none !important;
}

Tab.-active {
    color: $accent;
    text-style: bold;
    background: transparent !important;  /* No background color change */
    visibility: visible !important;
    display: block !important;
    opacity: 1 !important;
    border: none !important;
    outline: none !important;
}

Tab.-active Label {
    color: $accent;
    background: transparent !important;
    visibility: visible !important;
    opacity: 1 !important;
}

Tab:hover {
    color: $foreground;
    background: transparent !important;  /* No background color change */
    visibility: visible !important;
    opacity: 1 !important;
    border: none !important;
    outline: none !important;
}

Tab:focus {
    color: $accent;
    background: transparent !important;  /* Remove blue background on click */
    visibility: visible !important;
    display: block !important;
    opacity: 1 !important;
    border: none !important;
    outline: none !important;
}

Tab:focus Label {
    color: $accent;
    background: transparent !important;
    visibility: visible !important;
    opacity: 1 !important;
}

Tab Label {
    background: transparent !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Tab underline colors */
Underline {
    color: $primary;
    visibility: visible;
}

Underline > .underline--bar {
    color: $accent;
    visibility: visible;
}

/* TabbedContent and TabPane */
TabbedContent {
    background: $background;
}

TabPane {
    background: $background;
}

/* ----- DataTable Styling ----- */
/* Use cyan for selected rows to stand out */
DataTable > .datatable--cursor {
    background: $secondary 20%;
    color: $foreground;
}

DataTable > .datatable--header {
    background: $surface;
    color: $foreground;
}

/* ----- Status Indicators ----- */
/* Color-coded download states */
.status-active {
    color: $success;
}

.status-paused {
    color: $warning;
}

.status-error {
    color: $error;
}

.status-complete {
    color: $primary;
}

.status-waiting {
    color: $secondary;  /* cyan */
}

/* ----- Button Variants ----- */
/* Ensure buttons follow theme palette */
Button.-primary {
    background: $primary;
    color: $background;
}

Button.-primary:hover {
    background: $primary 120%;  /* Lighten on hover */
}

Button:focus {
    border: solid $accent;
}

/* ----- Input Focus States ----- */
/* Note: Input styles are defined in Global Form Elements section below */

/* Select overlay - compact dropdown with clear visibility */
Select > SelectOverlay {
    border: solid $primary;
    background: $panel;
    max-height: 10;  /* Limit dropdown height to prevent off-screen */
}

Select > SelectOverlay > OptionList {
    background: $panel;
    border: none;
}

Select > SelectOverlay > OptionList > .option-list--option {
    height: 1;
    padding: 0 1;
}

Select > SelectOverlay > OptionList > .option-list--option-highlighted {
    background: $boost;
    color: $accent;
}

/* ----- Scrollbar Styling ----- */
/* Subtle scrollbars matching the theme */
ScrollBar {
    background: $background;
    color: $text-muted;
}

/* ----- Label Color Variants ----- */
/* Semantic label colors */
.label-accent {
    color: $accent;
    text-style: bold;
}

.label-muted {
    color: $text-muted;
}

.label-success {
    color: $success;
}

.label-error {
    color: $error;
}

.label-warning {
    color: $warning;
}

/* ===== FORM OPTIMIZATION: Unified Compact Spacing ===== */
/* Apply to all forms: AddDownloadDialog, FormWidget, Settings, etc. */

/* --- Global Form Elements --- */
/* Labels - single line, no extra spacing */
Label {
    height: 1;
    margin: 0;
    padding: 0;
}

/* ===== Input - Surge-style: compact height (2 lines) with bottom border ===== */
Input {
    height: 2;
    min-height: 2;
    margin: 0;
    padding: 0 1;
    border: none;
    border-bottom: solid $primary;  /* Purple underline */
    background: transparent;
    color: $foreground;
}

/* Input - Hover state (subtle indication) */
Input:hover {
    border-bottom: solid $secondary;  /* Cyan underline on hover */
}

/* Input - Focus state (clear indication) */
Input:focus {
    border-bottom: solid $accent;  /* Pink underline when focused */
    background: $boost;  /* Subtle background highlight */
}

/* Input - Disabled state (clear visual feedback) */
Input:disabled {
    border-bottom: solid $surface;  /* Gray underline */
    color: $text-muted;  /* Muted text color */
    opacity: 0.6;  /* Semi-transparent */
}

/* ===== Select - Same as Input ===== */
Select {
    height: 2;
    min-height: 2;
    margin: 0;
    padding: 0 1;
    border: none;
    border-bottom: solid $primary;  /* Purple underline */
    background: transparent;
    color: $foreground;
}

/* Select - Hover state */
Select:hover {
    border-bottom: solid $secondary;  /* Cyan underline on hover */
}

/* Select - Focus state */
Select:focus {
    border-bottom: solid $accent;  /* Pink underline when focused */
    background: $boost;  /* Subtle background highlight */
}

/* Select - Disabled state */
Select:disabled {
    border-bottom: solid $surface;  /* Gray underline */
    color: $text-muted;  /* Muted text color */
    opacity: 0.6;  /* Semi-transparent */
}

/* Select current value display - compact */
Select > SelectCurrent {
    border: none;
    background: transparent;
    padding: 0;
    height: 2;
}

/* Select arrow indicator - muted color */
Select > SelectCurrent > .select--arrow {
    color: $text-muted;
}

/* ===== TextArea - Multi-line needs more height ===== */
TextArea {
    height: 4;
    min-height: 4;
    margin: 0;
    padding: 0 1;
    border: none;
    border-bottom: solid $primary;  /* Purple underline */
    background: transparent;
    color: $foreground;
}

/* TextArea - Hover state */
TextArea:hover {
    border-bottom: solid $secondary;  /* Cyan underline on hover */
}

/* TextArea - Focus state */
TextArea:focus {
    border-bottom: solid $accent;  /* Pink underline when focused */
    background: $boost;  /* Subtle background highlight */
}

/* TextArea - Disabled state */
TextArea:disabled {
    border-bottom: solid $surface;  /* Gray underline */
    color: $text-muted;  /* Muted text color */
    opacity: 0.6;  /* Semi-transparent */
}

/* Buttons - reduce padding */
Button {
    min-width: 16;
    padding: 0 2;
}

/* Containers - no default padding */
Vertical {
    padding: 0;
}

Container {
    padding: 0;
}

/* Dialog containers - slight padding for breathing room */
ModalScreen > Vertical {
    padding: 1;
}

/* --- FormWidget Specific Optimization --- */
/* Form sections - reduce spacing between sections */
.form-section {
    margin-bottom: 1;  /* Reduced from 2 */
    padding: 1;
    border: solid $primary;
    width: 100%;
}

.form-section-header {
    padding: 0 1;
    margin-bottom: 0;  /* Reduced from 1 */
    height: 1;
    text-style: bold;
    background: $primary;
    color: $text;
}

/* Form fields - compact spacing between field groups */
.form-field {
    margin-top: 1;
    margin-bottom: 0;
    height: auto;
    width: 100%;
}

/* Form label - color only (spacing from theme) */
.form-label {
    color: $text;
}

/* Form field row - label and input in same line (horizontal layout) */
.form-field-row {
    width: 100%;
    height: 2;  /* Match Input height for proper alignment */
}

/* Form label in horizontal layout - fixed width for alignment */
.form-field-row > .form-label {
    width: 35;  /* Fixed width for consistent label column */
    height: 2;
    padding: 0 1;
    content-align: left middle;
}

/* Form input widgets in horizontal layout - fill remaining space */
.form-field-row > Input,
.form-field-row > Select,
.form-field-row > TextArea {
    width: 1fr;  /* Fill remaining space */
}

.form-field-row > Switch {
    width: auto;
}

/* Form help text - below the field row */
.form-help {
    margin: 0 0 0 1;  /* Small left margin to align with input */
    padding: 0;
    height: 1;
    color: $text-muted;
    text-style: italic;
}

.form-error {
    margin: 0 0 0 1;  /* Small left margin to align with input */
    padding: 0;
    height: 1;
    color: $error;
    text-style: bold;
}

/* Modified field indicator - reduce padding */
.form-field-modified {
    padding-left: 1;
    border-left: thick $accent;
}

/* ===== CHUNK MAP: Adaptive grid visualization ===== */
/* Surge-style chunk map with fixed-height grid */

ChunkMap {
    border: solid $surface;
    background: $background;
    padding: 1;
}

/* Chunk map title */
.chunk-map-title {
    color: $text;
    text-style: bold;
    margin-bottom: 1;
}

/* Visual blocks use Rich styles (see chunk_map.py) */
/* Colors:
 * - Complete: $success (green)
 * - Downloading: $accent (magenta/pink)
 * - Partial: $warning (yellow)
 * - Waiting: $text-muted (gray)
 */
"""


def get_base_css() -> str:
    """Get the base CSS styles.

    Returns:
        CSS string with all layout and sizing rules
    """
    return BASE_CSS


class DefaultTheme(Theme):
    """Default fallback theme using hardcoded Dracula colors.

    This theme is used as the ultimate fallback when:
    1. No TOML theme files exist in colors/ directory
    2. User deleted all themes from ~/.config/ariatuc/themes/
    3. TOML theme loading fails for any reason

    This ensures the application can always start with a usable theme,
    even if all configuration is missing or corrupted.

    The theme uses Dracula color palette for good visual contrast and
    widespread familiarity.
    """

    @property
    def name(self) -> str:
        """Theme display name.

        Returns:
            Theme name
        """
        return "Default (Dracula)"

    @property
    def color_system(self) -> ColorSystem:
        """Get default color system.

        Returns:
            Hardcoded ColorSystem with Dracula colors
        """
        return DEFAULT_COLOR_SYSTEM

    @property
    def component_overrides(self) -> str:
        """Get base CSS styles.

        Returns:
            Shared base CSS
        """
        return get_base_css()
