"""Analytics modules registry."""

from src.analytics.modules.spending import SpendingAnalyzer
from src.analytics.modules.trends import TrendsAnalyzer
from src.analytics.modules.anomaly import AnomalyDetector

MODULES = {
    "spending": SpendingAnalyzer,
    "trends": TrendsAnalyzer,
    "anomaly": AnomalyDetector,
}

__all__ = ["MODULES"]
