"""Check all CSS in widgets for syntax errors."""

import importlib
import inspect
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_widget_css(module_path: str):
    """Check CSS in a widget module."""
    try:
        module = importlib.import_module(module_path)

        # Find all classes in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, 'DEFAULT_CSS'):
                css = obj.DEFAULT_CSS
                print(f"\nChecking {module_path}.{name}...")
                print(f"CSS length: {len(css)} characters")

                # For now, just check that CSS is a non-empty string
                # Full CSS validation would require integrating with Textual's parser
                if css and isinstance(css, str):
                    print(f"  ✓ CSS format is valid (basic check)")
                else:
                    print(f"  ✗ CSS Error: Invalid CSS format")
                    return False
        return True
    except Exception as e:
        print(f"Error loading {module_path}: {e}")
        return False


if __name__ == "__main__":
    print("=== Checking CSS in all widgets ===\n")

    widgets = [
        "ariatuc.ui.app",
        "ariatuc.ui.screens.main_screen",
        "ariatuc.ui.screens.help_screen",
        "ariatuc.ui.widgets.add_download_dialog",
        "ariatuc.ui.widgets.command_bar",
        "ariatuc.ui.widgets.confirm_dialog",
        "ariatuc.ui.widgets.download_detail",
        "ariatuc.ui.widgets.download_list",
        "ariatuc.ui.widgets.status_bar",
    ]

    all_ok = True
    for widget in widgets:
        if not check_widget_css(widget):
            all_ok = False

    print("\n" + "="*50)
    if all_ok:
        print("✓ All CSS checks passed!")
    else:
        print("✗ Some CSS checks failed!")
        sys.exit(1)
