"""Sender-based filter plugin.

Quickly filter SMS based on sender address.
"""

from typing import Any

from src.models.senders import is_financial_sender, Classification


class SenderFilter:
    """Filter SMS based on sender address."""

    name = "sender"
    enabled = True

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

    def classify(self, raw: dict[str, str]) -> Classification:
        """Classify SMS based on sender."""
        sender = raw.get("From", "")

        if is_financial_sender(sender):
            return Classification(
                type="transaction",
                confidence=0.9,
                reason=f"Financial sender: {sender}"
            )
        else:
            return Classification(
                type="promotional",
                confidence=0.9,
                reason=f"Non-financial sender: {sender}"
            )

    def is_enabled_sender(self, sender: str) -> bool:
        """Check if sender is enabled."""
        return is_financial_sender(sender)


plugin = SenderFilter
