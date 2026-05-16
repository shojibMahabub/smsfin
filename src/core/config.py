"""Configuration loader."""

import copy
import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml

_ENV_PATTERN = re.compile(
    r"\$\{([^}:]+?)(?::-([^}]*))?\}"
)


def expand_env(value: str) -> str:
    """Expand ${VAR} and ${VAR:-default} in a string."""

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        default = match.group(2)
        env_val = os.environ.get(var_name)
        if env_val is not None:
            return env_val
        if default is not None:
            return default
        return ""

    return _ENV_PATTERN.sub(replacer, value)


def expand_env_values(obj: Any) -> Any:
    """Recursively expand env placeholders in config values."""
    if isinstance(obj, str):
        return expand_env(obj)
    if isinstance(obj, dict):
        return {k: expand_env_values(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [expand_env_values(item) for item in obj]
    return obj


def get_enabled_plugin(section: str, config: dict[str, Any]) -> dict[str, Any]:
    """Return first enabled plugin config from a list section."""
    items = config.get(section) or []
    if not isinstance(items, list):
        return {}

    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("enabled", True):
            return item

    if items and isinstance(items[0], dict):
        return items[0]
    return {}


def _normalize_source_type(source: str) -> str:
    if source == "google_sheet":
        return "google_sheets"
    return source


def build_runtime_config(
    base_config: dict[str, Any],
    cli_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Merge CLI overrides into config for Pipeline execution."""
    config = copy.deepcopy(base_config)
    overrides = cli_overrides or {}

    # Source
    source_type = overrides.get("source")
    if source_type:
        source_type = _normalize_source_type(source_type)
        source_cfg = {"type": source_type, "enabled": True}
        if source_type == "csv":
            if overrides.get("input"):
                source_cfg["path"] = overrides["input"]
        else:
            if overrides.get("input"):
                source_cfg["sheet_url"] = overrides["input"]
            if overrides.get("credentials"):
                source_cfg["credentials"] = overrides["credentials"]
        config["sources"] = [source_cfg]
    elif overrides.get("input"):
        sources = config.get("sources") or []
        source_cfg = get_enabled_plugin("sources", config) or (
            sources[0] if sources and isinstance(sources[0], dict) else {}
        )
        source_cfg = copy.deepcopy(source_cfg)
        stype = _normalize_source_type(source_cfg.get("type", "csv"))
        source_cfg["type"] = stype
        if stype == "csv":
            source_cfg["path"] = overrides["input"]
        else:
            source_cfg["sheet_url"] = overrides["input"]
            if overrides.get("credentials"):
                source_cfg["credentials"] = overrides["credentials"]
        config["sources"] = [source_cfg]

    # Filter
    filter_type = overrides.get("filter")
    if filter_type and filter_type != "none":
        filter_cfg = {"type": filter_type, "enabled": True}
        existing = get_enabled_plugin("filters", config)
        if existing.get("model"):
            filter_cfg["model"] = existing["model"]
        if existing.get("workers"):
            filter_cfg["workers"] = existing["workers"]
        config["filters"] = [filter_cfg]
    elif filter_type == "none":
        config["filters"] = []

    # Parser
    parser_type = overrides.get("parser")
    if parser_type and parser_type != "none":
        parser_cfg = {"type": parser_type, "enabled": True}
        existing = get_enabled_plugin("parsers", config)
        if existing.get("model"):
            parser_cfg["model"] = existing["model"]
        if existing.get("fallback"):
            parser_cfg["fallback"] = existing["fallback"]
        config["parsers"] = [parser_cfg]
    elif parser_type == "none":
        config["parsers"] = []

    # Output path stored for pipeline.run()
    if overrides.get("output"):
        config["_output_path"] = overrides["output"]

    # Analytics / forecast flags
    analytics = config.setdefault("analytics", {})
    if overrides.get("analyze") is not None:
        analytics["enabled"] = overrides["analyze"]
    elif "analyze" not in overrides:
        pass  # keep config value

    forecasting = config.setdefault("forecasting", {})
    if overrides.get("forecast") is not None:
        forecasting["_run"] = overrides["forecast"]
    if overrides.get("forecast_periods") is not None:
        forecasting["periods"] = overrides["forecast_periods"]
    if overrides.get("forecast_model") is not None:
        forecasting["model"] = overrides["forecast_model"]

    config["_skip_filter"] = overrides.get("filter") == "none"
    config["_skip_parser"] = overrides.get("parser") == "none"

    return config


class Config:
    """Configuration manager."""

    def __init__(self, config_path: Optional[str] = None):
        self._data: dict[str, Any] = {}
        self._config_path = config_path or self._find_config()
        if self._config_path:
            self.load(self._config_path)

    def _find_config(self) -> Optional[str]:
        """Find config file in standard locations."""
        candidates = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "config.yml",
            Path.home() / ".fintrack" / "config.yaml",
            Path(__file__).parent.parent.parent / "config.yaml",
        ]
        for path in candidates:
            if path.exists():
                return str(path)
        return None

    def load(self, path: str) -> None:
        """Load config from YAML file with env expansion."""
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        self._data = expand_env_values(raw)
        self._config_path = path

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key."""
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set config value by dot-notation key."""
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value

    def build_runtime(self, cli_overrides: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Build merged runtime config with CLI overrides."""
        return build_runtime_config(self._data, cli_overrides)

    @property
    def data(self) -> dict[str, Any]:
        return self._data


config = Config()
