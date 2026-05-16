"""Source plugins registry."""

from src.io.sources.google_sheets import GoogleSheetsSource
from src.io.sources.csv_source import CSVSource

SOURCES = {
    "google_sheets": GoogleSheetsSource,
    "csv": CSVSource,
}

__all__ = ["SOURCES"]
