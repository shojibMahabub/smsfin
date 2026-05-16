"""NRB Bank SMS parser."""

import re
from typing import Optional

from src.models.ledger import LedgerRow
from src.parsers.base import make_row, money_match
from src.utils.text import normalize_text, parse_amount


def parse_nrb(raw: dict[str, str]) -> Optional[LedgerRow]:
    """Parse NRB Bank SMS."""
    text = normalize_text(raw["Content"])
    if re.search(r"one time password|otp", text, re.I):
        return None

    # Credit card bill
    bill = re.search(r"Credit Card Bill\s+([A-Z]{3}-\d{2}).*?Total Due:\s*Tk\s*([\d, ]+(?:\.\d+)?)", text, re.I)
    if bill:
        return make_row(
            raw,
            "bill_statement",
            parse_amount(bill.group(2)),
            merchant_or_counterparty=f"NRB Credit Card Bill {bill.group(1)}",
            category="credit card bill",
            direction="notice",
            confidence="high",
            review_flag="yes",
            review_reason="statement_not_counted_in_totals",
        )

    # Minimum due notice
    due_notice = re.search(r"min due\s+Tk\.?\s*([\d, ]+(?:\.\d+)?)", text, re.I)
    if due_notice:
        return make_row(
            raw,
            "bill_reminder",
            parse_amount(due_notice.group(1)),
            merchant_or_counterparty="NRB credit card minimum due reminder",
            category="credit card bill",
            direction="notice",
            confidence="medium",
            review_flag="yes",
            review_reason="reminder_not_counted_in_totals",
        )

    # Purchase
    purchase = re.search(r"(?:purchased|Mail/Phone Order)\s+BDT\s*([\d, ]+(?:\.\d+)?)\s+on\s+.*?\s+from\s+(.+?)\s+using card", text, re.I)
    if purchase:
        merchant = purchase.group(2).strip()
        return make_row(
            raw,
            "purchase",
            parse_amount(purchase.group(1)),
            merchant_or_counterparty=merchant,
            direction="expense",
            confidence="high",
        )

    # Card payment
    payment = re.search(r"payment of\s+BDT\s*([\d, ]+(?:\.\d+)?)\s+of card", text, re.I)
    if payment:
        return make_row(
            raw,
            "card_payment",
            parse_amount(payment.group(1)),
            merchant_or_counterparty="NRB credit card payment",
            category="credit card payment",
            direction="transfer_in",
            confidence="high",
        )

    # Reversal
    reversal = re.search(r"Transaction reversed\s+BDT\s*([\d, ]+(?:\.\d+)?)\s+.*?\s+from\s+(.+?)\s+\.", text, re.I)
    if reversal:
        return make_row(
            raw,
            "reversal",
            parse_amount(reversal.group(1)),
            merchant_or_counterparty=reversal.group(2).strip(),
            category="reversal",
            direction="income",
            confidence="medium",
            review_flag="yes",
            review_reason="card_reversal_confirm_effect_on_totals",
        )

    return None
