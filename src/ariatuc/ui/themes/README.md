# ariatuc Theme System

This directory contains the theme system for ariatuc, providing centralized color management and support for multiple visual themes.

## Architecture

### Theme Interface

All themes must extend the `Theme` abstract base class from `base.py`:

```python
from ariatuc.ui.themes.base import Theme

class MyTheme(Theme):
    @property
    def name(self) -> str:
        return "My Theme Name"

    @property
    def colors(self) -> dict[str, str]:
        return {
            "primary": "#FF0000",
            "background": "#000000",
            # ... more colors
        }

    @property
    def component_overrides(self) -> str:
        return """
        /* Optional component-specific CSS */
        Tab.-active {
            color: $primary;
        }
        """
```

### Required Color Variables

Every theme must define these CSS variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `primary` | Main UI color (borders, titles) | `#bd93f9` |
| `accent` | Focus/highlight color | `#ff79c6` |
| `background` | Main background | `#282a36` |
| `surface` | Panel/surface background | `#44475a` |
| `panel` | Dialog background | `#282a36` |
| `text` | Primary text color | `#f8f8f2` |
| `text-muted` | Secondary text color | `#6272a4` |
| `success` | Success state (green) | `#50fa7b` |
| `error` | Error state (red) | `#ff5555` |
| `warning` | Warning state (orange) | `#ffb86c` |
| `info` | Info state (blue/cyan) | `#8be9fd` |
| `boost` | Focus/hover background | `#44475a` |
| `border` | Default border color | `#6272a4` |
| `border-focus` | Focus border color | `#bd93f9` |

### Optional Variables

Themes can define additional variables for fine-grained control:

- `primary-lighten-1`, `primary-darken-1`, etc. - Color variants
- `secondary` - Secondary highlight color
- `warning-muted` - Muted warning color
- Custom variables specific to the theme

## Current Themes

### Dracula (Default)

**File**: `dracula.py`

Dark theme based on the [Dracula color scheme](https://draculatheme.com), with integration of user-specified colors for optimal terminal visibility.

**Key Colors**:
- Primary: Purple `#bd93f9`
- Accent: Orange `#FEA62B` (user-specified)
- Background: Dark gray `#282a36`
- Success: Green `#50fa7b`

**Features**:
- High contrast for readability
- Color-coded status indicators
- Orange active tabs for visibility
- Pink table row selection

## Adding a New Theme

### Step 1: Create Theme File

Create a new file in this directory, e.g., `my_theme.py`:

```python
"""My custom theme for ariatuc."""

from ariatuc.ui.themes.base import Theme

class MyTheme(Theme):
    @property
    def name(self) -> str:
        return "My Theme"

    @property
    def colors(self) -> dict[str, str]:
        return {
            # Required colors
            "primary": "#3b82f6",
            "accent": "#f59e0b",
            "background": "#1f2937",
            "surface": "#374151",
            "panel": "#1f2937",
            "text": "#f9fafb",
            "text-muted": "#9ca3af",
            "success": "#10b981",
            "error": "#ef4444",
            "warning": "#f59e0b",
            "info": "#3b82f6",
            "boost": "#374151",
            "border": "#6b7280",
            "border-focus": "#3b82f6",
            # Additional custom colors
            "custom-color": "#123456",
        }

    @property
    def component_overrides(self) -> str:
        # Optional: Add theme-specific component styles
        return """
        /* My theme overrides */
        Tab.-active {
            color: $accent;
            text-style: bold;
        }
        """
```

### Step 2: Register Theme

Add your theme to `__init__.py`:

```python
from ariatuc.ui.themes.my_theme import MyTheme

# Create instance
MY_THEME = MyTheme()

# Optionally set as default
DEFAULT_THEME = MY_THEME

# Export
__all__ = [
    # ... existing exports
    "MyTheme",
    "MY_THEME",
]
```

### Step 3: Apply Theme

The theme is automatically applied through `ui/app.py`:

```python
from ariatuc.ui.themes import DEFAULT_THEME

class AriatucApp(App):
    CSS = DEFAULT_THEME.full_css + """
    /* Additional app-specific styles */
    """
```

## Theme Design Guidelines

### 1. Contrast and Readability

- Ensure text-to-background contrast ratio ≥ 4.5:1 (WCAG AA)
- Use `text` for primary content, `text-muted` for secondary
- Test theme in multiple terminal emulators

### 2. Color Semantics

- `success` → Green tones (active, completed)
- `error` → Red tones (failed, critical)
- `warning` → Orange/yellow (caution, paused)
- `info` → Blue/cyan (neutral information)

### 3. Interactive States

- `accent` → Focus, active tabs, selected items
- `border-focus` → Focused panel borders
- `boost` → Hover backgrounds, subtle highlights

### 4. Component Overrides

Use `component_overrides` for:
- Tab styling (active state colors)
- DataTable selection colors
- Button hover states
- Component-specific borders

Avoid overriding:
- Layout properties (padding, margin, width, height)
- Component structure
- Positioning

### 5. Testing Checklist

Test your theme with:
- [ ] Main screen (download list, status bar)
- [ ] Add Download dialog (all three tabs)
- [ ] Settings screens (app settings, aria2 settings)
- [ ] Server management screen
- [ ] Help screen
- [ ] All download states (active, paused, error, complete)
- [ ] Focus navigation (tab through components)
- [ ] Different terminal emulators (iTerm2, Terminal.app, etc.)

## Color Palette Tools

Useful tools for creating harmonious color palettes:

- [Dracula Theme](https://draculatheme.com) - Base for current default theme
- [Coolors](https://coolors.co) - Color palette generator
- [Adobe Color](https://color.adobe.com) - Advanced color wheel
- [Contrast Checker](https://webaim.org/resources/contrastchecker/) - WCAG compliance

## Future Enhancements

Planned improvements to the theme system:

- [ ] Runtime theme switching without restart
- [ ] Theme configuration persistence
- [ ] Light mode themes
- [ ] Theme preview in settings
- [ ] Custom theme editor
- [ ] Theme import/export

## Contributing

When contributing a new theme:

1. Follow the Theme interface exactly
2. Define all required color variables
3. Test thoroughly (see Testing Checklist)
4. Document any special features in the theme docstring
5. Add theme to `__init__.py` exports
6. Update this README with theme details

## License

Themes in this directory follow the same license as the ariatuc project.

The Dracula theme is based on the [Dracula color scheme](https://draculatheme.com) by Zeno Rocha, licensed under MIT.
