"""Aria2 option type definitions and conversion utilities.

This module provides type conversion between aria2's string-based RPC format
and Python native types for better ergonomics.
"""

from typing import Any

# Aria2 options that are boolean values
BOOLEAN_OPTIONS: set[str] = {
    # Basic options
    "check-integrity",
    "continue",
    "dry-run",
    # HTTP/FTP/SFTP options
    "checksum",
    "remote-time",
    "reuse-uri",
    "conditional-get",
    "http-accept-gzip",
    "http-auth-challenge",
    "http-no-cache",
    "parameterized-uri",
    # FTP/SFTP options
    "ftp-pasv",
    # BitTorrent options
    "bt-enable-lpd",
    "bt-hash-check-seed",
    "bt-lpd-interface",
    "bt-require-crypto",
    "bt-save-metadata",
    "bt-seed-unverified",
    "enable-dht",
    "enable-dht6",
    "enable-peer-exchange",
    "follow-torrent",
    "bt-detach-seed-only",
    # Metalink options
    "follow-metalink",
    "metalink-enable-unique-protocol",
    # RPC options
    "pause-metadata",
    "rpc-save-upload-metadata",
    # Advanced options
    "allow-overwrite",
    "allow-piece-length-change",
    "always-resume",
    "async-dns",
    "auto-file-renaming",
    "daemon",
    "deferred-input",
    "enable-mmap",
    "force-save",
    "hash-check-only",
    "human-readable",
    "keep-unfinished-download-result",
    "realtime-chunk-checksum",
    "remove-control-file",
    "save-not-found",
    "save-session-interval",
    "truncate-console-readout",
}


# Aria2 options that are integer values
INTEGER_OPTIONS: set[str] = {
    # Basic options
    "max-concurrent-downloads",
    # HTTP/FTP/SFTP options
    "connect-timeout",
    "timeout",
    "max-tries",
    "retry-wait",
    "max-file-not-found",
    "max-connection-per-server",
    "split",
    "min-split-size",
    "lowest-speed-limit",
    # HTTP options
    "http-proxy-port",
    "https-proxy-port",
    # FTP/SFTP options
    "ftp-proxy-port",
    "ssh-host-key-md-type",
    # BitTorrent options
    "bt-max-open-files",
    "bt-max-peers",
    "bt-min-crypto-level",
    "bt-request-peer-speed-limit",
    "bt-stop-timeout",
    "bt-tracker-connect-timeout",
    "bt-tracker-interval",
    "bt-tracker-timeout",
    "dht-listen-port",
    "dht-message-timeout",
    "listen-port",
    "peer-id-prefix-length",
    # Metalink options
    "metalink-preferred-protocol-priority",
    # Advanced options
    "auto-save-interval",
    "disk-cache",
    "download-result",
    "max-download-limit",
    "max-upload-limit",
    "max-overall-download-limit",
    "max-overall-upload-limit",
    "max-resume-failure-tries",
    "min-tls-version",
    "piece-length",
    "save-session-interval-seconds",
    "seed-ratio-ratio",
    "seed-time",
    "stop-with-process",
    "stream-piece-selector-size",
}


def parse_option_value(key: str, value: Any) -> Any:
    """Parse aria2 option value from string to appropriate Python type.

    Args:
        key: Option key name
        value: Value from aria2 (typically string)

    Returns:
        Value converted to appropriate Python type
    """
    if value is None or value == "":
        return None

    # Boolean options
    if key in BOOLEAN_OPTIONS:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)

    # Integer options
    if key in INTEGER_OPTIONS:
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    # Default: return as string
    return value


def format_option_value(key: str, value: Any) -> str:
    """Format Python value to aria2 string format.

    Args:
        key: Option key name
        value: Python value

    Returns:
        String representation for aria2 RPC
    """
    if value is None or value == "":
        return ""

    # Boolean options
    if key in BOOLEAN_OPTIONS:
        return "true" if value else "false"

    # All other values convert to string
    return str(value)


def parse_options_dict(options: dict[str, Any]) -> dict[str, Any]:
    """Parse all options in a dictionary.

    Args:
        options: Dictionary from aria2 (string values)

    Returns:
        Dictionary with properly typed values
    """
    return {key: parse_option_value(key, value) for key, value in options.items()}


def format_options_dict(options: dict[str, Any]) -> dict[str, str]:
    """Format all options in a dictionary to aria2 format.

    Args:
        options: Dictionary with Python native types

    Returns:
        Dictionary with string values for aria2 RPC
    """
    return {key: format_option_value(key, value) for key, value in options.items()}
