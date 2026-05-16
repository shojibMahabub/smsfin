"""Trends analyzer module."""

from collections import defaultdict
from decimal import Decimal
from typing import Optional

from src.analytics import AnalyticsEngine, Insight


class TrendsAnalyzer(AnalyticsEngine):
    """Analyze spending trends over time."""

    name = "trends"

    def analyze(self, rows: list) -> list[Insight]:
        """Run trends analysis."""
        insights = []
        monthly = self.get_spending_by_month(rows)

        if len(monthly) >= 2:
            months = sorted(monthly.keys())
            current_month = months[-1]
            prev_month = months[-2]

            current_spending = monthly[current_month]
            prev_spending = monthly[prev_month]

            if prev_spending > 0:
                change_pct = ((current_spending - prev_spending) / prev_spending) * 100

                trend = "increased" if change_pct > 0 else "decreased"
                insights.append(Insight(
                    type="monthly_trend",
                    title=f"Spending {trend}",
                    description=f"{current_month}: ৳{current_spending:,.0f} ({change_pct:+.1f}% vs {prev_month})",
                    value=change_pct,
                    details={
                        "current": str(current_spending),
                        "previous": str(prev_spending),
                        "change_percent": change_pct
                    }
                ))

        # Category trends
        category_trends = self.get_category_trends(rows)
        if category_trends:
            insights.append(Insight(
                type="category_trends",
                title="Category Trends",
                description=f"Analyzed {len(category_trends)} categories",
                value=len(category_trends),
                details=category_trends
            ))

        return insights

    def get_spending_by_month(self, rows: list) -> dict:
        """Get monthly spending."""
        totals = defaultdict(Decimal)
        for row in rows:
            if hasattr(row, 'direction') and row.direction == "expense":
                if row.amount and row.month:
                    totals[row.month] += row.amount
        return dict(totals)

    def get_category_trends(self, rows: list) -> dict:
        """Get category trends over time."""
        # Group by month and category
        monthly_category = defaultdict(lambda: defaultdict(Decimal))
        for row in rows:
            if hasattr(row, 'direction') and row.direction == "expense":
                if row.amount and row.month and row.category:
                    monthly_category[row.month][row.category] += row.amount

        # Convert to serializable format
        trends = {}
        for month, categories in monthly_category.items():
            trends[month] = {cat: str(amt) for cat, amt in categories.items()}

        return trends
