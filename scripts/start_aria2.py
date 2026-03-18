#!/usr/bin/env python3
"""Start aria2c RPC server for ariatuc development and testing.

This script starts an aria2c daemon with RPC enabled for use with ariatuc.
The configuration is suitable for local development and testing.

Usage:
    python scripts/start_aria2.py              # Start with default config
    python scripts/start_aria2.py --stop       # Stop the running daemon
    python scripts/start_aria2.py --status     # Check daemon status
    python scripts/start_aria2.py --restart    # Restart the daemon
    python scripts/start_aria2.py --logs       # Show aria2c logs
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

class Aria2Server:
    """Manages aria2c RPC server for ariatuc."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.aria2_dir = project_root / ".aria2"
        self.config_file = self.aria2_dir / "aria2.conf"
        self.pid_file = self.aria2_dir / "aria2.pid"
        self.log_file = self.aria2_dir / "aria2.log"
        self.downloads_dir = self.aria2_dir / "downloads"
        self.session_file = self.aria2_dir / "session.txt"

        # RPC settings
        self.rpc_port = 6800
        self.rpc_secret = ""  # Empty secret for development

    def check_aria2c_installed(self) -> bool:
        """Check if aria2c is installed."""
        return shutil.which("aria2c") is not None

    def setup_config(self) -> None:
        """Create aria2c configuration for development."""
        print_info("Setting up aria2c configuration...")

        # Create directories
        self.aria2_dir.mkdir(exist_ok=True)
        self.downloads_dir.mkdir(exist_ok=True)

        # Create empty session file if it doesn't exist
        if not self.session_file.exists():
            self.session_file.touch()

        # Create configuration file
        # Note: rpc-secret is omitted for development (no authentication)
        # In production, set a secure secret token
        config_content = f"""# aria2 configuration for ariatuc development
# RPC Configuration
enable-rpc=true
rpc-listen-all=false
rpc-allow-origin-all=true
rpc-listen-port={self.rpc_port}

# Download Settings
dir={self.downloads_dir}
max-concurrent-downloads=5
max-connection-per-server=16
min-split-size=1M
split=4
continue=true
always-resume=true

# Speed Limits (optional, comment out for unlimited)
# max-overall-download-limit=0
# max-download-limit=0

# BitTorrent Settings
enable-dht=true
enable-peer-exchange=true
bt-enable-lpd=true
bt-max-peers=50

# Logging
log={self.log_file}
log-level=notice

# Session Management
save-session={self.session_file}
input-file={self.session_file}
save-session-interval=60

# Performance
disk-cache=32M
file-allocation=prealloc

# Connection Settings
timeout=60
connect-timeout=30
max-tries=5
retry-wait=10
"""
        self.config_file.write_text(config_content)
        print_info(f"Configuration created at: {self.config_file}")
        print_info(f"Downloads directory: {self.downloads_dir}")
        print_info(f"RPC endpoint: http://localhost:{self.rpc_port}/jsonrpc")

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
            # PID file exists but process is not running
            self.pid_file.unlink(missing_ok=True)
            return False

    def get_status(self) -> dict:
        """Get detailed status of aria2c daemon."""
        status = {
            "running": self.is_running(),
            "config_exists": self.config_file.exists(),
            "pid": None,
            "rpc_url": f"http://localhost:{self.rpc_port}/jsonrpc",
        }

        if status["running"]:
            try:
                status["pid"] = int(self.pid_file.read_text().strip())
            except (ValueError, FileNotFoundError):
                pass

        return status

    def start(self) -> bool:
        """Start aria2c daemon."""
        if self.is_running():
            print_warning("aria2c is already running")
            pid = int(self.pid_file.read_text().strip())
            print_info(f"PID: {pid}")
            print_info(f"RPC: http://localhost:{self.rpc_port}/jsonrpc")
            return True

        # Check if aria2c is installed
        if not self.check_aria2c_installed():
            print_error("aria2c is not installed!")
            print_info("Install it with:")
            print_info("  macOS:   brew install aria2")
            print_info("  Ubuntu:  sudo apt install aria2")
            print_info("  Arch:    sudo pacman -S aria2")
            return False

        print_header("Starting aria2c RPC Server")

        # Ensure config exists
        if not self.config_file.exists():
            self.setup_config()

        try:
            # Start aria2c in daemon mode
            subprocess.run(
                ["aria2c", f"--conf-path={self.config_file}", "--daemon=true"],
                check=True,
                capture_output=True,
                text=True
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
                print_info(f"aria2c started successfully (PID: {pid})")
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
                        break
                except subprocess.TimeoutExpired:
                    pass
                time.sleep(1)
            else:
                print_warning("RPC might not be ready, check logs if issues occur")

            print()
            print_info(f"RPC URL: http://localhost:{self.rpc_port}/jsonrpc")
            print_info(f"Log file: {self.log_file}")
            print_info(f"Downloads: {self.downloads_dir}")
            print()
            print_info("Use 'mise run dev' to start the ariatuc TUI")
            print_info("Use 'mise run aria2:stop' to stop the server")
            print_info("Use 'mise run aria2:logs' to view logs")

            return True

        except subprocess.CalledProcessError as e:
            print_error(f"Failed to start aria2c: {e}")
            if e.stderr:
                print_error(e.stderr)
            return False
        except FileNotFoundError:
            print_error("aria2c command not found!")
            return False

    def stop(self) -> bool:
        """Stop aria2c daemon."""
        print_header("Stopping aria2c RPC Server")

        if not self.is_running():
            print_warning("aria2c is not running")
            return True

        try:
            pid = int(self.pid_file.read_text().strip())
            print_info(f"Stopping aria2c (PID: {pid})...")

            # Try graceful shutdown first (SIGTERM)
            os.kill(pid, signal.SIGTERM)

            # Wait for process to terminate
            for _ in range(10):
                try:
                    os.kill(pid, 0)  # Check if still running
                    time.sleep(0.5)
                except ProcessLookupError:
                    # Process has terminated
                    break
            else:
                # If still running after 5 seconds, force kill
                print_warning("Graceful shutdown timed out, forcing...")
                try:
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(0.5)
                except ProcessLookupError:
                    pass

            # Clean up PID file
            self.pid_file.unlink(missing_ok=True)
            print_info("aria2c stopped successfully")
            return True

        except (ProcessLookupError, ValueError) as e:
            print_warning(f"Process not found, cleaning up: {e}")
            self.pid_file.unlink(missing_ok=True)
            return True
        except Exception as e:
            print_error(f"Error stopping aria2c: {e}")
            return False

    def restart(self) -> bool:
        """Restart aria2c daemon."""
        print_header("Restarting aria2c RPC Server")
        self.stop()
        time.sleep(1)
        return self.start()

    def show_logs(self, follow: bool = False) -> None:
        """Show aria2c logs."""
        if not self.log_file.exists():
            print_warning(f"Log file not found: {self.log_file}")
            return

        print_header("aria2c Logs")
        print_info(f"Log file: {self.log_file}")
        print()

        if follow:
            # Follow logs in real-time
            try:
                subprocess.run(["tail", "-f", str(self.log_file)])
            except KeyboardInterrupt:
                print()
                print_info("Stopped following logs")
        else:
            # Show last 50 lines
            try:
                subprocess.run(["tail", "-n", "50", str(self.log_file)])
            except Exception as e:
                print_error(f"Error reading logs: {e}")

    def print_status(self) -> None:
        """Print current status."""
        status = self.get_status()

        print_header("aria2c RPC Server Status")

        if status["running"]:
            print_info(f"Status: Running (PID: {status['pid']})")
            print_info(f"RPC URL: {status['rpc_url']}")
            print_info(f"Config: {self.config_file}")
            print_info(f"Logs: {self.log_file}")
            print_info(f"Downloads: {self.downloads_dir}")
        else:
            print_warning("Status: Not running")
            if status["config_exists"]:
                print_info(f"Config exists at: {self.config_file}")
                print_info("Run 'mise run aria2:start' to start the server")

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage aria2c RPC server for ariatuc",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start_aria2.py           # Start the server
  python scripts/start_aria2.py --stop    # Stop the server
  python scripts/start_aria2.py --status  # Check status
  python scripts/start_aria2.py --logs    # View logs
  python scripts/start_aria2.py --logs -f # Follow logs in real-time
        """
    )

    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the aria2c daemon"
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart the aria2c daemon"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show daemon status"
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Show aria2c logs"
    )
    parser.add_argument(
        "-f", "--follow",
        action="store_true",
        help="Follow logs in real-time (use with --logs)"
    )

    args = parser.parse_args()

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Create server manager
    server = Aria2Server(project_root)

    # Execute command
    if args.stop:
        return 0 if server.stop() else 1
    elif args.restart:
        return 0 if server.restart() else 1
    elif args.status:
        server.print_status()
        return 0
    elif args.logs:
        server.show_logs(follow=args.follow)
        return 0
    else:
        # Default: start the server
        return 0 if server.start() else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print_info("Interrupted by user")
        sys.exit(130)
