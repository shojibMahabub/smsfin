"""Text processing utilities."""

import re
from decimal import Decimal, InvalidOperation


def normalize_text(value: str) -> str:
    """Normalize text by collapsing whitespace."""
    return " ".join((value or "").split())


def parse_amount(value: str | None) -> Decimal | None:
    """Parse amount string to Decimal."""
    if not value:
        return None
    cleaned = re.sub(r"(?<=\d)\s+(?=\d)", "", value)
    cleaned = cleaned.replace(",", "").strip()
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def fmt_decimal(value: Decimal | None) -> float | None:
    """Format Decimal as float for Excel."""
    return float(value) if value is not None else None


def append_reason(existing: str, reason: str) -> str:
    """Append a reason to existing reasons."""
    if not existing:
        return reason
    parts = set(existing.split("; "))
    if reason not in parts:
        return f"{existing}; {reason}"
    return existing
