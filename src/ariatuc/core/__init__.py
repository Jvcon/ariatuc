"""Core business logic.

This module contains the core managers and service layer for the ariatuc application:
- ConfigManager: Application configuration management
- RPCManager: Multiple aria2 RPC server management
- DownloadManager: Download state management
- EventManager: WebSocket event notification handling
- LocalProcessManager: Local aria2c process lifecycle management
- Aria2Service: Main service layer coordinating all managers
"""

from ariatuc.core.config_manager import AppConfig, ConfigManager
from ariatuc.core.download_manager import Download, DownloadManager, DownloadStatus
from ariatuc.core.event_manager import EventManager, NotificationType
from ariatuc.core.local_process_manager import (
    LocalProcessManager,
    ProcessError,
    ProcessInfo,
    ProcessState,
)
from ariatuc.core.rpc_manager import (
    ConnectionProtocol,
    ConnectionState,
    RPCManager,
    ServerConfig,
    ServerState,
)
from ariatuc.core.service import (
    Aria2Service,
    ConnectionError,
    DownloadOperationError,
    DownloadOptions,
    ServiceError,
)

__all__ = [
    # Config management
    "ConfigManager",
    "AppConfig",
    # RPC management
    "RPCManager",
    "ServerConfig",
    "ServerState",
    "ConnectionProtocol",
    "ConnectionState",
    # Download management
    "DownloadManager",
    "Download",
    "DownloadStatus",
    # Event management
    "EventManager",
    "NotificationType",
    # Local process management
    "LocalProcessManager",
    "ProcessInfo",
    "ProcessState",
    "ProcessError",
    # Service layer
    "Aria2Service",
    "DownloadOptions",
    "ServiceError",
    "ConnectionError",
    "DownloadOperationError",
]
