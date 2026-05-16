"""Linear regression forecasting model."""

import statistics
from collections import defaultdict
from typing import Any, Optional

from src.forecasting import ForecastingEngine, Forecast


class LinearForecaster(ForecastingEngine):
    """Linear regression-based forecaster."""

    name = "linear"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.periods = self.config.get("periods", 3)

    def predict(self, historical_data: list) -> list[Forecast]:
        """Generate forecast using linear regression."""
        monthly = self._get_monthly_totals(historical_data)

        if len(monthly) < 2:
            return []

        # Prepare data for linear regression
        x_values = list(range(len(monthly)))
        y_values = [float(v) for v in monthly.values()]

        # Calculate linear regression
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        intercept = (sum_y - slope * sum_x) / n

        # Calculate standard error
        predictions = [slope * x + intercept for x in x_values]
        residuals = [y - p for y, p in zip(y_values, predictions)]
        std_error = statistics.stdev(residuals) if len(residuals) > 1 else 0

        # Generate forecasts
        forecasts = []
        months = sorted(monthly.keys())
        last_month = months[-1]

        for i in range(1, self.periods + 1):
            x = len(monthly) - 1 + i
            predicted = slope * x + intercept
            predicted = max(0, predicted)  # Can't be negative

            # Calculate confidence interval
            confidence = 0.95 if std_error == 0 else 0.80
            margin = 1.96 * std_error if std_error > 0 else predicted * 0.1

            # Project next month
            month_num = int(last_month.split("-")[1]) + i
            year_offset = (month_num - 1) // 12
            projected_month = f"{int(last_month.split('-')[0]) + year_offset}-{(month_num - 1) % 12 + 1:02d}"

            forecasts.append(Forecast(
                period=projected_month,
                predicted_value=round(predicted, 2),
                confidence=confidence,
                lower_bound=round(max(0, predicted - margin), 2),
                upper_bound=round(predicted + margin, 2),
                details={"slope": slope, "intercept": intercept}
            ))

        return forecasts

    def predict_category(self, category: str, historical_data: list) -> Optional[Forecast]:
        """Forecast for specific category."""
        category_data = [r for r in historical_data if hasattr(r, 'category') and r.category == category]
        if not category_data:
            return None

        monthly = defaultdict(float)
        for row in category_data:
            if row.amount and row.month:
                monthly[row.month] += float(row.amount)

        if len(monthly) < 2:
            return None

        # Use simple average for category prediction
        avg = statistics.mean(monthly.values())
        months = sorted(monthly.keys())
        last_month = months[-1]

        month_num = int(last_month.split("-")[1]) + 1
        year_offset = (month_num - 1) // 12
        next_month = f"{int(last_month.split('-')[0]) + year_offset}-{(month_num - 1) % 12 + 1:02d}"

        return Forecast(
            period=next_month,
            predicted_value=round(avg, 2),
            confidence=0.6,
            lower_bound=round(avg * 0.7, 2),
            upper_bound=round(avg * 1.3, 2),
            details={"method": "moving_average", "months": len(monthly)}
        )

    def _get_monthly_totals(self, historical_data: list) -> dict:
        """Get monthly spending totals."""
        monthly = defaultdict(float)
        for row in historical_data:
            if hasattr(row, 'direction') and row.direction == "expense":
                if row.amount and row.month:
                    monthly[row.month] += float(row.amount)
        return dict(sorted(monthly.items()))
