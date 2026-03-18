---
date: 2026-01-13
feature: "VIEW/EDIT Mode Interaction in Server Management Screen"
files:
  - src/ariatuc/ui/screens/server_management_screen.py
---

# VIEW/EDIT Mode Interaction Design

## Overview

The Server Management Screen implements a dual-mode interaction pattern inspired by Vim:
- **VIEW Mode**: Navigation and browsing (default)
- **EDIT Mode**: Form field editing

This document describes the design, implementation, and key fixes.

## Interaction Modes

### VIEW Mode (Default State)

**Characteristics:**
- No form field is focused
- Global keyboard shortcuts are active
- User can navigate without accidentally modifying data

**Available Actions:**
- `t` / `T`: Cycle through servers (next/previous)
- `j` / `k`: Navigate form fields (visual highlight only, no focus)
- `i`: Enter EDIT mode (focus first editable field)
- `a`: Add new server
- `d`: Delete selected server
- `w`: Save current server configuration
- `Space`: Set server as current and switch connection
- `Enter`: Test connection
- `Esc`: Close the server management screen
- `q`: Quit and close screen

### EDIT Mode (Form Field Focused)

**Characteristics:**
- An Input, Select, or TextArea widget is focused
- User can type and modify field values
- Global navigation keys are disabled (to avoid conflicts)

**Available Actions:**
- Typing: Modify field content
- `Tab`: Navigate between form fields (standard Textual behavior)
- `Esc`: Exit EDIT mode and return to VIEW mode
- `Enter` (in Input): Submit and move to next field (standard behavior)

**Disabled in EDIT Mode:**
- `t` / `T`: Server cycling (would interfere with typing)
- `j` / `k`: Field navigation (Tab is used instead)
- Other global shortcuts

## Mode Transitions

### Entering EDIT Mode

**Methods:**

1. **Explicit Entry (`i` key):**
   ```python
   def action_enter_edit_mode(self) -> None:
       # Focus on the first editable field
       for field_widget in self._form_widget.field_widgets.values():
           if hasattr(field_widget, "focus") and not field_widget.disabled:
               field_widget.focus()
               self._mode = "EDIT"
               break
   ```

2. **Automatic Detection:**
   ```python
   def on_key(self, event) -> None:
       focused = self.app.focused
       in_edit_mode = isinstance(focused, (Input, TextArea, Select))

       if in_edit_mode and self._mode == "VIEW":
           self._mode = "EDIT"  # Auto-enter EDIT mode
   ```

### Exiting EDIT Mode

**Methods:**

1. **Explicit Exit (`Esc` key in on_key()):**
   ```python
   if self._mode == "EDIT":
       if key == "escape":
           self.set_focus(None)  # Blur the focused field
           self._mode = "VIEW"
           event.stop()  # CRITICAL: Stop event propagation completely
           return
   ```

   **Why `event.stop()` is Critical:**
   - `event.prevent_default()` only prevents default behavior but still allows action bindings to trigger
   - `event.stop()` completely stops event propagation, preventing `action_handle_escape()` from being called
   - Without `.stop()`, both `on_key()` and `action_handle_escape()` would execute, causing the screen to close immediately

2. **Fallback in action_handle_escape():**
   ```python
   def action_handle_escape(self) -> None:
       # Real-time detection (doesn't rely on _mode state)
       focused = self.app.focused
       in_edit_mode = isinstance(focused, (Input, TextArea, Select))

       if in_edit_mode:
           self.set_focus(None)
           self._mode = "VIEW"
       else:
           self.dismiss(None)  # Close screen only in VIEW mode
   ```

   This provides a safety net in case `on_key()` doesn't catch the event.

3. **Automatic Detection (focus lost):**
   ```python
   def on_key(self, event) -> None:
       focused = self.app.focused
       in_edit_mode = isinstance(focused, (Input, TextArea, Select))

       if not in_edit_mode and self._mode == "EDIT":
           self._mode = "VIEW"  # Auto-exit EDIT mode
   ```

## Event Handling Architecture

### Event Flow Diagram

```
User presses Esc
       ↓
┌─────────────────┐
│   on_key()      │  (First handler)
│                 │
│ Check if EDIT?  │
│   Yes → Blur    │
│       → Set VIEW│
│       → STOP    │  ← Prevents action_handle_escape()
└─────────────────┘
       ↓
   (stopped)
```

**If on_key() doesn't stop the event:**

```
User presses Esc
       ↓
┌─────────────────┐
│   on_key()      │
│ (doesn't stop)  │
└─────────────────┘
       ↓
┌─────────────────────┐
│ action_handle_escape│  (Fallback)
│                     │
│ Real-time detect:   │
│   Focused field?    │
│   Yes → Exit EDIT   │
│   No → Close screen │
└─────────────────────┘
```

## Key Implementation Details

### 1. Mode State Tracking

```python
self._mode = "VIEW"  # or "EDIT"
```

- **Purpose**: Track current interaction mode
- **Updated**: Automatically in `on_key()` based on focus state
- **Used for**: Enabling/disabling different key handlers

### 2. Real-Time Focus Detection

```python
focused = self.app.focused
in_edit_mode = isinstance(focused, (Input, TextArea, Select))
```

- **Purpose**: Determine if user is currently editing a form field
- **Advantage**: More reliable than relying solely on `_mode` state
- **Used in**: Both `on_key()` and `action_handle_escape()`

### 3. Event Propagation Control

```python
event.stop()          # Completely stops propagation
event.prevent_default() # Only prevents default, actions still execute
```

- **Critical**: Use `event.stop()` to prevent both default behavior AND action execution
- **Location**: In `on_key()` when handling Esc in EDIT mode

## Bug Fix History

### Bug: Esc Key Closes Screen While in EDIT Mode

**Symptoms:**
- User presses `i` to enter EDIT mode
- User presses `Esc` expecting to exit EDIT mode
- Instead, the entire server management screen closes

**Root Cause:**
1. `on_key()` handles Esc, sets `_mode = "VIEW"`, calls `event.prevent_default()`
2. `event.prevent_default()` doesn't stop action binding execution
3. `action_handle_escape()` executes with `_mode == "VIEW"` (just changed)
4. `action_handle_escape()` sees VIEW mode, calls `self.dismiss(None)`

**Fix:**
1. Changed `event.prevent_default()` to `event.stop()` in `on_key()`
2. Updated `action_handle_escape()` to use real-time focus detection instead of relying on `_mode`

**Commit:** (reference to be added)

## Testing

### Manual Test Scenarios

1. **Basic EDIT Mode Entry/Exit:**
   - Press `i` → Should focus first field (EDIT mode)
   - Press `Esc` → Should unfocus field (VIEW mode)
   - Press `Esc` again → Should close screen

2. **Navigation in VIEW Mode:**
   - Press `j`/`k` → Should highlight fields (no focus)
   - Press `t`/`T` → Should cycle servers
   - Press `Esc` → Should close screen

3. **Navigation in EDIT Mode:**
   - Enter EDIT mode
   - Press `t`/`T` → Should NOT cycle servers (disabled)
   - Press `j`/`k` → Should NOT highlight fields (disabled)
   - Press `Tab` → Should move to next field (standard behavior)
   - Press `Esc` → Should exit EDIT mode (not close screen)

4. **Auto Mode Detection:**
   - Click on a form field → Should auto-enter EDIT mode
   - Click outside form → Should auto-exit EDIT mode

### Unit Tests

See: `tests/ariatuc/unit/test_server_management.py`

## Future Improvements

1. **Visual Mode Indicator:**
   - Add a status indicator showing current mode (VIEW/EDIT)
   - Similar to Vim's mode line

2. **Mode Transition Animations:**
   - Visual feedback when entering/exiting EDIT mode
   - Highlight focused field with different color

3. **Keyboard Shortcut Help:**
   - Show context-sensitive help based on current mode
   - `?` key to display available shortcuts

## References

- Vim-style modal editing: Inspiration for dual-mode design
- Textual Event System: https://textual.textualize.io/guide/events/
- lazygit UX: Keyboard-driven TUI interaction patterns
