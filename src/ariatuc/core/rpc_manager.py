"""Multiple RPC server management.

The Aria2Client factory function automatically selects the protocol based on URL:
- ws:// or wss:// → WebSocketRPCClient (supports events)
- http:// or https:// → HTTPRPCClient (no events)
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from aria2rpc import Aria2Client, Aria2Error
from aria2rpc.http import HTTPRPCClient
from aria2rpc.websocket import WebSocketRPCClient

logger = logging.getLogger(__name__)


class ConnectionProtocol(Enum):
    """RPC connection protocol."""

    WEBSOCKET = "websocket"
    HTTP = "http"
    UNKNOWN = "unknown"


class ConnectionState(Enum):
    """Connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


@dataclass
class ServerConfig:
    """Configuration for an aria2 RPC server."""

    name: str
    url: str
    secret: str | None = None

    # Local server management
    is_local: bool = False
    """Whether this is a locally-managed aria2c process."""

    session_file: str | None = None
    """Path to session file. If None and is_local=True, uses default path:
    ~/.config/ariatuc/sessions/{name}.session
    """

    aria2c_path: str | None = None
    """Custom aria2c binary path. If None, uses 'aria2c' from PATH."""

    aria2c_options: dict[str, Any] | None = None
    """Additional aria2c command-line options for local process.
    Example: {'max-concurrent-downloads': 5, 'max-connection-per-server': 4}
    """

    def __str__(self) -> str:
        """String representation of server config."""
        return f"{self.name} ({self.url})"

    @property
    def is_websocket(self) -> bool:
        """Check if URL is WebSocket."""
        return self.url.startswith(("ws://", "wss://"))

    @property
    def protocol(self) -> ConnectionProtocol:
        """Get protocol type based on URL."""
        if self.url.startswith(("ws://", "wss://")):
            return ConnectionProtocol.WEBSOCKET
        if self.url.startswith(("http://", "https://")):
            return ConnectionProtocol.HTTP
        return ConnectionProtocol.UNKNOWN

    @property
    def managed_session_file(self) -> Path:
        """Get effective session file path for local server."""
        if self.session_file:
            return Path(self.session_file)
        # Default managed location
        config_dir = Path.home() / ".config" / "ariatuc" / "sessions"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / f"{self.name}.session"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for config persistence."""
        return {
            "name": self.name,
            "url": self.url,
            "secret": self.secret,
            "is_local": self.is_local,
            "session_file": self.session_file,
            "aria2c_path": self.aria2c_path,
            "aria2c_options": self.aria2c_options,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServerConfig":
        """Deserialize from dict."""
        return cls(
            name=data["name"],
            url=data["url"],
            secret=data.get("secret"),
            is_local=data.get("is_local", False),
            session_file=data.get("session_file"),
            aria2c_path=data.get("aria2c_path"),
            aria2c_options=data.get("aria2c_options"),
        )


@dataclass
class ServerState:
    """Runtime state for a server."""

    state: ConnectionState = ConnectionState.DISCONNECTED
    last_error: str | None = None
    client: HTTPRPCClient | WebSocketRPCClient | None = None


class RPCManager:
    """Manages multiple aria2 RPC server connections.

    The manager uses Aria2Client factory which automatically selects protocol
    based on URL scheme. No manual protocol fallback is needed.
    """

    def __init__(self, connection_timeout: int = 10):
        """Initialize the RPC manager.

        Args:
            connection_timeout: Connection timeout in seconds
        """
        self.servers: dict[str, ServerConfig] = {}
        self.current_server: str | None = None
        self.connection_timeout = connection_timeout

        # Runtime state per server
        self._states: dict[str, ServerState] = {}

    def add_server(
        self,
        name: str,
        url: str,
        secret: str | None = None,
    ) -> None:
        """Add a new server configuration.

        Args:
            name: Unique name for the server
            url: RPC endpoint URL (ws://, wss://, http://, or https://)
            secret: Optional RPC secret token
        """
        self.servers[name] = ServerConfig(name=name, url=url, secret=secret)
        self._states[name] = ServerState()

        # Set as current if it's the first server
        if self.current_server is None:
            self.current_server = name

        logger.info(f"Added server '{name}' with protocol: {self.servers[name].protocol.value}")

    def remove_server(self, name: str) -> None:
        """Remove a server configuration.

        Args:
            name: Name of the server to remove
        """
        if name in self.servers:
            # Clean up resources
            self._cleanup_server(name)
            del self.servers[name]
            del self._states[name]

            # Update current server if needed
            if self.current_server == name:
                self.current_server = next(iter(self.servers.keys()), None)

            logger.info(f"Removed server '{name}'")

    def switch_server(self, name: str) -> bool:
        """Switch to a different server.

        Args:
            name: Name of the server to switch to

        Returns:
            True if successful, False if server doesn't exist
        """
        if name in self.servers:
            self.current_server = name
            logger.info(f"Switched to server '{name}'")
            return True
        logger.warning(f"Cannot switch to non-existent server '{name}'")
        return False

    async def connect(self, name: str | None = None) -> bool:
        """Connect to a server.

        The Aria2Client factory automatically selects the protocol based on URL.

        Args:
            name: Server name (uses current server if None)

        Returns:
            True if connected successfully, False otherwise
        """
        server_name = name or self.current_server
        if server_name is None or server_name not in self.servers:
            logger.error(f"Server not found: {server_name}")
            return False

        server = self.servers[server_name]
        state = self._states[server_name]
        state.state = ConnectionState.CONNECTING

        logger.info(f"Connecting to '{server_name}' ({server.protocol.value})...")

        try:
            # Create client using factory (auto protocol selection)
            client = Aria2Client(server.url, secret=server.secret)

            # For WebSocket, explicitly connect
            if isinstance(client, WebSocketRPCClient):
                await asyncio.wait_for(client.connect(), timeout=self.connection_timeout)

            # Test connection with get_version
            await asyncio.wait_for(client.get_version(), timeout=self.connection_timeout)

            state.client = client
            state.state = ConnectionState.CONNECTED
            state.last_error = None

            logger.info(f"Connected to '{server_name}' successfully")
            return True

        except TimeoutError:
            error = "Connection timeout"
            state.last_error = error
            state.state = ConnectionState.FAILED
            logger.error(f"Connection to '{server_name}' failed: {error}")
        except Aria2Error as e:
            state.last_error = str(e)
            state.state = ConnectionState.FAILED
            logger.error(f"RPC error for '{server_name}': {e}")
        except Exception as e:
            state.last_error = str(e)
            state.state = ConnectionState.FAILED
            logger.error(f"Connection error for '{server_name}': {e}")

        return False

    async def disconnect(self, name: str | None = None) -> None:
        """Disconnect from a server.

        Args:
            name: Server name (uses current server if None)
        """
        server_name = name or self.current_server
        if server_name:
            self._cleanup_server(server_name)
            logger.info(f"Disconnected from '{server_name}'")

    def _cleanup_server(self, name: str) -> None:
        """Clean up server resources.

        Args:
            name: Server name
        """
        if name not in self._states:
            return

        state = self._states[name]

        # Close WebSocket client if applicable
        if isinstance(state.client, WebSocketRPCClient):
            try:
                # Schedule close in background (don't block)
                asyncio.create_task(state.client.close())
            except Exception as e:
                logger.error(f"Error closing WebSocket client for '{name}': {e}")

        # Update state
        state.client = None
        state.state = ConnectionState.DISCONNECTED

    def get_client(self, name: str | None = None) -> HTTPRPCClient | WebSocketRPCClient | None:
        """Get the active client for a server.

        Args:
            name: Server name (uses current server if None)

        Returns:
            Client instance or None if not connected
        """
        server_name = name or self.current_server
        if server_name is None or server_name not in self._states:
            return None

        return self._states[server_name].client

    def get_websocket_client(self, name: str | None = None) -> WebSocketRPCClient | None:
        """Get WebSocket client for a server (for event subscription).

        Args:
            name: Server name (uses current server if None)

        Returns:
            WebSocketRPCClient instance or None if not using WebSocket
        """
        client = self.get_client(name)
        if isinstance(client, WebSocketRPCClient):
            return client
        return None

    def get_current_server(self) -> ServerConfig | None:
        """Get the current server configuration.

        Returns:
            Current ServerConfig or None
        """
        if self.current_server:
            return self.servers.get(self.current_server)
        return None

    def get_server_state(self, name: str | None = None) -> ServerState | None:
        """Get server runtime state.

        Args:
            name: Server name (uses current server if None)

        Returns:
            ServerState or None
        """
        server_name = name or self.current_server
        if server_name:
            return self._states.get(server_name)
        return None

    def get_protocol(self, name: str | None = None) -> ConnectionProtocol:
        """Get the protocol type for a server.

        Args:
            name: Server name (uses current server if None)

        Returns:
            ConnectionProtocol enum
        """
        server_name = name or self.current_server
        if server_name and server_name in self.servers:
            return self.servers[server_name].protocol
        return ConnectionProtocol.UNKNOWN

    def is_websocket(self, name: str | None = None) -> bool:
        """Check if server is using WebSocket protocol.

        Args:
            name: Server name (uses current server if None)

        Returns:
            True if using WebSocket, False otherwise
        """
        return self.get_protocol(name) == ConnectionProtocol.WEBSOCKET

    def list_servers(self) -> list[ServerConfig]:
        """Get list of all servers.

        Returns:
            List of ServerConfig objects
        """
        return list(self.servers.values())

    async def health_check(self, name: str | None = None) -> bool:
        """Check if server connection is healthy.

        Args:
            name: Server name (uses current server if None)

        Returns:
            True if healthy, False otherwise
        """
        client = self.get_client(name)
        if not client:
            return False

        try:
            await asyncio.wait_for(client.get_version(), timeout=5)
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def get_server_config(self, name: str | None = None) -> ServerConfig:
        """Get server configuration.

        Args:
            name: Server name (None = current server)

        Returns:
            ServerConfig

        Raises:
            KeyError: If server not found
        """
        server_name = name or self.current_server
        if not server_name or server_name not in self.servers:
            raise KeyError(f"Server not found: {server_name}")
        return self.servers[server_name]
