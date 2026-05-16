"""Plugin discovery and registry system."""

import importlib
import pkgutil
from pathlib import Path
from typing import Any, Protocol, Type


class Plugin(Protocol):
    """Base protocol for all plugins."""
    name: str
    enabled: bool = True


def discover_plugins(package_path: str) -> dict[str, Type[Plugin]]:
    """Discover plugins in a package directory."""
    plugins = {}
    package_dir = Path(package_path).parent

    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        if module_name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"{package_path}.{module_name}")
            if hasattr(module, "plugin"):
                plugin_class = module.plugin
                plugins[getattr(plugin_class, "name", module_name)] = plugin_class
        except ImportError as e:
            print(f"Failed to import {module_name}: {e}")
    return plugins


class PluginRegistry:
    """Central registry for all plugins."""

    def __init__(self):
        self._filters: dict[str, Type[Plugin]] = {}
        self._parsers: dict[str, Type[Plugin]] = {}
        self._sources: dict[str, Type[Plugin]] = {}
        self._outputs: dict[str, Type[Plugin]] = {}
        self._channels: dict[str, Type[Plugin]] = {}
        self._analyzers: dict[str, Type[Plugin]] = {}
        self._forecasters: dict[str, Type[Plugin]] = {}

    def register_filter(self, name: str, plugin_class: Type[Plugin]) -> None:
        self._filters[name] = plugin_class

    def register_parser(self, name: str, plugin_class: Type[Plugin]) -> None:
        self._parsers[name] = plugin_class

    def register_source(self, name: str, plugin_class: Type[Plugin]) -> None:
        self._sources[name] = plugin_class

    def register_output(self, name: str, plugin_class: Type[Plugin]) -> None:
        self._outputs[name] = plugin_class

    def register_channel(self, name: str, plugin_class: Type[Plugin]) -> None:
        self._channels[name] = plugin_class

    def register_analyzer(self, name: str, plugin_class: Type[Plugin]) -> None:
        self._analyzers[name] = plugin_class

    def register_forecaster(self, name: str, plugin_class: Type[Plugin]) -> None:
        self._forecasters[name] = plugin_class

    @property
    def filters(self) -> dict[str, Type[Plugin]]:
        return self._filters

    @property
    def parsers(self) -> dict[str, Type[Plugin]]:
        return self._parsers

    @property
    def sources(self) -> dict[str, Type[Plugin]]:
        return self._sources

    @property
    def outputs(self) -> dict[str, Type[Plugin]]:
        return self._outputs

    @property
    def channels(self) -> dict[str, Type[Plugin]]:
        return self._channels

    @property
    def analyzers(self) -> dict[str, Type[Plugin]]:
        return self._analyzers

    @property
    def forecasters(self) -> dict[str, Type[Plugin]]:
        return self._forecasters

    def all(self) -> dict[str, dict[str, Type[Plugin]]]:
        return {
            "filters": self._filters,
            "parsers": self._parsers,
            "sources": self._sources,
            "outputs": self._outputs,
            "channels": self._channels,
            "analyzers": self._analyzers,
            "forecasters": self._forecasters,
        }


registry = PluginRegistry()
