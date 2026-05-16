"""Telegram notification channel."""

import logging
from typing import Any

from src.io.notifications import NotificationChannel, Notification

logger = logging.getLogger(__name__)


class TelegramChannel(NotificationChannel):
    """Telegram bot notification channel."""

    name = "telegram"

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self.bot_token = self.config.get("bot_token")
        self.chat_id = self.config.get("chat_id")
        self._client = None

    def _get_client(self):
        """Get Telegram bot client."""
        if self._client is None:
            try:
                import requests
                self._client = requests
            except ImportError:
                raise ImportError("requests library required for Telegram")
        return self._client

    def send(self, notification: Notification) -> bool:
        """Send notification via Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot_token or chat_id not configured")
            return False

        try:
            client = self._get_client()

            # Format message
            emoji = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "success": "✅",
            }.get(notification.type, "ℹ️")

            text = f"{emoji} *{notification.title}*\n\n{notification.body}"

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }

            response = client.post(url, json=data, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False


plugin = TelegramChannel
