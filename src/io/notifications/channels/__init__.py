"""Notification channels registry."""

from src.io.notifications.channels.telegram import TelegramChannel

CHANNELS = {
    "telegram": TelegramChannel,
}

__all__ = ["CHANNELS"]
