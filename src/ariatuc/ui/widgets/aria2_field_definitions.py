"""Aria2 configuration field definitions matching AriaNg structure.

This module defines all aria2 global options organized by categories matching AriaNg:
- Basic: Core download settings (dir, log, max-concurrent-downloads, etc.)
- HTTP/FTP/SFTP: Common protocol options (proxy, timeout, retry, split, etc.)
- HTTP: HTTP-specific options (authentication, headers, cookies, etc.)
- FTP/SFTP: FTP and SFTP protocol options (authentication, mode, etc.)
- BitTorrent: BitTorrent protocol options (DHT, encryption, seeding, etc.)
- Metalink: Metalink protocol options (follow, preferred protocol, etc.)
- RPC: RPC server settings (port, security, etc.)
- Advanced: Advanced options (performance, logging, allocation, etc.)

Default values and order match AriaNg's aria2Options.js configuration.
"""

from ariatuc.ui.widgets.field_schema import ConfigField, FieldType

# =============================================================================
# Basic Options (Core download settings)
# =============================================================================
ARIA2_FIELDS_BASIC = [
    ConfigField(
        key="dir",
        label="Download Directory",
        type=FieldType.INPUT,
        default="",
        required=True,
        editable=False,
        placeholder="/path/to/downloads",
        help_text="Default directory to store downloaded files (read-only at runtime)",
        section="Basic Settings",
    ),
    ConfigField(
        key="log",
        label="Log File",
        type=FieldType.INPUT,
        default="",
        editable=False,
        placeholder="/path/to/aria2.log",
        help_text="File path to write log output (read-only at runtime)",
        section="Basic Settings",
    ),
    ConfigField(
        key="max-concurrent-downloads",
        label="Max Concurrent Downloads",
        type=FieldType.NUMBER,
        default=5,
        min_value=1,
        editable=False,
        unit="downloads",
        help_text="Maximum number of parallel downloads (read-only at runtime)",
        section="Basic Settings",
    ),
    ConfigField(
        key="check-integrity",
        label="Check Integrity",
        type=FieldType.SWITCH,
        default=False,
        editable=False,
        help_text="Check file integrity by validating piece hashes (read-only at runtime)",
        section="Basic Settings",
    ),
    ConfigField(
        key="continue",
        label="Continue Downloads",
        type=FieldType.SWITCH,
        default=True,
        editable=False,
        help_text="Continue downloading partially downloaded file (read-only at runtime)",
        section="Basic Settings",
    ),
]

# =============================================================================
# HTTP/FTP/SFTP Options (Common protocol options)
# =============================================================================
ARIA2_FIELDS_HTTP_FTP_SFTP = [
    # Proxy Settings
    ConfigField(
        key="all-proxy",
        label="All Protocols Proxy",
        type=FieldType.INPUT,
        default="",
        placeholder="http://proxy.example.com:8080",
        help_text="Proxy server for all protocols",
        section="General Proxy",
    ),
    ConfigField(
        key="all-proxy-user",
        label="All Proxy Username",
        type=FieldType.INPUT,
        default="",
        placeholder="username",
        help_text="Username for all-proxy authentication",
        section="General Proxy",
    ),
    ConfigField(
        key="all-proxy-passwd",
        label="All Proxy Password",
        type=FieldType.INPUT,
        default="",
        placeholder="password",
        help_text="Password for all-proxy authentication",
        section="General Proxy",
    ),
    ConfigField(
        key="no-proxy",
        label="No Proxy Domains",
        type=FieldType.TEXTAREA,
        default="",
        placeholder="localhost, 127.0.0.1, .example.com",
        help_text="Comma-separated list of domains to bypass proxy",
        section="General Proxy",
    ),
    ConfigField(
        key="proxy-method",
        label="Proxy Method",
        type=FieldType.SELECT,
        default="get",
        options=[
            ("get", "GET"),
            ("tunnel", "CONNECT Tunnel"),
        ],
        help_text="HTTP proxy method to use",
        section="General Proxy",
    ),
    # Connection & Retry Settings
    ConfigField(
        key="connect-timeout",
        label="Connect Timeout",
        type=FieldType.NUMBER,
        default=60,
        min_value=1,
        max_value=600,
        unit="seconds",
        help_text="Connection establishment timeout",
        section="Connection & Retry",
    ),
    ConfigField(
        key="timeout",
        label="Request Timeout",
        type=FieldType.NUMBER,
        default=60,
        min_value=1,
        max_value=600,
        unit="seconds",
        help_text="Timeout for general requests",
        section="Connection & Retry",
    ),
    ConfigField(
        key="max-tries",
        label="Max Retry Attempts",
        type=FieldType.NUMBER,
        default=5,
        min_value=0,
        unit="tries",
        help_text="Maximum retry attempts (0 = unlimited)",
        section="Connection & Retry",
    ),
    ConfigField(
        key="retry-wait",
        label="Retry Wait Time",
        type=FieldType.NUMBER,
        default=0,
        min_value=0,
        max_value=600,
        unit="seconds",
        help_text="Wait time before retry (0 = no wait)",
        section="Connection & Retry",
    ),
    ConfigField(
        key="max-file-not-found",
        label="Max File Not Found",
        type=FieldType.NUMBER,
        default=0,
        min_value=0,
        unit="tries",
        help_text="Maximum file not found errors before giving up (0 = unlimited)",
        section="Connection & Retry",
    ),
    # Download Settings
    ConfigField(
        key="max-connection-per-server",
        label="Max Connections Per Server",
        type=FieldType.NUMBER,
        default=1,
        min_value=1,
        max_value=16,
        unit="connections",
        help_text="Maximum connections to one server for each download",
        section="Download Settings",
    ),
    ConfigField(
        key="split",
        label="Split Downloads",
        type=FieldType.NUMBER,
        default=5,
        min_value=1,
        unit="pieces",
        help_text="Number of connections used for each download",
        section="Download Settings",
    ),
    ConfigField(
        key="min-split-size",
        label="Min Split Size",
        type=FieldType.INPUT,
        default="20M",
        placeholder="20M",
        help_text="Minimum size required before splitting (e.g., 10M, 1G)",
        section="Download Settings",
    ),
    ConfigField(
        key="lowest-speed-limit",
        label="Lowest Speed Limit",
        type=FieldType.INPUT,
        default="0",
        placeholder="0",
        unit="B/s",
        help_text="Close connection if download speed falls below this (0 = disabled)",
        section="Download Settings",
    ),
    ConfigField(
        key="stream-piece-selector",
        label="Stream Piece Selector",
        type=FieldType.SELECT,
        default="default",
        options=[
            ("default", "Default"),
            ("inorder", "Sequential"),
            ("random", "Random"),
            ("geom", "Geometric"),
        ],
        help_text="Piece selection algorithm for streaming",
        section="Download Settings",
    ),
    ConfigField(
        key="uri-selector",
        label="URI Selector",
        type=FieldType.SELECT,
        default="feedback",
        options=[
            ("inorder", "In Order"),
            ("feedback", "Feedback (adaptive)"),
            ("adaptive", "Adaptive"),
        ],
        help_text="URI selection algorithm",
        section="Download Settings",
    ),
    # Advanced Options
    ConfigField(
        key="checksum",
        label="Checksum",
        type=FieldType.INPUT,
        default="",
        placeholder="sha-256=...",
        help_text="Checksum to verify download (format: type=digest)",
        section="Verification",
    ),
    ConfigField(
        key="dry-run",
        label="Dry Run",
        type=FieldType.SWITCH,
        default=False,
        help_text="Test download without writing to disk",
        section="Advanced",
    ),
    ConfigField(
        key="remote-time",
        label="Remote Time",
        type=FieldType.SWITCH,
        default=False,
        help_text="Retrieve timestamp from remote server",
        section="Advanced",
    ),
    ConfigField(
        key="reuse-uri",
        label="Reuse URI",
        type=FieldType.SWITCH,
        default=True,
        help_text="Reuse URIs already used in the current download",
        section="Advanced",
    ),
]

# =============================================================================
# HTTP-Specific Options
# =============================================================================
ARIA2_FIELDS_HTTP = [
    # Authentication
    ConfigField(
        key="http-user",
        label="HTTP Username",
        type=FieldType.INPUT,
        default="",
        placeholder="username",
        help_text="Username for HTTP basic authentication",
        section="HTTP Authentication",
    ),
    ConfigField(
        key="http-passwd",
        label="HTTP Password",
        type=FieldType.INPUT,
        default="",
        placeholder="password",
        help_text="Password for HTTP basic authentication",
        section="HTTP Authentication",
    ),
    ConfigField(
        key="http-auth-challenge",
        label="HTTP Auth Challenge",
        type=FieldType.SWITCH,
        default=False,
        help_text="Send authorization header only when requested by server",
        section="HTTP Authentication",
    ),
    # Proxy
    ConfigField(
        key="http-proxy",
        label="HTTP Proxy",
        type=FieldType.INPUT,
        default="",
        placeholder="http://proxy.example.com:8080",
        help_text="HTTP proxy server URL",
        section="HTTP Proxy",
    ),
    ConfigField(
        key="http-proxy-user",
        label="HTTP Proxy Username",
        type=FieldType.INPUT,
        default="",
        placeholder="username",
        help_text="Username for HTTP proxy authentication",
        section="HTTP Proxy",
    ),
    ConfigField(
        key="http-proxy-passwd",
        label="HTTP Proxy Password",
        type=FieldType.INPUT,
        default="",
        placeholder="password",
        help_text="Password for HTTP proxy authentication",
        section="HTTP Proxy",
    ),
    ConfigField(
        key="https-proxy",
        label="HTTPS Proxy",
        type=FieldType.INPUT,
        default="",
        placeholder="http://proxy.example.com:8080",
        help_text="HTTPS proxy server URL",
        section="HTTP Proxy",
    ),
    ConfigField(
        key="https-proxy-user",
        label="HTTPS Proxy Username",
        type=FieldType.INPUT,
        default="",
        placeholder="username",
        help_text="Username for HTTPS proxy authentication",
        section="HTTP Proxy",
    ),
    ConfigField(
        key="https-proxy-passwd",
        label="HTTPS Proxy Password",
        type=FieldType.INPUT,
        default="",
        placeholder="password",
        help_text="Password for HTTPS proxy authentication",
        section="HTTP Proxy",
    ),
    # Options
    ConfigField(
        key="http-accept-gzip",
        label="Accept Gzip",
        type=FieldType.SWITCH,
        default=False,
        help_text="Accept gzip compression in HTTP responses",
        section="HTTP Options",
    ),
    ConfigField(
        key="http-no-cache",
        label="HTTP No Cache",
        type=FieldType.SWITCH,
        default=False,
        help_text="Send Cache-Control: no-cache and Pragma: no-cache headers",
        section="HTTP Options",
    ),
    ConfigField(
        key="enable-http-keep-alive",
        label="HTTP Keep-Alive",
        type=FieldType.SWITCH,
        default=True,
        help_text="Use HTTP/1.1 persistent connections",
        section="HTTP Options",
    ),
    ConfigField(
        key="enable-http-pipelining",
        label="HTTP Pipelining",
        type=FieldType.SWITCH,
        default=False,
        help_text="Enable HTTP pipelining (experimental)",
        section="HTTP Options",
    ),
    ConfigField(
        key="use-head",
        label="Use HEAD Method",
        type=FieldType.SWITCH,
        default=False,
        help_text="Use HTTP HEAD method for first request",
        section="HTTP Options",
    ),
    # Headers & Cookies
    ConfigField(
        key="header",
        label="Custom Headers",
        type=FieldType.TEXTAREA,
        default="",
        placeholder="Header1: value1\nHeader2: value2",
        help_text="Custom HTTP headers (one per line, format: Header: value)",
        section="Headers & Cookies",
    ),
    ConfigField(
        key="referer",
        label="Referer",
        type=FieldType.INPUT,
        default="",
        placeholder="https://example.com",
        help_text="HTTP referer header",
        section="Headers & Cookies",
    ),
    ConfigField(
        key="user-agent",
        label="User Agent",
        type=FieldType.INPUT,
        default="aria2/$VERSION",
        placeholder="Mozilla/5.0 ...",
        help_text="User agent string for HTTP(S) downloads",
        section="Headers & Cookies",
    ),
    ConfigField(
        key="save-cookies",
        label="Save Cookies To",
        type=FieldType.INPUT,
        default="",
        placeholder="/path/to/cookies.txt",
        help_text="Save cookies to file in Netscape/Mozilla format",
        section="Headers & Cookies",
    ),
]

# =============================================================================
# FTP/SFTP Options
# =============================================================================
ARIA2_FIELDS_FTP_SFTP = [
    # FTP Authentication
    ConfigField(
        key="ftp-user",
        label="FTP Username",
        type=FieldType.INPUT,
        default="anonymous",
        placeholder="username",
        help_text="Username for FTP authentication",
        section="FTP Authentication",
    ),
    ConfigField(
        key="ftp-passwd",
        label="FTP Password",
        type=FieldType.INPUT,
        default="ARIA2USER@",
        placeholder="password",
        help_text="Password for FTP authentication",
        section="FTP Authentication",
    ),
    # FTP Proxy
    ConfigField(
        key="ftp-proxy",
        label="FTP Proxy",
        type=FieldType.INPUT,
        default="",
        placeholder="http://proxy.example.com:8080",
        help_text="FTP proxy server URL",
        section="FTP Proxy",
    ),
    ConfigField(
        key="ftp-proxy-user",
        label="FTP Proxy Username",
        type=FieldType.INPUT,
        default="",
        placeholder="username",
        help_text="Username for FTP proxy authentication",
        section="FTP Proxy",
    ),
    ConfigField(
        key="ftp-proxy-passwd",
        label="FTP Proxy Password",
        type=FieldType.INPUT,
        default="",
        placeholder="password",
        help_text="Password for FTP proxy authentication",
        section="FTP Proxy",
    ),
    # FTP Options
    ConfigField(
        key="ftp-pasv",
        label="FTP Passive Mode",
        type=FieldType.SWITCH,
        default=True,
        help_text="Use passive mode for FTP connections",
        section="FTP Options",
    ),
    ConfigField(
        key="ftp-type",
        label="FTP Transfer Type",
        type=FieldType.SELECT,
        default="binary",
        options=[
            ("binary", "Binary"),
            ("ascii", "ASCII"),
        ],
        help_text="FTP transfer type",
        section="FTP Options",
    ),
    ConfigField(
        key="ftp-reuse-connection",
        label="Reuse FTP Connection",
        type=FieldType.SWITCH,
        default=True,
        help_text="Reuse connection for sequential requests",
        section="FTP Options",
    ),
    # SFTP Options
    ConfigField(
        key="ssh-host-key-md",
        label="SSH Host Key MD5",
        type=FieldType.INPUT,
        default="",
        placeholder="00:11:22:33:44:55:66:77:88:99:aa:bb:cc:dd:ee:ff",
        help_text="SSH host key fingerprint (MD5) for validation",
        section="SFTP Options",
    ),
]

# =============================================================================
# BitTorrent Options
# =============================================================================
ARIA2_FIELDS_BITTORRENT = [
    # Peer Discovery
    ConfigField(
        key="bt-enable-lpd",
        label="Enable Local Peer Discovery",
        type=FieldType.SWITCH,
        default=False,
        help_text="Enable Local Peer Discovery (LPD)",
        section="Peer Discovery",
    ),
    ConfigField(
        key="enable-peer-exchange",
        label="Enable Peer Exchange",
        type=FieldType.SWITCH,
        default=True,
        help_text="Enable peer exchange extension (PEX)",
        section="Peer Discovery",
    ),
    # Tracker Settings
    ConfigField(
        key="bt-exclude-tracker",
        label="Exclude Trackers",
        type=FieldType.TEXTAREA,
        default="",
        placeholder="http://bad-tracker.example.com:8080/announce",
        help_text="Tracker URLs to exclude (comma-separated or one per line)",
        section="Trackers",
    ),
    ConfigField(
        key="bt-tracker",
        label="Additional Trackers",
        type=FieldType.TEXTAREA,
        default="",
        placeholder="http://tracker1.example.com:8080/announce\nhttp://tracker2.example.com:8080/announce",
        help_text="Additional tracker URLs (comma-separated or one per line)",
        section="Trackers",
    ),
    ConfigField(
        key="bt-tracker-connect-timeout",
        label="Tracker Connect Timeout",
        type=FieldType.NUMBER,
        default=60,
        min_value=1,
        max_value=600,
        unit="seconds",
        help_text="Connection timeout for tracker requests",
        section="Trackers",
    ),
    ConfigField(
        key="bt-tracker-timeout",
        label="Tracker Timeout",
        type=FieldType.NUMBER,
        default=60,
        min_value=1,
        max_value=600,
        unit="seconds",
        help_text="Timeout for tracker requests",
        section="Trackers",
    ),
    # Encryption
    ConfigField(
        key="bt-force-encryption",
        label="Force Encryption",
        type=FieldType.SWITCH,
        default=False,
        help_text="Require encrypted connections only",
        section="Encryption",
    ),
    ConfigField(
        key="bt-min-crypto-level",
        label="Min Encryption Level",
        type=FieldType.SELECT,
        default="plain",
        options=[
            ("plain", "Plain Text"),
            ("arc4", "ARC4 Encryption"),
        ],
        help_text="Minimum encryption level for BitTorrent",
        section="Encryption",
    ),
    ConfigField(
        key="bt-require-crypto",
        label="Require Encryption",
        type=FieldType.SWITCH,
        default=False,
        help_text="Reject legacy BitTorrent handshake (force encryption)",
        section="Encryption",
    ),
    # Peer Settings
    ConfigField(
        key="bt-max-open-files",
        label="Max Open Files",
        type=FieldType.NUMBER,
        default=100,
        min_value=1,
        unit="files",
        help_text="Maximum number of files to open in multi-file torrent",
        section="Peer Settings",
    ),
    ConfigField(
        key="bt-max-peers",
        label="Max Peers Per Torrent",
        type=FieldType.NUMBER,
        default=55,
        min_value=0,
        unit="peers",
        help_text="Maximum number of peers per torrent (0 = unlimited)",
        section="Peer Settings",
    ),
    ConfigField(
        key="bt-request-peer-speed-limit",
        label="Request Peer Speed Limit",
        type=FieldType.INPUT,
        default="50K",
        placeholder="50K",
        help_text="Only request pieces from peers faster than this speed",
        section="Peer Settings",
    ),
    # Seeding
    ConfigField(
        key="bt-hash-check-seed",
        label="Hash Check Before Seeding",
        type=FieldType.SWITCH,
        default=True,
        help_text="Check file integrity before seeding",
        section="Seeding",
    ),
    ConfigField(
        key="bt-save-metadata",
        label="Save Metadata",
        type=FieldType.SWITCH,
        default=False,
        help_text="Save metadata as .torrent file",
        section="Seeding",
    ),
    ConfigField(
        key="bt-seed-unverified",
        label="Seed Unverified",
        type=FieldType.SWITCH,
        default=False,
        help_text="Seed previously downloaded files without verification",
        section="Seeding",
    ),
    ConfigField(
        key="bt-stop-timeout",
        label="Stop Timeout",
        type=FieldType.NUMBER,
        default=0,
        min_value=0,
        unit="seconds",
        help_text="Stop BitTorrent download if speed is 0 for this duration (0 = disabled)",
        section="Seeding",
    ),
    ConfigField(
        key="seed-ratio",
        label="Seed Ratio",
        type=FieldType.NUMBER,
        default=1.0,
        min_value=0.0,
        help_text="Stop seeding when share ratio reaches this value (0 = seed forever)",
        section="Seeding",
    ),
    ConfigField(
        key="seed-time",
        label="Seed Time",
        type=FieldType.NUMBER,
        default=0,
        min_value=0,
        unit="minutes",
        help_text="Stop seeding after this many minutes (0 = seed forever)",
        section="Seeding",
    ),
    # Upload Speed
    ConfigField(
        key="max-overall-upload-limit",
        label="Global Upload Speed Limit",
        type=FieldType.INPUT,
        default="0",
        placeholder="0 (unlimited)",
        unit="B/s",
        help_text="Overall upload speed limit (0 = unlimited)",
        section="Upload Speed",
    ),
    ConfigField(
        key="max-upload-limit",
        label="Per-Upload Speed Limit",
        type=FieldType.INPUT,
        default="0",
        placeholder="0 (unlimited)",
        unit="B/s",
        help_text="Maximum upload speed per torrent (0 = unlimited)",
        section="Upload Speed",
    ),
    # Advanced
    ConfigField(
        key="follow-torrent",
        label="Follow Torrent",
        type=FieldType.SELECT,
        default="true",
        options=[
            ("true", "Always Follow"),
            ("false", "Never Follow"),
            ("mem", "Follow in Memory Only"),
        ],
        help_text="Handle torrent files found in metalink",
        section="Advanced",
    ),
]

# =============================================================================
# Metalink Options
# =============================================================================
ARIA2_FIELDS_METALINK = [
    ConfigField(
        key="follow-metalink",
        label="Follow Metalink",
        type=FieldType.SELECT,
        default="true",
        options=[
            ("true", "Always Follow"),
            ("false", "Never Follow"),
            ("mem", "Follow in Memory Only"),
        ],
        help_text="Automatically download files in metalink",
        section="Metalink Processing",
    ),
    ConfigField(
        key="metalink-preferred-protocol",
        label="Preferred Protocol",
        type=FieldType.SELECT,
        default="none",
        options=[
            ("none", "No Preference"),
            ("http", "HTTP"),
            ("https", "HTTPS"),
            ("ftp", "FTP"),
        ],
        help_text="Preferred protocol for metalink downloads",
        section="Metalink Processing",
    ),
    ConfigField(
        key="metalink-enable-unique-protocol",
        label="Unique Protocol Per Mirror",
        type=FieldType.SWITCH,
        default=True,
        help_text="Use only one protocol per mirror",
        section="Metalink Processing",
    ),
    ConfigField(
        key="metalink-language",
        label="Preferred Language",
        type=FieldType.INPUT,
        default="",
        placeholder="en-US,ja,zh-CN",
        help_text="Comma-separated list of preferred languages",
        section="Metalink Preferences",
    ),
    ConfigField(
        key="metalink-location",
        label="Preferred Location",
        type=FieldType.INPUT,
        default="",
        placeholder="us,jp,cn",
        help_text="Comma-separated list of preferred server locations",
        section="Metalink Preferences",
    ),
    ConfigField(
        key="metalink-os",
        label="Preferred OS",
        type=FieldType.INPUT,
        default="",
        placeholder="linux,windows",
        help_text="Operating system for version-specific downloads",
        section="Metalink Preferences",
    ),
    ConfigField(
        key="metalink-version",
        label="Preferred Version",
        type=FieldType.INPUT,
        default="",
        placeholder="1.0.0,2.0.0",
        help_text="Version string for version-specific downloads",
        section="Metalink Preferences",
    ),
]

# =============================================================================
# RPC Options (mostly read-only in global settings)
# =============================================================================
ARIA2_FIELDS_RPC = [
    ConfigField(
        key="pause-metadata",
        label="Pause Metadata",
        type=FieldType.SWITCH,
        default=False,
        help_text="Pause downloads created from metadata or torrent files",
        section="RPC Behavior",
    ),
    ConfigField(
        key="rpc-save-upload-metadata",
        label="Save Upload Metadata",
        type=FieldType.SWITCH,
        default=True,
        help_text="Save uploaded metadata/torrent to file in dir",
        section="RPC Behavior",
    ),
]

# =============================================================================
# Advanced Options (Speed limits, performance, logging, etc.)
# =============================================================================
ARIA2_FIELDS_ADVANCED = [
    # Speed Limits
    ConfigField(
        key="max-overall-download-limit",
        label="Global Download Speed Limit",
        type=FieldType.INPUT,
        default="0",
        placeholder="0 (unlimited)",
        unit="B/s",
        help_text="Overall download speed limit (0 = unlimited, e.g., 1M, 500K)",
        section="Speed Limits",
    ),
    ConfigField(
        key="max-download-limit",
        label="Per-Download Speed Limit",
        type=FieldType.INPUT,
        default="0",
        placeholder="0 (unlimited)",
        unit="B/s",
        help_text="Maximum download speed per download (0 = unlimited)",
        section="Speed Limits",
    ),
    # File Management
    ConfigField(
        key="allow-overwrite",
        label="Allow Overwrite",
        type=FieldType.SWITCH,
        default=False,
        help_text="Allow overwriting existing files",
        section="File Management",
    ),
    ConfigField(
        key="allow-piece-length-change",
        label="Allow Piece Length Change",
        type=FieldType.SWITCH,
        default=False,
        help_text="Allow piece length change for .aria2 control file",
        section="File Management",
    ),
    ConfigField(
        key="always-resume",
        label="Always Resume",
        type=FieldType.SWITCH,
        default=True,
        help_text="Always resume download (automatically restart downloads)",
        section="File Management",
    ),
    ConfigField(
        key="auto-file-renaming",
        label="Auto File Renaming",
        type=FieldType.SWITCH,
        default=True,
        help_text="Rename file automatically if same name already exists",
        section="File Management",
    ),
    ConfigField(
        key="conditional-get",
        label="Conditional GET",
        type=FieldType.SWITCH,
        default=False,
        help_text="Use If-Modified-Since header for resume downloads",
        section="File Management",
    ),
    ConfigField(
        key="file-allocation",
        label="File Allocation Method",
        type=FieldType.SELECT,
        default="prealloc",
        options=[
            ("none", "None"),
            ("prealloc", "Pre-allocate (recommended)"),
            ("trunc", "Truncate"),
            ("falloc", "Fallocate (fast, Linux only)"),
        ],
        help_text="File space allocation method",
        section="File Management",
    ),
    ConfigField(
        key="no-file-allocation-limit",
        label="No File Allocation Limit",
        type=FieldType.INPUT,
        default="5M",
        placeholder="5M",
        help_text="No file allocation for files smaller than this (e.g., 5M)",
        section="File Management",
    ),
    ConfigField(
        key="parameterized-uri",
        label="Parameterized URI",
        type=FieldType.SWITCH,
        default=False,
        help_text="Enable parameterized URI support",
        section="File Management",
    ),
    ConfigField(
        key="realtime-chunk-checksum",
        label="Realtime Chunk Checksum",
        type=FieldType.SWITCH,
        default=True,
        help_text="Validate chunk of data by calculating checksum while downloading",
        section="File Management",
    ),
    ConfigField(
        key="remove-control-file",
        label="Remove Control File",
        type=FieldType.SWITCH,
        default=False,
        help_text="Remove .aria2 control file on download completion",
        section="File Management",
    ),
    # Performance
    ConfigField(
        key="async-dns",
        label="Async DNS",
        type=FieldType.SWITCH,
        default=True,
        help_text="Enable asynchronous DNS resolution",
        section="Performance",
    ),
    ConfigField(
        key="enable-mmap",
        label="Enable Memory Mapping",
        type=FieldType.SWITCH,
        default=False,
        help_text="Use memory-mapped I/O for disk access",
        section="Performance",
    ),
    ConfigField(
        key="max-mmap-limit",
        label="Max Memory Map Limit",
        type=FieldType.INPUT,
        default="9223372036854775807",
        placeholder="9M (9MiB)",
        help_text="Maximum size of memory-mapped file (bytes)",
        section="Performance",
    ),
    ConfigField(
        key="optimize-concurrent-downloads",
        label="Optimize Concurrent Downloads",
        type=FieldType.SWITCH,
        default=False,
        help_text="Optimize concurrent downloads by reducing CPU and memory usage",
        section="Performance",
    ),
    ConfigField(
        key="piece-length",
        label="Piece Length",
        type=FieldType.INPUT,
        default="1M",
        placeholder="1M",
        help_text="Piece length for HTTP/FTP downloads (e.g., 1M, 2M)",
        section="Performance",
    ),
    # Download Result Management
    ConfigField(
        key="download-result",
        label="Download Result",
        type=FieldType.SELECT,
        default="default",
        options=[
            ("default", "Default"),
            ("full", "Full Information"),
            ("hide", "Hide"),
        ],
        help_text="Control download result output",
        section="Download Result",
    ),
    ConfigField(
        key="force-save",
        label="Force Save",
        type=FieldType.SWITCH,
        default=False,
        help_text="Save download with --save-session even if completed or removed",
        section="Download Result",
    ),
    ConfigField(
        key="hash-check-only",
        label="Hash Check Only",
        type=FieldType.SWITCH,
        default=False,
        help_text="Only verify checksums, don't download files",
        section="Download Result",
    ),
    ConfigField(
        key="keep-unfinished-download-result",
        label="Keep Unfinished Result",
        type=FieldType.SWITCH,
        default=True,
        help_text="Keep unfinished downloads in memory",
        section="Download Result",
    ),
    ConfigField(
        key="max-download-result",
        label="Max Download Result",
        type=FieldType.NUMBER,
        default=1000,
        min_value=0,
        help_text="Maximum number of download results to keep",
        section="Download Result",
    ),
    ConfigField(
        key="max-resume-failure-tries",
        label="Max Resume Failure Tries",
        type=FieldType.NUMBER,
        default=0,
        min_value=0,
        help_text="Maximum resume failure attempts (0 = unlimited)",
        section="Download Result",
    ),
    ConfigField(
        key="save-not-found",
        label="Save Not Found",
        type=FieldType.SWITCH,
        default=True,
        help_text="Save 404 downloads with --save-session",
        section="Download Result",
    ),
    # Logging
    ConfigField(
        key="log-level",
        label="Log Level",
        type=FieldType.SELECT,
        default="debug",
        options=[
            ("debug", "Debug (most verbose)"),
            ("info", "Info"),
            ("notice", "Notice"),
            ("warn", "Warning"),
            ("error", "Error (least verbose)"),
        ],
        help_text="Log output verbosity level",
        section="Logging",
    ),
    # Session
    ConfigField(
        key="save-session",
        label="Save Session File",
        type=FieldType.INPUT,
        default="",
        placeholder="/path/to/session.txt",
        help_text="Save error/unfinished downloads to this file on exit",
        section="Session",
    ),
]

# =============================================================================
# Combined Lists
# =============================================================================

# All fields grouped by AriaNg categories (in proper order)
ALL_ARIA2_FIELDS = (
    ARIA2_FIELDS_BASIC
    + ARIA2_FIELDS_HTTP_FTP_SFTP
    + ARIA2_FIELDS_HTTP
    + ARIA2_FIELDS_FTP_SFTP
    + ARIA2_FIELDS_BITTORRENT
    + ARIA2_FIELDS_METALINK
    + ARIA2_FIELDS_RPC
    + ARIA2_FIELDS_ADVANCED
)

# Legacy combined field for backward compatibility
ARIA2_FIELDS_HTTP_FTP = ARIA2_FIELDS_HTTP + ARIA2_FIELDS_FTP_SFTP
