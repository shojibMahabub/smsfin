"""Anomaly detection module."""

from collections import defaultdict
from decimal import Decimal
import statistics

from src.analytics import AnalyticsEngine, Insight


class AnomalyDetector(AnalyticsEngine):
    """Detect unusual spending patterns."""

    name = "anomaly"

    def analyze(self, rows: list) -> list[Insight]:
        """Run anomaly detection."""
        insights = []

        # Large transactions
        large = self.get_large_transactions(rows)
        if large:
            insights.append(Insight(
                type="large_transactions",
                title="Large Transactions",
                description=f"Found {len(large)} transactions above threshold",
                value=len(large),
                details={"transactions": large[:10]}
            ))

        # Unusual merchants
        unusual = self.get_unusual_merchants(rows)
        if unusual:
            insights.append(Insight(
                type="unusual_merchants",
                title="Unusual Merchants",
                description=f"Found {len(unusual)} one-time merchants",
                value=len(unusual),
                details={"merchants": unusual[:10]}
            ))

        # Spending spikes
        spikes = self.get_spending_spikes(rows)
        if spikes:
            insights.append(Insight(
                type="spending_spikes",
                title="Spending Spikes",
                description=f"Found {len(spikes)} months with unusual spending",
                value=len(spikes),
                details={"spikes": spikes}
            ))

        return insights

    def get_large_transactions(self, rows: list, threshold: float = 5000) -> list:
        """Get transactions above threshold."""
        large = []
        for row in rows:
            if hasattr(row, 'amount') and row.amount:
                amount = float(row.amount)
                if amount > threshold:
                    large.append({
                        "date": row.date,
                        "amount": amount,
                        "merchant": row.merchant_or_counterparty,
                        "category": row.category
                    })
        return sorted(large, key=lambda x: x["amount"], reverse=True)

    def get_unusual_merchants(self, rows: list) -> list:
        """Find merchants with only one transaction."""
        merchant_counts = defaultdict(int)
        merchant_amounts = defaultdict(Decimal)

        for row in rows:
            if hasattr(row, 'merchant_or_counterparty') and row.merchant_or_counterparty:
                merchant_counts[row.merchant_or_counterparty] += 1
                if row.amount:
                    merchant_amounts[row.merchant_or_counterparty] += row.amount

        unusual = []
        for merchant, count in merchant_counts.items():
            if count == 1 and merchant_amounts[merchant] > Decimal("1000"):
                unusual.append({
                    "merchant": merchant,
                    "amount": str(merchant_amounts[merchant])
                })

        return unusual

    def get_spending_spikes(self, rows: list, std_multiplier: float = 2.0) -> list:
        """Find months with spending spikes."""
        monthly_totals = defaultdict(Decimal)
        for row in rows:
            if hasattr(row, 'direction') and row.direction == "expense":
                if row.amount and row.month:
                    monthly_totals[row.month] += row.amount

        if len(monthly_totals) < 3:
            return []

        amounts = [float(v) for v in monthly_totals.values()]
        mean = statistics.mean(amounts)
        std = statistics.stdev(amounts) if len(amounts) > 1 else 0

        spikes = []
        for month, amount in sorted(monthly_totals.items()):
            if std > 0 and float(amount) > mean + (std_multiplier * std):
                spikes.append({
                    "month": month,
                    "amount": str(amount),
                    "mean": mean,
                    "deviation": float(amount) - mean
                })

        return spikes
