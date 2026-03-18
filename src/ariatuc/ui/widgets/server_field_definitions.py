"""Server configuration field definitions.

This module defines the configuration fields for aria2 RPC server management.
"""

from ariatuc.ui.widgets.form_widget import ConfigField, FieldType

# Server basic configuration fields
SERVER_FIELDS = [
    ConfigField(
        key="name",
        label="Server Name",
        type=FieldType.INPUT,
        help_text="Friendly name for this server",
        placeholder="My Aria2 Server",
        required=True,
        editable=True,
    ),
    ConfigField(
        key="url",
        label="RPC URL",
        type=FieldType.INPUT,
        help_text="aria2 RPC server URL (e.g., http://localhost:6800/jsonrpc)",
        placeholder="http://localhost:6800/jsonrpc",
        required=True,
        editable=True,
    ),
    ConfigField(
        key="protocol",
        label="Protocol",
        type=FieldType.SELECT,
        help_text="RPC protocol type (auto-detect or manual)",
        options=[
            ("auto", "Auto Detect"),
            ("http", "HTTP"),
            ("websocket", "WebSocket"),
        ],
        default="auto",
        editable=True,
    ),
    ConfigField(
        key="secret",
        label="RPC Secret",
        type=FieldType.INPUT,
        help_text="Secret token (recommended, matches --rpc-secret)",
        placeholder="",
        required=False,
        editable=True,
    ),
    ConfigField(
        key="username",
        label="Username (Deprecated)",
        type=FieldType.INPUT,
        help_text="Legacy username authentication (not recommended)",
        placeholder="",
        required=False,
        editable=True,
    ),
    ConfigField(
        key="password",
        label="Password (Deprecated)",
        type=FieldType.INPUT,
        help_text="Legacy password authentication (not recommended)",
        placeholder="",
        required=False,
        editable=True,
    ),
    ConfigField(
        key="timeout",
        label="Connection Timeout (seconds)",
        type=FieldType.NUMBER,
        help_text="Request timeout in seconds",
        default="30",
        editable=True,
    ),
]
