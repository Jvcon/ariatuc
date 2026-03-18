"""Main entry point for ariatuc TUI application."""

from ariatuc.ui.app import AriatucApp
from ariatuc.utils.logger import setup_logging


def main() -> None:
    """Run the ariatuc application."""
    # Initialize logging before starting the app
    setup_logging()

    app = AriatucApp()
    app.run()


if __name__ == "__main__":
    main()
