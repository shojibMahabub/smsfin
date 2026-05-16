"""CSV source plugin."""

import csv
from pathlib import Path
from typing import Any, Iterator

from src.io.csv_reader import read_csv as read_csv_original


class CSVSource:
    """CSV file input source plugin."""

    name = "csv"
    enabled = True

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

    def read(self) -> Iterator[dict[str, str]]:
        """Read SMS data from CSV file."""
        file_path = self.config.get("path")
        if not file_path:
            raise ValueError("path required in config")

        return read_csv_original(Path(file_path))


plugin = CSVSource
