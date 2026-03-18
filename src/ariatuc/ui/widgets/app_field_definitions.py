"""Application settings field definitions.

This module defines the configuration fields for ariatuc application settings.
"""

from ariatuc.ui.widgets.form_widget import ConfigField, FieldType

# Application settings fields
APP_FIELDS = [
    # Appearance
    ConfigField(
        key="theme",
        label="Theme",
        type=FieldType.SELECT,
        help_text="Application color theme",
        options=[
            ("default", "Default"),
            ("dark", "Dark"),
            ("light", "Light"),
        ],
        default="dark",
        editable=True,
    ),
    # Updates
    ConfigField(
        key="refresh_interval",
        label="Refresh Interval (ms)",
        type=FieldType.NUMBER,
        help_text="Download status refresh interval in milliseconds",
        default="1000",
        editable=True,
    ),
    ConfigField(
        key="auto_refresh",
        label="Auto Refresh",
        type=FieldType.SELECT,
        help_text="Automatically refresh download list",
        options=[
            ("true", "Enabled"),
            ("false", "Disabled"),
        ],
        default="true",
        editable=True,
    ),
    # Connection
    ConfigField(
        key="connection_timeout",
        label="Connection Timeout (s)",
        type=FieldType.NUMBER,
        help_text="RPC connection timeout in seconds",
        default="10",
        editable=True,
    ),
    ConfigField(
        key="reconnect_interval",
        label="Reconnect Interval (s)",
        type=FieldType.NUMBER,
        help_text="Reconnection interval in seconds",
        default="5",
        editable=True,
    ),
    # WebSocket
    ConfigField(
        key="prefer_websocket",
        label="Prefer WebSocket",
        type=FieldType.SELECT,
        help_text="Prefer WebSocket over HTTP when available",
        options=[
            ("true", "Enabled"),
            ("false", "Disabled"),
        ],
        default="true",
        editable=True,
    ),
    ConfigField(
        key="websocket_fallback_http",
        label="WebSocket Fallback to HTTP",
        type=FieldType.SELECT,
        help_text="Auto fallback to HTTP if WebSocket fails",
        options=[
            ("true", "Enabled"),
            ("false", "Disabled"),
        ],
        default="true",
        editable=True,
    ),
    # Downloads
    ConfigField(
        key="max_concurrent_downloads",
        label="Max Concurrent Downloads",
        type=FieldType.NUMBER,
        help_text="Maximum number of concurrent downloads",
        default="5",
        editable=True,
    ),
    ConfigField(
        key="max_connection_per_server",
        label="Max Connections Per Server",
        type=FieldType.NUMBER,
        help_text="Maximum connections per server",
        default="16",
        editable=True,
    ),
    # Notifications
    ConfigField(
        key="enable_notifications",
        label="Enable Notifications",
        type=FieldType.SELECT,
        help_text="Show notifications for download events",
        options=[
            ("true", "Enabled"),
            ("false", "Disabled"),
        ],
        default="true",
        editable=True,
    ),
    ConfigField(
        key="play_sound_on_complete",
        label="Sound on Complete",
        type=FieldType.SELECT,
        help_text="Play sound when download completes",
        options=[
            ("true", "Enabled"),
            ("false", "Disabled"),
        ],
        default="true",
        editable=True,
    ),
    ConfigField(
        key="play_sound_on_error",
        label="Sound on Error",
        type=FieldType.SELECT,
        help_text="Play sound on download errors",
        options=[
            ("true", "Enabled"),
            ("false", "Disabled"),
        ],
        default="true",
        editable=True,
    ),
]
