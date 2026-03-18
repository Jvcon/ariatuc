"""Event management for aria2 WebSocket notifications.

This manager handles WebSocket event subscriptions and provides high-level
event processing capabilities like notifications, sound alerts, and custom callbacks.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import Any

from aria2rpc import Aria2Event
from aria2rpc.websocket import WebSocketRPCClient

logger = logging.getLogger(__name__)


# Type aliases
EventCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]
SyncEventCallback = Callable[[dict[str, Any]], None]


class NotificationType(Enum):
    """Notification type for user alerts."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class EventManager:
    """Manages aria2 WebSocket event notifications.

    This manager subscribes to aria2 events through WebSocket and provides:
    - Event callback registration
    - Built-in notification support
    - Sound alert support (reserved)
    - Event filtering and aggregation
    - Automatic enable/disable based on connection protocol
    """

    def __init__(self):
        """Initialize the event manager."""
        self._ws_client: WebSocketRPCClient | None = None
        self._is_active = False

        # User callbacks per event type
        self._callbacks: dict[Aria2Event, list[EventCallback]] = {event: [] for event in Aria2Event}

        # Built-in notification handlers
        self._notification_handler: SyncEventCallback | None = None
        self._sound_handler: SyncEventCallback | None = None

        # Event statistics
        self._event_counts: dict[Aria2Event, int] = dict.fromkeys(Aria2Event, 0)

    def set_client(self, ws_client: WebSocketRPCClient | None) -> None:
        """Set the WebSocket client for event subscription.

        Args:
            ws_client: WebSocket RPC client or None to disable events
        """
        # Unsubscribe from old client
        if self._ws_client and self._is_active:
            self.disable()

        self._ws_client = ws_client

        # Auto-enable if we have a WebSocket client
        if self._ws_client:
            self.enable()
        else:
            logger.info("No WebSocket client available, events disabled")

    def enable(self) -> bool:
        """Enable event monitoring.

        Returns:
            True if enabled successfully, False if no WebSocket client
        """
        if not self._ws_client:
            logger.warning("Cannot enable events: no WebSocket client set")
            return False

        if self._is_active:
            logger.debug("Events already enabled")
            return True

        # Subscribe to all aria2 events
        for event in Aria2Event:
            self._ws_client.on(event, self._handle_event(event))

        self._is_active = True
        logger.info("Event monitoring enabled")
        return True

    def disable(self) -> None:
        """Disable event monitoring."""
        if not self._is_active:
            return

        # Note: WebSocketRPCClient doesn't provide unsubscribe method,
        # so we just mark as inactive and ignore events
        self._is_active = False
        logger.info("Event monitoring disabled")

    def is_active(self) -> bool:
        """Check if event monitoring is active.

        Returns:
            True if active, False otherwise
        """
        return self._is_active and self._ws_client is not None

    def on(self, event: Aria2Event, callback: EventCallback) -> None:
        """Register a callback for an event.

        Args:
            event: The event type to subscribe to
            callback: Async callback function
                     Signature: async def callback(event_data: dict) -> None

        Example:
            async def on_complete(event_data):
                gid = event_data['gid']
                print(f"Download {gid} completed!")

            event_manager.on(Aria2Event.DOWNLOAD_COMPLETE, on_complete)
        """
        if callback not in self._callbacks[event]:
            self._callbacks[event].append(callback)
            logger.debug(f"Registered callback for {event.value}")

    def off(self, event: Aria2Event, callback: EventCallback) -> None:
        """Unregister a callback for an event.

        Args:
            event: The event type
            callback: The callback to remove
        """
        if callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
            logger.debug(f"Unregistered callback for {event.value}")

    def set_notification_handler(self, handler: SyncEventCallback | None) -> None:
        """Set the notification handler for UI notifications.

        Args:
            handler: Sync callback for notifications
                    Signature: def handler(notification: dict) -> None
                    notification = {
                        'type': NotificationType,
                        'title': str,
                        'message': str,
                        'event': Aria2Event,
                        'gid': str
                    }
        """
        self._notification_handler = handler
        logger.info("Notification handler set")

    def set_sound_handler(self, handler: SyncEventCallback | None) -> None:
        """Set the sound handler for audio alerts.

        Args:
            handler: Sync callback for sound playback
                    Signature: def handler(event_data: dict) -> None
        """
        self._sound_handler = handler
        logger.info("Sound handler set")

    def _handle_event(self, event_type: Aria2Event) -> EventCallback:
        """Create event handler for a specific event type.

        Args:
            event_type: The event type

        Returns:
            Async callback function
        """

        async def handler(event_data: dict[str, Any]) -> None:
            """Internal event handler."""
            if not self._is_active:
                return

            # Update statistics
            self._event_counts[event_type] += 1

            gid = event_data.get("gid", "unknown")
            logger.debug(f"Received event: {event_type.value} for GID {gid}")

            # Call user callbacks
            for callback in self._callbacks[event_type]:
                try:
                    await callback(event_data)
                except Exception as e:
                    logger.error(f"Error in user callback for {event_type.value}: {e}")

            # Built-in handlers
            self._handle_notification(event_type, event_data)
            self._handle_sound(event_type, event_data)

        return handler

    def _handle_notification(self, event: Aria2Event, event_data: dict[str, Any]) -> None:
        """Handle notification for an event.

        Args:
            event: The event type
            event_data: Event data from aria2
        """
        if not self._notification_handler:
            return

        # Determine notification type and message
        notification_map = {
            Aria2Event.DOWNLOAD_START: (NotificationType.INFO, "Download Started"),
            Aria2Event.DOWNLOAD_PAUSE: (NotificationType.WARNING, "Download Paused"),
            Aria2Event.DOWNLOAD_STOP: (NotificationType.WARNING, "Download Stopped"),
            Aria2Event.DOWNLOAD_COMPLETE: (NotificationType.SUCCESS, "Download Complete"),
            Aria2Event.DOWNLOAD_ERROR: (NotificationType.ERROR, "Download Error"),
            Aria2Event.BT_DOWNLOAD_COMPLETE: (
                NotificationType.SUCCESS,
                "BitTorrent Download Complete",
            ),
        }

        notif_type, title = notification_map.get(event, (NotificationType.INFO, "Download Event"))
        gid = event_data.get("gid", "unknown")

        notification = {
            "type": notif_type,
            "title": title,
            "message": f"GID: {gid}",
            "event": event,
            "gid": gid,
        }

        try:
            self._notification_handler(notification)
        except Exception as e:
            logger.error(f"Error in notification handler: {e}")

    def _handle_sound(self, event: Aria2Event, event_data: dict[str, Any]) -> None:
        """Handle sound alert for an event.

        Args:
            event: The event type
            event_data: Event data from aria2
        """
        if not self._sound_handler:
            return

        # Play sound for completion and error events
        if event in (
            Aria2Event.DOWNLOAD_COMPLETE,
            Aria2Event.BT_DOWNLOAD_COMPLETE,
            Aria2Event.DOWNLOAD_ERROR,
        ):
            try:
                self._sound_handler(event_data)
            except Exception as e:
                logger.error(f"Error in sound handler: {e}")

    def get_event_counts(self) -> dict[str, int]:
        """Get event statistics.

        Returns:
            Dict mapping event names to counts
        """
        return {event.value: count for event, count in self._event_counts.items()}

    def reset_event_counts(self) -> None:
        """Reset event statistics."""
        self._event_counts = dict.fromkeys(Aria2Event, 0)
        logger.debug("Event counts reset")

    async def wait_for_event(
        self,
        event: Aria2Event,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Wait for a specific event to occur.

        Args:
            event: The event type to wait for
            predicate: Optional filter function to match specific events
            timeout: Optional timeout in seconds

        Returns:
            Event data dict

        Raises:
            asyncio.TimeoutError: If timeout is reached
        """
        future: asyncio.Future[dict[str, Any]] = asyncio.Future()

        async def callback(event_data: dict[str, Any]) -> None:
            if not future.done():
                if predicate is None or predicate(event_data):
                    future.set_result(event_data)

        # Register temporary callback
        self.on(event, callback)

        try:
            if timeout:
                result = await asyncio.wait_for(future, timeout=timeout)
            else:
                result = await future
            return result
        finally:
            # Cleanup
            self.off(event, callback)
