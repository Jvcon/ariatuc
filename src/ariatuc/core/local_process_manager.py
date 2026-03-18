"""Local aria2c process lifecycle management.

This module provides functionality to start, stop, restart, and monitor
local aria2c daemon processes managed by ariatuc.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ProcessState(Enum):
    """Local aria2c process state."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ProcessInfo:
    """Information about a local aria2c process."""

    pid: int | None = None
    state: ProcessState = ProcessState.STOPPED
    last_error: str | None = None
    process: asyncio.subprocess.Process | None = None


class LocalProcessManager:
    """Manages local aria2c process lifecycle.

    Features:
    - Start aria2c with custom configuration
    - Stop/restart with graceful shutdown
    - Health monitoring
    - Automatic session file configuration
    """

    def __init__(self) -> None:
        """Initialize the local process manager."""
        self._processes: dict[str, ProcessInfo] = {}
        self._monitoring_tasks: dict[str, asyncio.Task] = {}

    async def start_process(
        self,
        server_name: str,
        aria2c_path: str | None,
        rpc_port: int,
        rpc_secret: str | None,
        session_file: Path,
        options: dict[str, Any] | None = None,
    ) -> bool:
        """Start a local aria2c process.

        Args:
            server_name: Server identifier
            aria2c_path: Path to aria2c binary (None = use PATH)
            rpc_port: RPC listen port
            rpc_secret: RPC authentication secret
            session_file: Path to session file
            options: Additional aria2c options

        Returns:
            True if started successfully

        Raises:
            ProcessError: If process startup fails
        """
        if server_name in self._processes:
            info = self._processes[server_name]
            if info.state in (ProcessState.RUNNING, ProcessState.STARTING):
                logger.warning(f"Process {server_name} already running")
                return False

        # Prepare process info
        info = ProcessInfo(state=ProcessState.STARTING)
        self._processes[server_name] = info

        try:
            # Build command
            cmd = self._build_command(
                aria2c_path or "aria2c",
                rpc_port,
                rpc_secret,
                session_file,
                options or {},
            )

            logger.info(f"Starting aria2c for {server_name}: {' '.join(cmd)}")

            # Start process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait briefly to check if it crashes immediately
            await asyncio.sleep(0.5)

            if process.returncode is not None:
                # Process exited immediately
                _, stderr_bytes = await process.communicate()
                stderr = stderr_bytes.decode() if stderr_bytes else ""
                raise ProcessError(f"aria2c exited immediately: {stderr}")

            # Update info
            info.pid = process.pid
            info.state = ProcessState.RUNNING
            info.process = process
            info.last_error = None

            logger.info(f"Started aria2c (PID: {process.pid}) for {server_name}")

            # Start monitoring task
            self._start_monitoring(server_name)

            return True

        except Exception as e:
            logger.error(f"Failed to start aria2c for {server_name}: {e}")
            info.state = ProcessState.ERROR
            info.last_error = str(e)
            return False

    def _build_command(
        self,
        aria2c_path: str,
        rpc_port: int,
        rpc_secret: str | None,
        session_file: Path,
        options: dict[str, Any],
    ) -> list[str]:
        """Build aria2c command line."""
        cmd = [aria2c_path]

        # Essential RPC options
        cmd.extend(
            [
                "--enable-rpc=true",
                f"--rpc-listen-port={rpc_port}",
                "--rpc-listen-all=false",  # Only localhost for security
            ]
        )

        if rpc_secret:
            cmd.append(f"--rpc-secret={rpc_secret}")

        # Session management
        cmd.extend(
            [
                f"--save-session={session_file}",
                f"--input-file={session_file}",
                "--save-session-interval=60",  # Save every minute
            ]
        )

        # Daemon mode
        cmd.append("--daemon=false")  # We manage the process

        # Additional options
        for key, value in options.items():
            if key not in (
                "enable-rpc",
                "rpc-listen-port",
                "rpc-secret",
                "save-session",
                "input-file",
                "daemon",
            ):
                cmd.append(f"--{key}={value}")

        return cmd

    async def stop_process(
        self,
        server_name: str,
        force: bool = False,
        timeout: int = 10,
    ) -> bool:
        """Stop a local aria2c process.

        Args:
            server_name: Server identifier
            force: Use force shutdown if True
            timeout: Timeout in seconds for graceful shutdown

        Returns:
            True if stopped successfully
        """
        info = self._processes.get(server_name)
        if not info or info.state != ProcessState.RUNNING:
            logger.warning(f"Process {server_name} not running")
            return False

        info.state = ProcessState.STOPPING

        try:
            if force or not info.process:
                # Force kill
                if info.process:
                    info.process.kill()
                    await asyncio.wait_for(info.process.wait(), timeout=5)
            else:
                # Graceful shutdown via SIGTERM
                info.process.terminate()
                try:
                    await asyncio.wait_for(info.process.wait(), timeout=timeout)
                except TimeoutError:
                    logger.warning(f"Process {server_name} didn't stop gracefully, killing")
                    info.process.kill()
                    await asyncio.wait_for(info.process.wait(), timeout=5)

            # Stop monitoring
            self._stop_monitoring(server_name)

            # Update state
            info.state = ProcessState.STOPPED
            info.pid = None
            info.process = None

            logger.info(f"Stopped aria2c for {server_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop aria2c for {server_name}: {e}")
            info.state = ProcessState.ERROR
            info.last_error = str(e)
            return False

    async def restart_process(
        self,
        server_name: str,
        aria2c_path: str | None,
        rpc_port: int,
        rpc_secret: str | None,
        session_file: Path,
        options: dict[str, Any] | None = None,
    ) -> bool:
        """Restart a local aria2c process.

        Performs graceful stop followed by start.
        """
        logger.info(f"Restarting aria2c for {server_name}")

        # Stop existing process
        await self.stop_process(server_name, force=False)

        # Wait briefly
        await asyncio.sleep(1)

        # Start new process
        return await self.start_process(
            server_name,
            aria2c_path,
            rpc_port,
            rpc_secret,
            session_file,
            options,
        )

    def get_process_info(self, server_name: str) -> ProcessInfo | None:
        """Get process information."""
        return self._processes.get(server_name)

    def is_running(self, server_name: str) -> bool:
        """Check if process is running."""
        info = self._processes.get(server_name)
        return info is not None and info.state == ProcessState.RUNNING

    def _start_monitoring(self, server_name: str) -> None:
        """Start background monitoring task."""
        if server_name in self._monitoring_tasks:
            return

        async def monitor() -> None:
            while True:
                await asyncio.sleep(5)  # Check every 5 seconds

                info = self._processes.get(server_name)
                if not info or info.state != ProcessState.RUNNING:
                    break

                # Check if process is still alive
                if info.process and info.process.returncode is not None:
                    logger.warning(f"Process {server_name} died unexpectedly")
                    info.state = ProcessState.ERROR
                    info.last_error = "Process died unexpectedly"
                    break

        task = asyncio.create_task(monitor())
        self._monitoring_tasks[server_name] = task

    def _stop_monitoring(self, server_name: str) -> None:
        """Stop monitoring task."""
        task = self._monitoring_tasks.pop(server_name, None)
        if task:
            task.cancel()

    async def cleanup(self) -> None:
        """Cleanup all managed processes."""
        logger.info("Cleaning up local processes...")

        # Stop all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        self._monitoring_tasks.clear()

        # Stop all processes
        for server_name in list(self._processes.keys()):
            await self.stop_process(server_name, force=False)


class ProcessError(Exception):
    """Local process management error."""

    pass
