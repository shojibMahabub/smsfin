"""Forecasting base module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Forecast:
    """Forecast result."""
    period: str
    predicted_value: float
    confidence: float
    lower_bound: float
    upper_bound: float
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ForecastingEngine:
    """Base forecasting engine."""

    def __init__(self, config: dict = None):
        self.config = config or {}

    def predict(self, historical_data: list) -> list[Forecast]:
        """Generate forecast."""
        raise NotImplementedError

    def predict_category(self, category: str, historical_data: list) -> Forecast:
        """Forecast for specific category."""
        raise NotImplementedError
