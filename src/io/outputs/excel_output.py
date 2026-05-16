"""Excel output plugin."""

from pathlib import Path
from typing import Any

from src.io.excel_writer import create_workbook, save_workbook, ledger_to_values, write_sheet
from src.models.ledger import LedgerRow, LEDGER_HEADERS


class ExcelOutput:
    """Excel output plugin."""

    name = "excel"
    enabled = True

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

    def write(self, rows: list[LedgerRow], output_path: str) -> None:
        """Write ledger rows to Excel file."""
        wb = create_workbook()
        ws = wb.active
        ws.title = "Ledger"

        # Write main ledger
        values = ledger_to_values(rows)
        write_sheet(ws, LEDGER_HEADERS, values, "Ledger")

        save_workbook(wb, Path(output_path))


plugin = ExcelOutput
