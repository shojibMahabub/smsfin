"""Filter plugins registry."""

from src.parsers.filters.ollama_filter import OllamaFilter
from src.parsers.filters.sender_filter import SenderFilter

FILTERS = {
    "ollama": OllamaFilter,
    "sender": SenderFilter,
}

__all__ = ["FILTERS"]
