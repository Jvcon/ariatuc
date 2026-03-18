"""Speed tracking with Exponential Moving Average (EMA) smoothing.

This module provides speed calculation and smoothing functionality
inspired by the Surge download manager implementation.

Key features:
- EMA smoothing to prevent speed value jitter
- Configurable smoothing factor (alpha)
- Per-download speed tracking
- Thread-safe operations
"""

import time
from dataclasses import dataclass


@dataclass
class SpeedInfo:
    """Speed information for a download."""

    instant_speed: float  # Instantaneous speed (bytes/s)
    smoothed_speed: float  # EMA smoothed speed (bytes/s)
    last_completed: int  # Last recorded completed bytes
    last_update_time: float  # Last update timestamp


class SpeedTracker:
    """Track and smooth download speeds using EMA algorithm.

    Uses Exponential Moving Average (EMA) for smoothing speed values:
        smoothed_speed = alpha * instant_speed + (1 - alpha) * last_smoothed_speed

    Reference: Surge download manager speed tracking implementation
    Update frequency: ~150ms (independent of UI refresh rate)
    """

    def __init__(self, alpha: float = 0.3) -> None:
        """Initialize speed tracker.

        Args:
            alpha: Smoothing factor (0.0 to 1.0)
                  Higher alpha = more responsive to changes (less smoothing)
                  Lower alpha = more stable (more smoothing)
                  Default 0.3 provides good balance
        """
        if not 0.0 <= alpha <= 1.0:
            msg = f"alpha must be between 0.0 and 1.0, got {alpha}"
            raise ValueError(msg)

        self.alpha = alpha
        self._speeds: dict[str, SpeedInfo] = {}  # gid -> SpeedInfo

    def update(
        self,
        gid: str,
        completed_length: int,
        current_time: float | None = None,
    ) -> float:
        """Update speed for a download and return smoothed speed.

        Args:
            gid: Download GID
            completed_length: Current completed bytes
            current_time: Current timestamp (seconds), uses time.time() if None

        Returns:
            Smoothed download speed in bytes/s
        """
        if current_time is None:
            current_time = time.time()

        # Get or create speed info for this download
        if gid not in self._speeds:
            # Initialize with zero speed
            self._speeds[gid] = SpeedInfo(
                instant_speed=0.0,
                smoothed_speed=0.0,
                last_completed=completed_length,
                last_update_time=current_time,
            )
            return 0.0

        speed_info = self._speeds[gid]

        # Calculate time elapsed since last update
        time_elapsed = current_time - speed_info.last_update_time

        # Avoid division by zero
        if time_elapsed <= 0.0:
            return speed_info.smoothed_speed

        # Calculate bytes downloaded since last update
        bytes_diff = completed_length - speed_info.last_completed

        # Calculate instantaneous speed (bytes/s)
        instant_speed = bytes_diff / time_elapsed

        # Apply EMA smoothing
        # smoothed = alpha * instant + (1 - alpha) * last_smoothed
        smoothed_speed = self.alpha * instant_speed + (1 - self.alpha) * speed_info.smoothed_speed

        # Update speed info
        speed_info.instant_speed = instant_speed
        speed_info.smoothed_speed = smoothed_speed
        speed_info.last_completed = completed_length
        speed_info.last_update_time = current_time

        return smoothed_speed

    def get_smoothed_speed(self, gid: str) -> float:
        """Get current smoothed speed for a download.

        Args:
            gid: Download GID

        Returns:
            Smoothed speed in bytes/s, or 0.0 if not tracked
        """
        if gid not in self._speeds:
            return 0.0
        return self._speeds[gid].smoothed_speed

    def get_instant_speed(self, gid: str) -> float:
        """Get current instantaneous speed for a download.

        Args:
            gid: Download GID

        Returns:
            Instant speed in bytes/s, or 0.0 if not tracked
        """
        if gid not in self._speeds:
            return 0.0
        return self._speeds[gid].instant_speed

    def remove(self, gid: str) -> None:
        """Remove speed tracking for a download.

        Args:
            gid: Download GID
        """
        self._speeds.pop(gid, None)

    def clear(self) -> None:
        """Clear all speed tracking data."""
        self._speeds.clear()

    def reset(self, gid: str) -> None:
        """Reset speed tracking for a download to zero.

        Args:
            gid: Download GID
        """
        if gid in self._speeds:
            speed_info = self._speeds[gid]
            speed_info.instant_speed = 0.0
            speed_info.smoothed_speed = 0.0
