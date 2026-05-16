"""Core processing logic."""

from collections import Counter, defaultdict
from typing import Iterable, Iterator, Optional

from src.models.ledger import LedgerRow
from src.models.senders import FINANCIAL_SENDERS
from src.parsers.bkash import parse_bkash
from src.parsers.dbbl import parse_dbbl
from src.parsers.dhaka_bank import parse_dhaka_bank
from src.parsers.nrb import parse_nrb

_DHAKA_SENDERS = {"DHAKA BANK", "DHAKABANK."}
_BKASH_SENDERS = {"bKash", "bKashNotice", "bKash Offer"}
_DBBL_SENDERS = {"16216"}


def parse_raw_row(raw: dict[str, str]) -> Optional[LedgerRow]:
    """Parse raw SMS row using appropriate parser."""
    source = raw.get("From", "")
    if source == "NRB Bank":
        return parse_nrb(raw)
    if source in _DHAKA_SENDERS:
        return parse_dhaka_bank(raw)
    if source in _DBBL_SENDERS:
        return parse_dbbl(raw)
    if source in _BKASH_SENDERS:
        return parse_bkash(raw)
    return None


def mark_possible_duplicates(rows: list[LedgerRow]) -> None:
    """Mark potential duplicate transactions."""
    from src.parsers.base import append_reason
    seen: dict[tuple[str, str, str, str, str, str], list[LedgerRow]] = defaultdict(list)
    for row in rows:
        if row.direction.startswith("ignored"):
            continue
        key = (
            row.date,
            str(row.amount),
            row.currency,
            row.source,
            row.merchant_or_counterparty.upper(),
            row.type,
        )
        seen[key].append(row)
    for group in seen.values():
        if len(group) > 1:
            for row in group:
                row.review_flag = "yes"
                row.review_reason = append_reason(row.review_reason, "possible_duplicate")
                if row.confidence == "high":
                    row.confidence = "medium"


def build_rows(raw_rows: Iterable[dict[str, str]]) -> tuple[list[LedgerRow], Counter]:
    """Build ledger rows from raw SMS data."""
    from src.parsers.base import append_reason
    rows: list[LedgerRow] = []
    stats: Counter = Counter()
    for raw in raw_rows:
        stats["input_rows"] += 1
        parsed = parse_raw_row(raw)
        if parsed is None:
            stats["ignored_non_financial_or_unknown"] += 1
            continue
        rows.append(parsed)
        stats[f"parsed_{parsed.type}"] += 1
    mark_possible_duplicates(rows)
    rows.sort(key=lambda row: (row.date, row.time, row.source, row.type))
    return rows, stats


def summarize_monthly(rows: list[LedgerRow]) -> list[list[object]]:
    """Generate monthly summary."""
    from src.utils.text import fmt_decimal
    monthly: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        if not row.month or row.amount is None or row.currency != "BDT":
            continue
        bucket = monthly[row.month]
        if row.direction == "income":
            bucket["income"] += row.amount
        elif row.direction == "expense":
            bucket["expense"] += row.amount
        elif row.direction == "transfer_in":
            bucket["transfer_in"] += row.amount
        elif row.direction == "transfer_out":
            bucket["transfer_out"] += row.amount
        elif row.direction == "notice":
            bucket["notices"] += 1
        elif row.direction == "ignored":
            bucket["ignored"] += 1
    data = []
    for month in sorted(monthly):
        bucket = monthly[month]
        income = bucket["income"]
        expense = bucket["expense"]
        data.append([
            month,
            fmt_decimal(income),
            fmt_decimal(expense),
            fmt_decimal(bucket["transfer_in"]),
            fmt_decimal(bucket["transfer_out"]),
            fmt_decimal(income - expense),
            int(bucket["notices"]),
            int(bucket["ignored"]),
        ])
    return data


def summarize_categories(rows: list[LedgerRow]) -> list[list[object]]:
    """Generate category-wise expense summary."""
    from src.utils.text import fmt_decimal
    from decimal import Decimal
    totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    for row in rows:
        if row.direction == "expense" and row.amount is not None and row.currency == "BDT":
            totals[(row.month, row.category or "uncategorized")] += row.amount
    return [[month, category, fmt_decimal(amount)] for (month, category), amount in sorted(totals.items())]


def summarize_accounts(rows: list[LedgerRow]) -> list[list[object]]:
    """Generate account-wise summary."""
    from src.utils.text import fmt_decimal
    from decimal import Decimal
    totals: dict[tuple[str, str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    for row in rows:
        if row.amount is not None and row.currency == "BDT" and row.direction in {"income", "expense", "transfer_in", "transfer_out"}:
            totals[(row.source, row.account, row.direction)] += row.amount
    return [[source, account, direction, fmt_decimal(amount)] for (source, account, direction), amount in sorted(totals.items())]
