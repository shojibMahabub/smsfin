"""CSV input reader."""

import csv
from pathlib import Path
from typing import Iterator


def read_csv(path: Path) -> Iterator[dict[str, str]]:
    """Read SMS data from CSV file.

    Args:
        path: Path to CSV file

    Yields:
        Dictionary records from CSV
    """
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)
