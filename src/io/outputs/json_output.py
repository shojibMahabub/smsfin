"""JSON output plugin."""

import json
from pathlib import Path
from typing import Any

from src.models.ledger import LedgerRow


class JSONOutput:
    """JSON output plugin."""

    name = "json"
    enabled = True

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

    def write(self, rows: list[LedgerRow], output_path: str) -> None:
        """Write ledger rows to JSON file."""
        data = []
        for row in rows:
            data.append({
                "date": row.date,
                "time": row.time,
                "month": row.month,
                "source": row.source,
                "account": row.account,
                "type": row.type,
                "amount": str(row.amount) if row.amount else None,
                "currency": row.currency,
                "merchant_or_counterparty": row.merchant_or_counterparty,
                "category": row.category,
                "direction": row.direction,
                "balance_after": str(row.balance_after) if row.balance_after else None,
                "transaction_id": row.transaction_id,
                "confidence": row.confidence,
                "review_flag": row.review_flag,
                "review_reason": row.review_reason,
            })

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


plugin = JSONOutput
