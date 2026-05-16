"""Output plugins registry."""

from src.io.outputs.excel_output import ExcelOutput
from src.io.outputs.json_output import JSONOutput

OUTPUTS = {
    "excel": ExcelOutput,
    "json": JSONOutput,
}

__all__ = ["OUTPUTS"]
