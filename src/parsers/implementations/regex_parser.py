"""Regex-based parser plugin (wrapper for existing parsers)."""

import logging
from typing import Any, Optional

from src.models.ledger import LedgerRow

logger = logging.getLogger(__name__)


class RegexParser:
    """Regex-based SMS parser using bank-specific rules."""

    name = "regex"
    enabled = True

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self._parsers = None

    def _get_parsers(self):
        """Lazy-load bank parsers."""
        if self._parsers is None:
            from src.core.processor import parse_raw_row
            self._parsers = parse_raw_row
        return self._parsers

    def parse(self, raw: dict[str, str]) -> Optional[LedgerRow]:
        """Parse SMS using regex patterns."""
        try:
            parser = self._get_parsers()
            return parser(raw)
        except Exception as e:
            logger.error(f"Regex parse error: {e}")
            return None


plugin = RegexParser
