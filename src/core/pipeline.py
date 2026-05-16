"""Pipeline orchestrator for SMS processing."""

import logging
from typing import Any, Iterator, Optional

from src.core.config import get_enabled_plugin
from src.models.ledger import LedgerRow
from src.plugins import registry  # noqa: F401 - triggers plugin registration
from src.plugins.registry import registry as plugin_registry

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the SMS processing pipeline."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._filter = None
        self._parser = None
        self._source = None
        self._output = None

    def _plugin_config(self, section: str, default_type: str) -> dict[str, Any]:
        cfg = get_enabled_plugin(section, self.config)
        if cfg:
            return cfg
        return {"type": default_type, "enabled": True}

    def _get_filter(self):
        """Get filter plugin instance."""
        if self._filter is None:
            if self.config.get("_skip_filter"):
                return None
            filter_config = self._plugin_config("filters", "sender")
            filter_type = filter_config.get("type", "sender")
            plugin_cls = plugin_registry.filters.get(filter_type)
            if plugin_cls:
                self._filter = plugin_cls(filter_config)
            else:
                logger.warning("Filter %s not found", filter_type)
        return self._filter

    def _get_parser(self):
        """Get parser plugin instance."""
        if self._parser is None:
            if self.config.get("_skip_parser"):
                return None
            parser_config = self._plugin_config("parsers", "regex")
            parser_type = parser_config.get("type", "regex")
            plugin_cls = plugin_registry.parsers.get(parser_type)
            if plugin_cls:
                self._parser = plugin_cls(parser_config)
            else:
                logger.warning("Parser %s not found", parser_type)
        return self._parser

    def _get_source(self):
        """Get source plugin instance."""
        if self._source is None:
            source_config = self._plugin_config("sources", "csv")
            source_type = source_config.get("type", "csv")
            plugin_cls = plugin_registry.sources.get(source_type)
            if plugin_cls:
                self._source = plugin_cls(source_config)
            else:
                logger.warning("Source %s not found", source_type)
        return self._source

    def _get_output(self, output_path: Optional[str] = None):
        """Get output plugin instance based on file extension or config."""
        if self._output is None:
            path = output_path or self.config.get("_output_path", "output.xlsx")
            if path.endswith(".json"):
                output_config = {"type": "json", "enabled": True}
            else:
                output_config = get_enabled_plugin("outputs", self.config) or {
                    "type": "excel",
                    "enabled": True,
                }
            output_type = output_config.get("type", "excel")
            plugin_cls = plugin_registry.outputs.get(output_type)
            if plugin_cls:
                self._output = plugin_cls(output_config)
            else:
                logger.warning("Output %s not found", output_type)
        return self._output

    def _filter_rows(self, raw_rows: list[dict]) -> list[dict]:
        """Apply filter plugin to raw SMS rows."""
        filter_plugin = self._get_filter()
        if not filter_plugin:
            return raw_rows

        from src.parsers.filters.ollama_filter import OllamaFilter

        if isinstance(filter_plugin, OllamaFilter):
            classifications = filter_plugin.classify_batch(raw_rows, show_progress=True)
            return [
                raw
                for i, raw in enumerate(raw_rows)
                if classifications[i] and classifications[i].is_transaction()
            ]

        filtered = []
        for raw in raw_rows:
            classification = filter_plugin.classify(raw)
            if classification.type == "transaction":
                filtered.append(raw)
        return filtered

    def process(self, raw_sms: list[dict] | Iterator[dict]) -> list[LedgerRow]:
        """Process SMS data through filter and parser."""
        raw_rows = list(raw_sms)
        stats = {"total": len(raw_rows), "filtered": 0, "parsed": 0, "failed": 0}

        if self.config.get("_skip_filter"):
            to_parse = raw_rows
        else:
            before = len(raw_rows)
            to_parse = self._filter_rows(raw_rows)
            stats["filtered"] = before - len(to_parse)

        parser_plugin = self._get_parser()
        rows: list[LedgerRow] = []

        if parser_plugin:
            for raw in to_parse:
                row = parser_plugin.parse(raw)
                if row:
                    rows.append(row)
                    stats["parsed"] += 1
                else:
                    stats["failed"] += 1
        elif not self.config.get("_skip_parser"):
            stats["failed"] = len(to_parse)

        logger.info("Pipeline stats: %s", stats)
        return rows

    def write_output(self, rows: list[LedgerRow], output_path: str) -> None:
        """Write rows to output."""
        self._output = None
        output_plugin = self._get_output(output_path)
        if output_plugin:
            output_plugin.write(rows, output_path)
        else:
            raise RuntimeError("No output plugin configured")

    def run(self, output_path: str) -> list[LedgerRow]:
        """Read source, process, and write output."""
        source = self._get_source()
        if not source:
            raise RuntimeError("No source plugin configured")

        self.config["_output_path"] = output_path
        raw_rows = list(source.read())
        rows = self.process(raw_rows)
        if output_path:
            self.write_output(rows, output_path)
        return rows
