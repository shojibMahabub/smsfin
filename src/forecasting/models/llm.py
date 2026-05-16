"""LLM-based forecasting model."""

import json
import subprocess
from collections import defaultdict
from typing import Any, Optional

from src.forecasting import ForecastingEngine, Forecast


class LLMForecaster(ForecastingEngine):
    """LLM-based forecaster using Ollama."""

    name = "llm"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.model = self.config.get("model", "gemma4:e4b")
        self.periods = self.config.get("periods", 3)

    def predict(self, historical_data: list) -> list[Forecast]:
        """Generate forecast using LLM."""
        # Prepare data summary
        monthly = self._get_monthly_summary(historical_data)
        category = self._get_category_summary(historical_data)

        if not monthly:
            return []

        # Build prompt
        prompt = self._build_prompt(monthly, category, self.periods)

        # Call LLM
        result = self._call_llm(prompt)

        if result:
            return self._parse_forecast(result)

        return []

    def predict_category(self, category: str, historical_data: list) -> Optional[Forecast]:
        """Forecast for specific category."""
        category_data = [r for r in historical_data if hasattr(r, 'category') and r.category == category]
        if not category_data:
            return None

        monthly = self._get_monthly_summary(category_data)
        if not monthly:
            return None

        prompt = f"""Based on this spending history for '{category}' category:

{json.dumps(monthly, indent=2)}

Predict spending for next 3 months. Return JSON array:
[{{"period": "YYYY-MM", "predicted": number, "reasoning": "brief reason"}}]"""

        result = self._call_llm(prompt)
        if result:
            forecasts = self._parse_forecast(result)
            return forecasts[0] if forecasts else None

        return None

    def _get_monthly_summary(self, data: list) -> dict:
        """Get monthly spending summary."""
        monthly = defaultdict(float)
        for row in data:
            if hasattr(row, 'direction') and row.direction == "expense":
                if row.amount and row.month:
                    monthly[row.month] += float(row.amount)
        return dict(sorted(monthly.items()))

    def _get_category_summary(self, data: list) -> dict:
        """Get category breakdown."""
        category = defaultdict(float)
        for row in data:
            if hasattr(row, 'direction') and row.direction == "expense":
                if row.amount and row.category:
                    category[row.category] += float(row.amount)
        return dict(category)

    def _build_prompt(self, monthly: dict, category: dict, periods: int) -> str:
        """Build forecasting prompt."""
        return f"""You are a financial advisor. Based on this spending history:

Monthly totals:
{json.dumps(monthly, indent=2)}

Category breakdown:
{json.dumps(category, indent=2)}

Predict spending for next {periods} months. Consider:
- Current trends
- Seasonal patterns
- Category distributions

Return JSON array with {periods} predictions:
[{{"period": "YYYY-MM", "predicted": number, "confidence": 0.0-1.0, "reasoning": "brief explanation"}}]"""

    def _call_llm(self, prompt: str) -> Optional[dict]:
        """Call Ollama API."""
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if "[" in output:
                    start = output.find("[")
                    end = output.rfind("]") + 1
                    return json.loads(output[start:end])
        except Exception:
            pass
        return None

    def _parse_forecast(self, result: Any) -> list[Forecast]:
        """Parse LLM response to Forecast objects."""
        forecasts = []
        try:
            if isinstance(result, list):
                for item in result:
                    forecasts.append(Forecast(
                        period=item.get("period", ""),
                        predicted_value=float(item.get("predicted", 0)),
                        confidence=float(item.get("confidence", 0.5)),
                        lower_bound=float(item.get("predicted", 0)) * 0.8,
                        upper_bound=float(item.get("predicted", 0)) * 1.2,
                        details={"reasoning": item.get("reasoning", "")}
                    ))
        except (ValueError, TypeError):
            pass
        return forecasts
