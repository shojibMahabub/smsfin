"""Notifications base module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Notification:
    """Notification message."""
    title: str
    body: str
    type: str = "info"  # info, warning, error, success
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class NotificationChannel:
    """Base notification channel."""

    def __init__(self, config: dict = None):
        self.config = config or {}

    def send(self, notification: Notification) -> bool:
        """Send notification."""
        raise NotImplementedError

    def send_batch(self, notifications: list[Notification]) -> list[bool]:
        """Send multiple notifications."""
        return [self.send(n) for n in notifications]


class NotificationManager:
    """Manage multiple notification channels."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._channels: dict[str, NotificationChannel] = {}

    def register_channel(self, name: str, channel: NotificationChannel) -> None:
        """Register a notification channel."""
        self._channels[name] = channel

    def send(self, notification: Notification, channels: list[str] = None) -> dict[str, bool]:
        """Send notification to specified channels."""
        if channels is None:
            channels = list(self._channels.keys())

        results = {}
        for channel_name in channels:
            if channel_name in self._channels:
                try:
                    results[channel_name] = self._channels[channel_name].send(notification)
                except Exception as e:
                    results[channel_name] = False
        return results
