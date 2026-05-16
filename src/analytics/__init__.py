"""Analytics base module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Insight:
    """Analytics insight."""
    type: str
    title: str
    description: str
    value: Any
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class AnalyticsEngine:
    """Base analytics engine."""

    def __init__(self, config: dict = None):
        self.config = config or {}

    def analyze(self, rows: list) -> list[Insight]:
        """Run all analytics and return insights."""
        raise NotImplementedError

    def get_spending_by_category(self, rows: list) -> dict:
        """Get spending breakdown by category."""
        raise NotImplementedError

    def get_spending_by_month(self, rows: list) -> dict:
        """Get monthly spending trends."""
        raise NotImplementedError

    def get_top_merchants(self, rows: list, limit: int = 10) -> list:
        """Get top merchants by spending."""
        raise NotImplementedError
