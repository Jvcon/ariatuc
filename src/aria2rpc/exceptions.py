"""Exception classes for aria2 RPC client."""


class Aria2Error(Exception):
    """Base exception for all aria2 RPC errors."""

    pass


class Aria2ConnectionError(Aria2Error):
    """Raised when connection to aria2 RPC server fails."""

    def __init__(self, message: str, url: str | None = None):
        """Initialize connection error.

        Args:
            message: Error message
            url: The RPC server URL that failed to connect
        """
        super().__init__(message)
        self.url = url


class Aria2TimeoutError(Aria2Error):
    """Raised when RPC request times out."""

    pass


class Aria2AuthenticationError(Aria2Error):
    """Raised when authentication fails (invalid secret token)."""

    pass


class Aria2RPCError(Aria2Error):
    """Raised when aria2 returns an RPC error."""

    def __init__(self, code: int, message: str):
        """Initialize RPC error.

        Args:
            code: Error code from aria2
            message: Error message from aria2
        """
        super().__init__(f"RPC Error {code}: {message}")
        self.code = code
        self.message = message
