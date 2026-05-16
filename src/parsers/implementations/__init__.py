"""Parser plugins registry."""

from src.parsers.implementations.regex_parser import RegexParser
from src.parsers.implementations.ollama_parser import OllamaParser

PARSERS = {
    "regex": RegexParser,
    "ollama": OllamaParser,
}

__all__ = ["PARSERS"]
