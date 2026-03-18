"""Configuration management."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    """Application configuration."""

    # Server configurations
    servers: list[dict[str, Any]]
    current_server: str | None = None

    # Connection preferences
    prefer_websocket: bool = True  # Prefer WebSocket over HTTP
    websocket_fallback_http: bool = True  # Auto fallback to HTTP if WS fails
    connection_timeout: int = 10  # Connection timeout in seconds
    reconnect_interval: int = 5  # Reconnection interval in seconds

    # UI preferences
    theme: str = "dark"
    auto_refresh: bool = True
    refresh_interval: int = 1000  # milliseconds

    # Download defaults
    default_download_dir: str | None = None
    max_concurrent_downloads: int = 5
    max_connection_per_server: int = 16

    # Event notifications
    enable_notifications: bool = True
    play_sound_on_complete: bool = True
    play_sound_on_error: bool = True

    # Local process management settings
    local_process_monitoring: bool = True
    """Enable health monitoring for local aria2c processes."""

    auto_start_local: bool = True
    """Automatically start local aria2c when connecting if not running."""

    auto_save_session_interval: int | None = 300
    """Auto-save session every N seconds. None = disabled. Default: 5 minutes."""


class ConfigManager:
    """Manages application configuration."""

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "ariatuc"
    CONFIG_FILE = "config.json"

    # Default localhost server configuration
    DEFAULT_SERVER = {
        "name": "local",
        "url": "http://localhost:6800/jsonrpc",
        "secret": None,
        "is_local": True,
        "session_file": None,  # Use default managed path
        "aria2c_path": None,  # Use system aria2c
        "aria2c_options": {
            "max-concurrent-downloads": 5,
            "max-connection-per-server": 4,
            "enable-rpc": True,
            "rpc-listen-port": 6800,
        },
    }

    def __init__(self, config_dir: Path | None = None):
        """Initialize the config manager.

        Args:
            config_dir: Custom config directory (uses default if None)
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_path = self.config_dir / self.CONFIG_FILE
        self.config: AppConfig | None = None

    def load(self) -> AppConfig:
        """Load configuration from file.

        Returns:
            AppConfig instance
        """
        if not self.config_path.exists():
            # Create default config with localhost server
            self.config = AppConfig(
                servers=[self.DEFAULT_SERVER],
                current_server="local",  # Auto-select the default server
            )
            self.save()
            return self.config

        try:
            with open(self.config_path) as f:
                data = json.load(f)
                self.config = AppConfig(**data)
                return self.config
        except (json.JSONDecodeError, TypeError):
            # If config is corrupted, create new default config
            self.config = AppConfig(
                servers=[self.DEFAULT_SERVER],
                current_server="local",
            )
            self.save()
            return self.config

    def save(self) -> None:
        """Save configuration to file."""
        if self.config is None:
            return

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Save to file
        with open(self.config_path, "w") as f:
            json.dump(asdict(self.config), f, indent=2)

    def get(self) -> AppConfig:
        """Get current configuration.

        Returns:
            AppConfig instance (loads if not already loaded)
        """
        if self.config is None:
            return self.load()
        return self.config

    def update(self, **kwargs) -> None:
        """Update configuration values.

        Args:
            **kwargs: Configuration fields to update
        """
        if self.config is None:
            self.load()

        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self.save()
