"""DBBL (Dutch-Bangla Bank) SMS parser — sender ID 16216."""

import re
from typing import Optional

from src.models.ledger import LedgerRow
from src.parsers.base import make_row
from src.utils.text import normalize_text, parse_amount


def parse_dbbl(raw: dict[str, str]) -> Optional[LedgerRow]:
    """Parse DBBL credit card SMS."""
    text = normalize_text(raw["Content"])
    if re.search(r"declined|otp|one time password", text, re.I):
        return None

    bill = re.search(
        r"DBBL VISA Platinum TQ Card\s+\S+\s+bill for\s+(\w+-\d+)\s+is\s*:BDT([\d, ]+(?:\.\d+)?)",
        text,
        re.I,
    )
    if bill:
        return make_row(
            raw,
            "bill_statement",
            parse_amount(bill.group(2)),
            merchant_or_counterparty=f"DBBL card bill {bill.group(1)}",
            category="credit card bill",
            direction="notice",
            confidence="high",
            review_flag="yes",
            review_reason="statement_not_counted_in_totals",
        )

    card_payment_bdt = re.search(
        r"Payment of BDT\s*([\d, ]+(?:\.\d+)?)\s+against DBBL Cr\.?\s*Card",
        text,
        re.I,
    )
    if card_payment_bdt:
        return make_row(
            raw,
            "card_payment",
            parse_amount(card_payment_bdt.group(1)),
            merchant_or_counterparty="DBBL credit card payment",
            category="credit card payment",
            direction="transfer_in",
            confidence="high",
        )

    card_payment_usd = re.search(
        r"Payment of USD\s*([\d, ]+(?:\.\d+)?)\s+against DBBL Cr",
        text,
        re.I,
    )
    if card_payment_usd:
        return make_row(
            raw,
            "card_payment",
            parse_amount(card_payment_usd.group(1)),
            merchant_or_counterparty="DBBL credit card payment",
            category="credit card payment",
            direction="transfer_in",
            currency="USD",
            confidence="high",
        )

    purchase_bdt = re.search(
        r"Thank you for using DBBL Cr\.?\s*Card#\s*\S+\s+for BDT\s*([\d, ]+(?:\.\d+)?)\s+at\s+(.+?)\s+on\s+",
        text,
        re.I,
    )
    if purchase_bdt:
        return make_row(
            raw,
            "purchase",
            parse_amount(purchase_bdt.group(1)),
            merchant_or_counterparty=purchase_bdt.group(2).strip(),
            direction="expense",
            confidence="high",
        )

    purchase_usd = re.search(
        r"Thank you for using DBBL Cr\.?\s*Card#\s*\S+\s+for USD\s*([\d, ]+(?:\.\d+)?)\s+at\s+(.+?)\s+on\s+",
        text,
        re.I,
    )
    if purchase_usd:
        return make_row(
            raw,
            "purchase",
            parse_amount(purchase_usd.group(1)),
            merchant_or_counterparty=purchase_usd.group(2).strip(),
            direction="expense",
            currency="USD",
            confidence="high",
        )

    credited = re.search(
        r"DBBL Cr\.?\s*Card\s+\S+\s+has been credited\s+\(([^)]+)\)\s+by BDT\s*([\d, ]+(?:\.\d+)?)",
        text,
        re.I,
    )
    if credited:
        return make_row(
            raw,
            "bank_credit",
            parse_amount(credited.group(2)),
            merchant_or_counterparty=credited.group(1).strip(),
            direction="income",
            confidence="high",
        )

    debited = re.search(
        r"DBBL Cr\.?\s*Card\s+\S+\s+has been debited\s+\(([^)]+)\)\s+by BDT\s*([\d, ]+(?:\.\d+)?)",
        text,
        re.I,
    )
    if debited:
        return make_row(
            raw,
            "bank_debit",
            parse_amount(debited.group(2)),
            merchant_or_counterparty=debited.group(1).strip(),
            direction="expense",
            confidence="high",
        )

    return None
