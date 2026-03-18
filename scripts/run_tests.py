#!/usr/bin/env python3
"""Unified test runner for aria2rpc package.

This script provides a comprehensive testing solution that:
- Manages aria2c daemon lifecycle for integration tests
- Runs different test categories (unit, integration, all)
- Provides clear output and error handling
- Can be easily integrated with mise tasks

Usage:
    python scripts/run_tests.py               # Run all tests (with aria2c)
    python scripts/run_tests.py --unit        # Run only unit tests (fast, no aria2c)
    python scripts/run_tests.py --integration # Run only integration tests (needs aria2c)
    python scripts/run_tests.py --setup-only  # Just setup aria2c configuration
    python scripts/run_tests.py --no-daemon   # Run tests without starting/stopping aria2c
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
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
    print(f"{Colors.GREEN}{msg}{Colors.NC}")

def print_warning(msg: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}{msg}{Colors.NC}")

def print_error(msg: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}{msg}{Colors.NC}")

def print_header(msg: str) -> None:
    """Print header message in blue."""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{msg}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

class Aria2Manager:
    """Manages aria2c daemon for integration tests."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.aria2_dir = project_root / ".test_aria2"
        self.config_file = self.aria2_dir / "aria2.conf"
        self.pid_file = self.aria2_dir / "aria2.pid"
        self.log_file = self.aria2_dir / "aria2.log"
        self.downloads_dir = self.aria2_dir / "downloads"
        self.session_file = self.aria2_dir / "session.txt"

    def check_aria2c_installed(self) -> bool:
        """Check if aria2c is installed."""
        return shutil.which("aria2c") is not None

    def setup_config(self) -> None:
        """Create aria2c configuration for testing."""
        print_info("Setting up aria2c configuration...")

        # Create directories
        self.aria2_dir.mkdir(exist_ok=True)
        self.downloads_dir.mkdir(exist_ok=True)

        # Create configuration file
        config_content = f"""# aria2 configuration for integration tests
enable-rpc=true
rpc-listen-all=true
rpc-allow-origin-all=true
rpc-listen-port=6800
rpc-secret=

# Download settings
dir={self.downloads_dir}
max-concurrent-downloads=5
max-connection-per-server=4
min-split-size=1M
split=4

# Logging
log={self.log_file}
log-level=notice

# Session
save-session={self.session_file}
input-file={self.session_file}
save-session-interval=60

# Misc
continue=true
always-resume=true
"""
        self.config_file.write_text(config_content)
        print_info(f"Configuration created at: {self.config_file}")

    def is_running(self) -> bool:
        """Check if aria2c daemon is running."""
        if not self.pid_file.exists():
            return False

        try:
            pid = int(self.pid_file.read_text().strip())
            # Check if process is running
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, ValueError):
            return False

    def start(self) -> bool:
        """Start aria2c daemon."""
        if self.is_running():
            print_warning("aria2c is already running")
            return True

        print_info("Starting aria2c daemon...")

        # Ensure config exists
        if not self.config_file.exists():
            self.setup_config()

        try:
            # Start aria2c in daemon mode
            subprocess.run(
                ["aria2c", f"--conf-path={self.config_file}", "--daemon=true"],
                check=True,
                capture_output=True
            )

            # Wait a bit for daemon to start
            time.sleep(1)

            # Find and save PID
            result = subprocess.run(
                ["pgrep", "-f", f"aria2c.*{self.config_file}"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip().split('\n')[0]
                self.pid_file.write_text(pid)
                print_info(f"aria2c started (PID: {pid})")
            else:
                print_error("Failed to find aria2c process")
                return False

            # Wait for RPC to be ready
            print_info("Waiting for RPC to be ready...")
            for _ in range(10):
                try:
                    result = subprocess.run(
                        ["curl", "-s", "http://localhost:6800/jsonrpc"],
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        print_info("RPC is ready!")
                        return True
                except subprocess.TimeoutExpired:
                    pass
                time.sleep(1)

            print_warning("RPC might not be ready, continuing anyway...")
            return True

        except subprocess.CalledProcessError as e:
            print_error(f"Failed to start aria2c: {e}")
            if e.stderr:
                print_error(e.stderr.decode())
            return False

    def stop(self) -> None:
        """Stop aria2c daemon."""
        print_info("Stopping aria2c daemon...")

        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())

                # Try graceful shutdown first
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(1)

                    # Check if still running
                    try:
                        os.kill(pid, 0)
                        # Still running, force kill
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Already stopped

                except ProcessLookupError:
                    pass  # Already stopped

                self.pid_file.unlink()
                print_info("aria2c stopped")

            except (ValueError, OSError) as e:
                print_warning(f"Error stopping aria2c: {e}")

        # Fallback: try to kill any aria2c with our config
        try:
            subprocess.run(
                ["pkill", "-f", f"aria2c.*{self.config_file}"],
                capture_output=True
            )
        except subprocess.CalledProcessError:
            pass  # No process found or already killed

class TestRunner:
    """Manages test execution."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.aria2_manager = Aria2Manager(project_root)

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        # Check if poetry is available
        if not shutil.which("poetry"):
            print_error("Poetry is not installed or not in PATH")
            return False

        # Check if pytest is installed
        result = subprocess.run(
            ["poetry", "run", "pytest", "--version"],
            capture_output=True,
            cwd=self.project_root
        )
        if result.returncode != 0:
            print_error("pytest is not installed. Run: poetry install --with dev")
            return False

        return True

    def run_unit_tests(self, verbose: bool = True, coverage: bool = False) -> int:
        """Run unit tests (fast, no aria2c needed)."""
        print_header("Running Unit Tests")

        cmd = ["poetry", "run", "pytest", "-m", "not integration"]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(["--cov=aria2rpc", "--cov=ariatuc", "--cov-report=term-missing"])

        # Run unit tests from both packages
        cmd.extend([
            "tests/aria2rpc/unit/",
            "tests/ariatuc/unit/",
        ])

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode

    def run_integration_tests(self, verbose: bool = True) -> int:
        """Run integration tests (requires aria2c)."""
        print_header("Running Integration Tests")

        cmd = ["poetry", "run", "pytest", "-m", "integration"]

        if verbose:
            cmd.append("-v")

        # Run integration tests from aria2rpc package
        cmd.append("tests/aria2rpc/integration/")

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode

    def run_all_tests(self, verbose: bool = True, coverage: bool = False) -> int:
        """Run all tests."""
        print_header("Running All Tests")

        cmd = ["poetry", "run", "pytest"]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(["--cov=aria2rpc", "--cov=ariatuc", "--cov-report=term-missing"])

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified test runner for aria2rpc package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests with aria2c management
  %(prog)s --unit             # Run only unit tests (fast)
  %(prog)s --integration      # Run only integration tests
  %(prog)s --no-daemon        # Run tests without managing aria2c
  %(prog)s --setup-only       # Just setup aria2c configuration
  %(prog)s --coverage         # Run with coverage report
        """
    )

    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests (no aria2c needed)"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests (requires aria2c)"
    )

    parser.add_argument(
        "--no-daemon",
        action="store_true",
        help="Don't start/stop aria2c daemon (assume it's already running)"
    )

    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Just setup aria2c configuration and exit"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Less verbose output"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )

    args = parser.parse_args()

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Initialize managers
    runner = TestRunner(project_root)
    aria2_manager = runner.aria2_manager

    # Setup only mode
    if args.setup_only:
        if not aria2_manager.check_aria2c_installed():
            print_error("aria2c is not installed")
            print_info("Install instructions:")
            print_info("  macOS:   brew install aria2")
            print_info("  Ubuntu:  sudo apt install aria2")
            print_info("  Arch:    sudo pacman -S aria2")
            return 1

        aria2_manager.setup_config()
        print_info("\nTo start aria2c manually:")
        print_info(f"  aria2c --conf-path={aria2_manager.config_file}")
        return 0

    # Check dependencies
    if not runner.check_dependencies():
        return 1

    # Determine test mode
    needs_aria2c = args.integration or (not args.unit and not args.integration)
    manage_daemon = needs_aria2c and not args.no_daemon

    # Check aria2c if needed
    if needs_aria2c and not aria2_manager.check_aria2c_installed():
        print_error("aria2c is not installed but is required for integration tests")
        print_info("Install instructions:")
        print_info("  macOS:   brew install aria2")
        print_info("  Ubuntu:  sudo apt install aria2")
        print_info("  Arch:    sudo pacman -S aria2")
        print_info("\nOr run unit tests only with: --unit")
        return 1

    exit_code = 0

    try:
        # Start aria2c if needed
        if manage_daemon:
            if not aria2_manager.start():
                print_error("Failed to start aria2c")
                return 1

        verbose = not args.quiet

        # Run tests based on mode
        if args.unit:
            exit_code = runner.run_unit_tests(verbose=verbose, coverage=args.coverage)
        elif args.integration:
            exit_code = runner.run_integration_tests(verbose=verbose)
        else:
            # Run all tests
            exit_code = runner.run_all_tests(verbose=verbose, coverage=args.coverage)

        # Print summary
        print_header("Test Summary")
        if exit_code == 0:
            print_info("✅ All tests passed!")
        else:
            print_error("❌ Some tests failed")

    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
        exit_code = 130

    finally:
        # Stop aria2c if we started it
        if manage_daemon:
            aria2_manager.stop()

    return exit_code

if __name__ == "__main__":
    sys.exit(main())