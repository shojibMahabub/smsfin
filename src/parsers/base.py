"""Base parser functionality."""

import re
from decimal import Decimal
from typing import Optional

from src.models.ledger import LedgerRow
from src.utils.text import parse_amount, normalize_text
from src.utils.date import parse_sms_datetime


def account_from_text(text: str, source: str) -> tuple[str, str]:
    """Extract account information from text."""
    card = re.search(r"(?:card(?: no\.?|#)?|Card:|Card#)\s*([*\dXx-]+)", text, re.I)
    account = re.search(r"AC:([*\d]+)", text, re.I)
    if card:
        hint = card.group(1)
        return f"{source} card {hint[-4:]}", hint
    if account:
        hint = account.group(1)
        return f"{source} account {hint[-5:]}", hint
    if source in {"bKash", "bKashNotice"}:
        return "bKash wallet", ""
    return source, ""


def extract_balance(text: str) -> Optional[Decimal]:
    """Extract balance from text."""
    match = re.search(r"(?:Balance|Current balance|Available limit)\s*:?\s*(?:BDT|Tk|USD)?\.?\s*([\d, ]+(?:\.\d+)?)", text, re.I)
    return parse_amount(match.group(1)) if match else None


def extract_trx_id(text: str) -> str:
    """Extract transaction ID from text."""
    match = re.search(r"TrxID:?\s*([A-Z0-9]+)", text, re.I)
    if match:
        return match.group(1)
    match = re.search(r"transactionId\s*:?\s*([A-Z0-9]+)", text, re.I)
    return match.group(1) if match else ""


def categorize(merchant: str, tx_type: str, text: str) -> str:
    """Categorize transaction based on merchant and type."""
    from src.models.ledger import CATEGORY_RULES
    blob = f"{merchant} {tx_type} {text}".upper()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in blob for keyword in keywords):
            return category
    if tx_type in {"transfer_in", "transfer_out", "card_payment"}:
        return "transfer"
    if tx_type == "cashback":
        return "cashback"
    if tx_type == "bank_credit":
        return "income"
    if tx_type == "bank_debit":
        return "bank payment"
    if tx_type == "purchase":
        return "shopping"
    return "uncategorized"


def make_row(raw: dict[str, str], tx_type: str, amount: Optional[Decimal], **kwargs) -> LedgerRow:
    """Create a ledger row from raw data."""
    dt = parse_sms_datetime(raw.get("Date", ""))
    text = normalize_text(raw.get("Content", ""))
    source = raw.get("From", "")
    account, hint = account_from_text(text, source)
    row = LedgerRow(
        date=dt.strftime("%Y-%m-%d") if dt else "",
        time=dt.strftime("%H:%M:%S") if dt else "",
        month=dt.strftime("%Y-%m") if dt else "",
        source=source,
        account=kwargs.pop("account", account),
        type=tx_type,
        amount=amount,
        currency=kwargs.pop("currency", "BDT"),
        balance_after=kwargs.pop("balance_after", extract_balance(text)),
        transaction_id=kwargs.pop("transaction_id", extract_trx_id(text)),
        card_or_account_hint=kwargs.pop("card_or_account_hint", hint),
        original_sms=text,
        **kwargs,
    )
    if not row.category:
        row.category = categorize(row.merchant_or_counterparty, row.type, text)
    if not row.date or row.amount is None:
        row.review_flag = "yes"
        row.review_reason = append_reason(row.review_reason, "missing_date_or_amount")
        row.confidence = "low"
    return row


def money_match(text: str, prefix: str = r"(?:BDT|Tk|USD|৳)") -> Optional[re.Match[str]]:
    """Find money amounts in text."""
    return re.search(prefix + r"\.?\s*([\d, ]+(?:\.\d+)?)", text, re.I)


def append_reason(existing: str, reason: str) -> str:
    """Append a reason to existing reasons."""
    if not existing:
        return reason
    parts = set(existing.split("; "))
    if reason not in parts:
        return f"{existing}; {reason}"
    return existing
