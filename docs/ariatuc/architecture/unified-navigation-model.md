# Unified Navigation Model

ariatuc uses a unified navigation model across all settings and management screens, inspired by modal editors like Vim.

## Core Concepts

### Two Modes: VIEW and EDIT

The interface operates in two distinct modes:

1. **VIEW Mode** (Default)
   - Navigation and inspection mode
   - All navigation keys work **globally** regardless of focus
   - Can browse, scroll, and trigger actions
   - No direct text editing

2. **EDIT Mode** (Field Focused)
   - Text editing mode
   - Activated when a form field is focused
   - Standard text input behavior
   - Tab moves between fields

## Global Navigation Keys (VIEW Mode)

These keys work **anywhere in the screen**, regardless of which panel has focus:

### Left Panel Navigation

- `t` - Next item (cycle forward)
- `T` - Previous item (cycle backward)

**Applies to:**
- Server Management: Cycle through servers
- Aria2 Settings: Cycle through sections

### Right Panel Navigation

- `j` - Scroll to next field (no focus)
- `k` - Scroll to previous field (no focus)

**Purpose:** Preview form fields without entering edit mode

### Mode Switching

- `i` - Enter EDIT mode (focus on first field)
- `Esc` - Exit EDIT mode (return to VIEW)
  - In VIEW mode: Close screen

## Why This Model?

### 1. **Consistency**

The same keys work the same way across all screens:
- `t/T` always navigates left panel
- `j/k` always navigates right panel
- `i` always enters edit mode
- `Esc` always exits current context

### 2. **No Context Dependency**

Traditional UI navigation requires you to:
1. Focus on the left panel
2. Navigate within it
3. Switch focus to right panel
4. Navigate within it

With unified navigation:
- `t/T` works regardless of focus
- `j/k` works regardless of focus
- No manual focus switching needed

### 3. **Efficient Workflow**

Common workflow example:

```
[VIEW Mode - browsing servers]
t t t              → Cycle through 3 servers quickly
j j j              → Preview their configurations
Enter              → Test connection on current server
i                  → Edit a field
[EDIT Mode]
<type changes>
Tab Tab            → Move to next fields
Esc                → Return to VIEW mode
w                  → Save changes
Space              → Set as current server
```

No focus management, no clicking required!

## Comparison with Traditional Navigation

### Traditional (Focus-Based)

```
Click left panel   → Focus on server list
↓ ↓ ↓              → Navigate servers
Click right panel  → Focus on form
↓ ↓                → Navigate fields
Click field        → Start editing
Esc                → Exit field (but stay in form)
Click elsewhere    → Change focus again
```

### Unified (Mode-Based)

```
t t t              → Navigate servers (global)
j j                → Preview fields (global)
i                  → Edit mode (focus first field)
Esc                → VIEW mode (blur all)
```

## Implementation Details

### For Developers

Each settings screen implements:

1. **Mode State Tracking**
   ```python
   self._mode = "VIEW"  # or "EDIT"
   ```

2. **Global Key Handler**
   ```python
   def on_key(self, event) -> None:
       # Detect mode from focused widget
       focused = self.app.focused
       in_edit_mode = isinstance(focused, (Input, TextArea, Select))

       if self._mode == "EDIT":
           # Only handle Esc in EDIT mode
           if key == "escape":
               self.set_focus(None)  # Blur field
               self._mode = "VIEW"
           return

       # VIEW mode: handle navigation globally
       if key == "t":
           self._cycle_left_panel(1)
       elif key == "T":
           self._cycle_left_panel(-1)
       # ... etc
   ```

3. **Navigation Methods**
   - `_cycle_left_panel(direction)` - Navigate left panel items
   - `_navigate_field(direction)` - Scroll to fields in VIEW mode

### Screens Using This Model

- ✅ `server_management_screen.py` - Server configuration
- ✅ `aria2_settings_screen.py` - Aria2 global settings
- 🔄 `app_settings_screen.py` - To be updated (future)

## Benefits for Users

1. **Muscle Memory**: Same keys work everywhere
2. **Speed**: No clicking or focus switching
3. **Clarity**: Clear mental model (VIEW vs EDIT)
4. **Accessibility**: Fully keyboard-driven
5. **Productivity**: Vim-like efficiency for power users

## Related Documentation

- [Server Management Testing Guide](./server-management-testing.md)
- [Aria2 Settings Documentation](./ariatuc/architecture/)
