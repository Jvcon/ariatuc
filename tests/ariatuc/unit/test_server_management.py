"""Unit tests for server management functionality."""

import pytest

from ariatuc.ui.screens.server_management_screen import ServerManagementScreen


class MockConfigManager:
    """Mock ConfigManager for testing."""

    def __init__(self):
        """Initialize mock config manager."""
        from dataclasses import dataclass

        @dataclass
        class MockConfig:
            servers: list = None

            def __post_init__(self):
                if self.servers is None:
                    self.servers = []

        self._config = MockConfig()

    def get(self):
        """Get mock config."""
        return self._config

    def save(self):
        """Mock save (no-op)."""
        pass


class MockService:
    """Mock Aria2Service for testing."""

    def __init__(self):
        """Initialize mock service."""
        self.servers = {}
        self.current_server = None

        # Mock managers
        self.rpc_mgr = MockRPCManager()
        self.config_mgr = MockConfigManager()

    def add_server(self, name: str, url: str, secret: str | None = None) -> None:
        """Mock add_server."""
        self.servers[name] = {"url": url, "secret": secret}
        self.rpc_mgr.add_server(name, url, secret)

    def remove_server(self, name: str) -> None:
        """Mock remove_server."""
        if name in self.servers:
            del self.servers[name]
        self.rpc_mgr.remove_server(name)

    async def switch_server(self, name: str) -> bool:
        """Mock switch_server."""
        if name in self.servers:
            self.current_server = name
            self.rpc_mgr.switch_server(name)
            return True
        return False


class MockRPCManager:
    """Mock RPCManager for testing."""

    def __init__(self):
        """Initialize mock RPC manager."""
        self.servers = {}
        self.current_server = None
        self._states = {}

    def add_server(self, name: str, url: str, secret: str | None = None) -> None:
        """Mock add_server."""
        from ariatuc.core.rpc_manager import ServerConfig, ServerState

        self.servers[name] = ServerConfig(name=name, url=url, secret=secret)
        self._states[name] = ServerState()

    def remove_server(self, name: str) -> None:
        """Mock remove_server."""
        if name in self.servers:
            del self.servers[name]
            del self._states[name]

    def switch_server(self, name: str) -> bool:
        """Mock switch_server."""
        if name in self.servers:
            self.current_server = name
            return True
        return False

    def get_server_state(self, name: str | None = None):
        """Mock get_server_state."""
        server_name = name or self.current_server
        if server_name:
            return self._states.get(server_name)
        return None


class TestServerManagementScreen:
    """Test suite for ServerManagementScreen."""

    def test_init(self):
        """Test screen initialization."""
        service = MockService()
        screen = ServerManagementScreen(service)

        assert screen.service == service
        assert screen._mode == "VIEW"
        assert screen._current_field_index == 0

    def test_validate_server_config_valid_http(self):
        """Test validation with valid HTTP URL."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = [{"name": "Server 1", "url": "http://localhost:6800/jsonrpc"}]

        values = {
            "name": "Test Server",
            "url": "http://localhost:6800/jsonrpc",
            "secret": "",
        }

        is_valid, error = screen._validate_server_config(values, 0)
        assert is_valid
        assert error is None

    def test_validate_server_config_valid_websocket(self):
        """Test validation with valid WebSocket URL."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = []

        values = {
            "name": "WS Server",
            "url": "ws://localhost:6800/jsonrpc",
            "secret": "mytoken",
        }

        is_valid, error = screen._validate_server_config(values, 0)
        assert is_valid
        assert error is None

    def test_validate_server_config_invalid_scheme(self):
        """Test validation with invalid URL scheme."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = []

        values = {
            "name": "Bad Server",
            "url": "ftp://localhost:6800/jsonrpc",
            "secret": "",
        }

        is_valid, error = screen._validate_server_config(values, 0)
        assert not is_valid
        assert "http://, https://, ws://, or wss://" in error

    def test_validate_server_config_missing_url(self):
        """Test validation with missing URL."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = []

        values = {
            "name": "No URL Server",
            "url": "",
            "secret": "",
        }

        is_valid, error = screen._validate_server_config(values, 0)
        assert not is_valid
        assert "URL is required" in error

    def test_validate_server_config_missing_name(self):
        """Test validation with missing server name."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = []

        values = {
            "name": "",
            "url": "http://localhost:6800/jsonrpc",
            "secret": "",
        }

        is_valid, error = screen._validate_server_config(values, 0)
        assert not is_valid
        assert "Server name is required" in error

    def test_validate_server_config_duplicate_name(self):
        """Test validation with duplicate server name."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = [
            {"name": "Server 1", "url": "http://localhost:6800/jsonrpc"},
            {"name": "Server 2", "url": "http://localhost:6801/jsonrpc"},
        ]

        values = {
            "name": "Server 1",  # Duplicate
            "url": "http://localhost:6802/jsonrpc",
            "secret": "",
        }

        # Trying to save as Server 2 (index 1) with name "Server 1"
        is_valid, error = screen._validate_server_config(values, 1)
        assert not is_valid
        assert "already exists" in error

    def test_validate_server_config_same_name_allowed(self):
        """Test validation allows same name when editing same server."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = [
            {"name": "Server 1", "url": "http://localhost:6800/jsonrpc"},
        ]

        values = {
            "name": "Server 1",  # Same name, same index
            "url": "http://localhost:6802/jsonrpc",
            "secret": "newsecret",
        }

        # Editing Server 1 (index 0) and keeping same name should be valid
        is_valid, error = screen._validate_server_config(values, 0)
        assert is_valid
        assert error is None

    def test_validate_server_config_invalid_url_format(self):
        """Test validation with malformed URL."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = []

        values = {
            "name": "Bad URL",
            "url": "http://",  # Missing hostname
            "secret": "",
        }

        is_valid, error = screen._validate_server_config(values, 0)
        assert not is_valid
        assert "Invalid URL format" in error


class TestViewEditModeInteraction:
    """Test suite for VIEW/EDIT mode interaction."""

    def test_default_mode_is_view(self):
        """Test that screen starts in VIEW mode."""
        service = MockService()
        screen = ServerManagementScreen(service)
        assert screen._mode == "VIEW"

    def test_mode_transitions(self):
        """Test mode state transitions."""
        service = MockService()
        screen = ServerManagementScreen(service)

        # Start in VIEW
        assert screen._mode == "VIEW"

        # Simulate entering EDIT mode
        screen._mode = "EDIT"
        assert screen._mode == "EDIT"

        # Simulate exiting to VIEW
        screen._mode = "VIEW"
        assert screen._mode == "VIEW"


class TestServerOrdering:
    """Test suite for server ordering functionality."""

    def test_move_server_up(self):
        """Test moving server up in the list."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = [
            {"name": "Server 1", "url": "http://localhost:6801/jsonrpc"},
            {"name": "Server 2", "url": "http://localhost:6802/jsonrpc"},
            {"name": "Server 3", "url": "http://localhost:6803/jsonrpc"},
        ]
        screen._current_server_index = 1  # Select Server 2

        # Move Server 2 up (should swap with Server 1)
        screen.action_move_server_up()

        assert screen._servers[0]["name"] == "Server 2"
        assert screen._servers[1]["name"] == "Server 1"
        assert screen._servers[2]["name"] == "Server 3"
        assert screen._current_server_index == 0  # Index should follow the server

    def test_move_server_down(self):
        """Test moving server down in the list."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = [
            {"name": "Server 1", "url": "http://localhost:6801/jsonrpc"},
            {"name": "Server 2", "url": "http://localhost:6802/jsonrpc"},
            {"name": "Server 3", "url": "http://localhost:6803/jsonrpc"},
        ]
        screen._current_server_index = 1  # Select Server 2

        # Move Server 2 down (should swap with Server 3)
        screen.action_move_server_down()

        assert screen._servers[0]["name"] == "Server 1"
        assert screen._servers[1]["name"] == "Server 3"
        assert screen._servers[2]["name"] == "Server 2"
        assert screen._current_server_index == 2  # Index should follow the server

    def test_move_server_up_at_top(self):
        """Test moving server up when already at top."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = [
            {"name": "Server 1", "url": "http://localhost:6801/jsonrpc"},
            {"name": "Server 2", "url": "http://localhost:6802/jsonrpc"},
        ]
        screen._current_server_index = 0  # Already at top

        # Try to move up (should not change)
        screen.action_move_server_up()

        assert screen._servers[0]["name"] == "Server 1"
        assert screen._servers[1]["name"] == "Server 2"
        assert screen._current_server_index == 0

    def test_move_server_down_at_bottom(self):
        """Test moving server down when already at bottom."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = [
            {"name": "Server 1", "url": "http://localhost:6801/jsonrpc"},
            {"name": "Server 2", "url": "http://localhost:6802/jsonrpc"},
        ]
        screen._current_server_index = 1  # Already at bottom

        # Try to move down (should not change)
        screen.action_move_server_down()

        assert screen._servers[0]["name"] == "Server 1"
        assert screen._servers[1]["name"] == "Server 2"
        assert screen._current_server_index == 1

    def test_move_single_server(self):
        """Test moving when only one server exists."""
        service = MockService()
        screen = ServerManagementScreen(service)
        screen._servers = [
            {"name": "Server 1", "url": "http://localhost:6801/jsonrpc"},
        ]
        screen._current_server_index = 0

        # Try to move (should do nothing)
        screen.action_move_server_up()
        assert len(screen._servers) == 1
        assert screen._servers[0]["name"] == "Server 1"

        screen.action_move_server_down()
        assert len(screen._servers) == 1
        assert screen._servers[0]["name"] == "Server 1"
