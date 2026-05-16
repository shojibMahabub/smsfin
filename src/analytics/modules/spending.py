"""Spending analyzer module."""

from collections import defaultdict
from decimal import Decimal

from src.analytics import AnalyticsEngine, Insight


class SpendingAnalyzer(AnalyticsEngine):
    """Analyze spending patterns."""

    name = "spending"

    def analyze(self, rows: list) -> list[Insight]:
        """Run spending analysis."""
        insights = []

        spending = self.get_spending_by_category(rows)
        if spending:
            total = sum(spending.values())
            top_category = max(spending.items(), key=lambda x: x[1])

            insights.append(Insight(
                type="spending_summary",
                title="Total Spending",
                description=f"Total spending: ৳{total:,.0f}",
                value=total,
                details={"by_category": dict(spending)}
            ))

            insights.append(Insight(
                type="top_category",
                title=f"Top Category: {top_category[0]}",
                description=f"Highest spending in {top_category[0]}: ৳{top_category[1]:,.0f}",
                value=top_category[1],
                details={"category": top_category[0]}
            ))

        monthly = self.get_spending_by_month(rows)
        if monthly:
            avg = sum(monthly.values()) / len(monthly)
            insights.append(Insight(
                type="monthly_average",
                title="Average Monthly Spending",
                description=f"Average: ৳{avg:,.0f} per month",
                value=avg,
                details={"by_month": dict(monthly)}
            ))

        return insights

    def get_spending_by_category(self, rows: list) -> dict:
        """Get spending breakdown by category."""
        totals = defaultdict(Decimal)
        for row in rows:
            if hasattr(row, 'direction') and row.direction == "expense":
                if row.amount and row.category:
                    totals[row.category] += row.amount
        return dict(totals)

    def get_spending_by_month(self, rows: list) -> dict:
        """Get monthly spending."""
        totals = defaultdict(Decimal)
        for row in rows:
            if hasattr(row, 'direction') and row.direction == "expense":
                if row.amount and row.month:
                    totals[row.month] += row.amount
        return dict(totals)

    def get_top_merchants(self, rows: list, limit: int = 10) -> list:
        """Get top merchants by spending."""
        totals = defaultdict(Decimal)
        for row in rows:
            if hasattr(row, 'direction') and row.direction == "expense":
                if row.amount and row.merchant_or_counterparty:
                    totals[row.merchant_or_counterparty] += row.amount
        sorted_merchants = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        return sorted_merchants[:limit]
