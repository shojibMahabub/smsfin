"""Forecasting models registry."""

from src.forecasting.models.linear import LinearForecaster
from src.forecasting.models.llm import LLMForecaster

MODELS = {
    "linear": LinearForecaster,
    "llm": LLMForecaster,
}

__all__ = ["MODELS"]
