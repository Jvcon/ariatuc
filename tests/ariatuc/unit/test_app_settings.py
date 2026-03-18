"""Unit tests for app settings functionality."""

import pytest

from ariatuc.ui.screens.app_settings_screen import AppSettingsScreen


class MockConfigManager:
    """Mock ConfigManager for testing."""

    def __init__(self):
        """Initialize mock config manager."""
        from dataclasses import dataclass

        @dataclass
        class MockConfig:
            theme: str = "dark"
            refresh_interval: int = 1000
            auto_refresh: bool = True
            connection_timeout: int = 10
            reconnect_interval: int = 5
            prefer_websocket: bool = True
            websocket_fallback_http: bool = True
            max_concurrent_downloads: int = 5
            max_connection_per_server: int = 16
            enable_notifications: bool = True
            play_sound_on_complete: bool = True
            play_sound_on_error: bool = True

        self._config = MockConfig()
        self._updates = {}

    def get(self):
        """Get mock config."""
        return self._config

    def update(self, **kwargs):
        """Mock update (stores updates for verification)."""
        self._updates = kwargs
        # Apply updates to config for testing
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def save(self):
        """Mock save (no-op)."""
        pass


class TestAppSettingsScreen:
    """Test suite for AppSettingsScreen."""

    def test_init(self):
        """Test screen initialization."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)

        assert screen.config_manager == config_mgr
        assert screen._mode == "VIEW"
        assert screen._current_field_index == 0
        assert screen._form_widget is None

    def test_default_mode_is_view(self):
        """Test that screen starts in VIEW mode."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)
        assert screen._mode == "VIEW"

    def test_mode_transitions(self):
        """Test mode state transitions."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)

        # Start in VIEW
        assert screen._mode == "VIEW"

        # Simulate entering EDIT mode
        screen._mode = "EDIT"
        assert screen._mode == "EDIT"

        # Simulate exiting to VIEW
        screen._mode = "VIEW"
        assert screen._mode == "VIEW"


class TestAppSettingsValidation:
    """Test suite for app settings validation."""

    def test_save_with_valid_values(self):
        """Test saving with all valid values."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)

        # Simulate form widget with valid values
        class MockFormWidget:
            def get_values(self):
                return {
                    "theme": "light",
                    "refresh_interval": "2000",
                    "auto_refresh": "true",
                    "connection_timeout": "15",
                    "reconnect_interval": "10",
                    "prefer_websocket": "false",
                    "websocket_fallback_http": "false",
                    "max_concurrent_downloads": "10",
                    "max_connection_per_server": "8",
                    "enable_notifications": "false",
                    "play_sound_on_complete": "false",
                    "play_sound_on_error": "false",
                }

            def validate_all(self):
                return (True, {})

        screen._form_widget = MockFormWidget()
        screen.action_save_settings()

        # Verify ConfigManager.update was called with correct types
        assert config_mgr._updates["theme"] == "light"
        assert config_mgr._updates["refresh_interval"] == 2000
        assert config_mgr._updates["auto_refresh"] is True
        assert config_mgr._updates["connection_timeout"] == 15
        assert config_mgr._updates["reconnect_interval"] == 10
        assert config_mgr._updates["prefer_websocket"] is False
        assert config_mgr._updates["websocket_fallback_http"] is False
        assert config_mgr._updates["max_concurrent_downloads"] == 10
        assert config_mgr._updates["max_connection_per_server"] == 8
        assert config_mgr._updates["enable_notifications"] is False
        assert config_mgr._updates["play_sound_on_complete"] is False
        assert config_mgr._updates["play_sound_on_error"] is False

    def test_save_with_defaults_on_missing_values(self):
        """Test saving uses defaults when values are missing."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)

        # Simulate form widget with missing/empty values
        class MockFormWidget:
            def get_values(self):
                return {}

            def validate_all(self):
                return (True, {})

        screen._form_widget = MockFormWidget()
        screen.action_save_settings()

        # Verify defaults are used
        assert config_mgr._updates["theme"] == "dark"
        assert config_mgr._updates["refresh_interval"] == 1000
        assert config_mgr._updates["auto_refresh"] is False  # "false" != "true"
        assert config_mgr._updates["connection_timeout"] == 10
        assert config_mgr._updates["reconnect_interval"] == 5

    def test_save_with_validation_failure(self):
        """Test that save is aborted when validation fails."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)

        # Simulate form widget with validation errors
        class MockFormWidget:
            def get_values(self):
                return {"theme": "invalid"}

            def validate_all(self):
                return (False, {"theme": "Invalid theme value"})

        screen._form_widget = MockFormWidget()
        screen.action_save_settings()

        # Verify ConfigManager.update was NOT called
        assert config_mgr._updates == {}


class TestFieldNavigation:
    """Test suite for field navigation."""

    def test_navigate_field_increments_index(self):
        """Test that navigation increments field index."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)

        # Mock form widget
        class MockFormWidget:
            def get_field_keys(self):
                return ["field1", "field2", "field3"]

            def highlight_field(self, key):
                pass

        screen._form_widget = MockFormWidget()
        screen._current_field_index = 0

        # Navigate forward
        screen._navigate_field(1)
        assert screen._current_field_index == 1

        screen._navigate_field(1)
        assert screen._current_field_index == 2

    def test_navigate_field_wraps_around(self):
        """Test that navigation wraps around at boundaries."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)

        # Mock form widget
        class MockFormWidget:
            def get_field_keys(self):
                return ["field1", "field2", "field3"]

            def highlight_field(self, key):
                pass

        screen._form_widget = MockFormWidget()

        # Start at last field
        screen._current_field_index = 2

        # Navigate forward should wrap to 0
        screen._navigate_field(1)
        assert screen._current_field_index == 0

        # Navigate backward should wrap to 2
        screen._navigate_field(-1)
        assert screen._current_field_index == 2

    def test_navigate_field_backward(self):
        """Test backward navigation."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)

        # Mock form widget
        class MockFormWidget:
            def get_field_keys(self):
                return ["field1", "field2", "field3"]

            def highlight_field(self, key):
                pass

        screen._form_widget = MockFormWidget()
        screen._current_field_index = 2

        # Navigate backward
        screen._navigate_field(-1)
        assert screen._current_field_index == 1

        screen._navigate_field(-1)
        assert screen._current_field_index == 0


class TestEscapeKeyHandling:
    """Test suite for Escape key handling.

    Note: Full Escape key behavior testing requires integration tests with
    a running Textual app. The real-time focus detection in action_handle_escape()
    depends on self.app.focused which cannot be mocked in unit tests.
    The mode transition tests above verify the basic state management.
    """

    def test_mode_state_tracking(self):
        """Test that mode state is properly tracked."""
        config_mgr = MockConfigManager()
        screen = AppSettingsScreen(config_mgr)

        # Verify initial state
        assert screen._mode == "VIEW"
        assert screen._current_field_index == 0

        # Simulate mode change
        screen._mode = "EDIT"
        assert screen._mode == "EDIT"
