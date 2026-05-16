"""Google Sheets source plugin."""

from typing import Any, Iterator

from src.io.google_sheets import read_google_sheet


class GoogleSheetsSource:
    """Google Sheets input source plugin."""

    name = "google_sheets"
    enabled = True

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

    def read(self) -> Iterator[dict[str, str]]:
        """Read SMS data from Google Sheets."""
        sheet_url = self.config.get("sheet_url") or self.config.get("sheet_id")
        credentials = self.config.get("credentials")

        if not sheet_url:
            raise ValueError("sheet_url or sheet_id required in config")

        return read_google_sheet(sheet_url, credentials)


plugin = GoogleSheetsSource
