#!/usr/bin/env python3
"""Start ariatuc TUI application.

This script starts the ariatuc TUI application with proper error handling
and helpful messages.

Usage:
    python scripts/start_app.py           # Start the TUI app
    python scripts/start_app.py --check   # Check if aria2c is running first
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_info(msg: str) -> None:
    """Print info message in green."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.NC}")

def print_warning(msg: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.NC}")

def print_error(msg: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}✗ {msg}{Colors.NC}")

def print_header(msg: str) -> None:
    """Print header message in blue."""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{msg}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

def check_aria2_running() -> bool:
    """Check if aria2c RPC server is accessible."""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:6800/jsonrpc"],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start ariatuc TUI application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start_app.py         # Start the app
  python scripts/start_app.py --check # Check aria2c status first

Note:
  Make sure aria2c RPC server is running before starting the app.
  Use 'mise run aria2:start' to start the aria2c server.
        """
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if aria2c is running before starting"
    )

    args = parser.parse_args()

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print_header("Starting ariatuc TUI Application")

    # Check aria2c status if requested
    if args.check:
        print_info("Checking aria2c RPC server...")
        if not check_aria2_running():
            print_error("aria2c RPC server is not running!")
            print()
            print_info("Start it with: mise run aria2:start")
            print_info("Or run the app anyway with: mise run dev")
            print()
            return 1
        print_info("aria2c RPC server is running")

    # Check if aria2c is running (warning only)
    if not args.check:
        if not check_aria2_running():
            print_warning("Warning: aria2c RPC server doesn't seem to be running")
            print_warning("The app may not work properly without it")
            print()
            print_info("Tip: Start aria2c with: mise run aria2:start")
            print()

    # Run the application
    try:
        print_info("Starting ariatuc...")
        print()

        # Run using python -m to ensure proper module loading
        result = subprocess.run(
            [sys.executable, "-m", "ariatuc"],
            cwd=project_root
        )

        return result.returncode

    except KeyboardInterrupt:
        print()
        print_info("Application stopped by user")
        return 130
    except Exception as e:
        print_error(f"Failed to start application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
