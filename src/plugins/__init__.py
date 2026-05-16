"""Plugin system initialization.

This module auto-discovers and registers all plugins.
"""

from src.parsers.filters import FILTERS
from src.parsers.implementations import PARSERS
from src.io.sources import SOURCES
from src.io.outputs import OUTPUTS
from src.analytics.modules import MODULES as ANALYTICS
from src.forecasting.models import MODELS as FORECASTING
from src.io.notifications.channels import CHANNELS
from src.plugins.registry import registry


def register_all_plugins():
    """Register all available plugins."""
    # Filters
    for name, plugin_class in FILTERS.items():
        registry.register_filter(name, plugin_class)

    # Parsers
    for name, plugin_class in PARSERS.items():
        registry.register_parser(name, plugin_class)

    # Sources
    for name, plugin_class in SOURCES.items():
        registry.register_source(name, plugin_class)

    # Outputs
    for name, plugin_class in OUTPUTS.items():
        registry.register_output(name, plugin_class)

    # Analytics
    for name, plugin_class in ANALYTICS.items():
        registry.register_analyzer(name, plugin_class)

    # Forecasting
    for name, plugin_class in FORECASTING.items():
        registry.register_forecaster(name, plugin_class)

    # Notification channels
    for name, plugin_class in CHANNELS.items():
        registry.register_channel(name, plugin_class)


# Auto-register on import
register_all_plugins()
