"""Dhaka Bank SMS parser."""

import re
from typing import Optional

from src.models.ledger import LedgerRow
from src.parsers.base import make_row, money_match
from src.utils.text import normalize_text, parse_amount


def parse_dhaka_bank(raw: dict[str, str]) -> Optional[LedgerRow]:
    """Parse Dhaka Bank SMS (sender: DHAKA BANK, DHAKABANK.)."""
    text = normalize_text(raw["Content"])
    if re.search(r"one time password|otp|পিন|ওটিপি", text, re.I):
        return None

    # Skip promotional Bengali-only alerts without transaction amounts
    if not re.search(r"(?:Tk|BDT)\s*[\d,]", text, re.I):
        return None

    credited = re.search(
        r"Tk\s*([\d, ]+(?:\.\d+)?)\s+has been credited to your AC:([*\d]+)(?:\s+as\s+([^.\n]+))?",
        text,
        re.I,
    )
    if credited:
        purpose = (credited.group(3) or "credit").strip()
        return make_row(
            raw,
            "bank_credit",
            parse_amount(credited.group(1)),
            merchant_or_counterparty=purpose,
            direction="income",
            confidence="high",
            card_or_account_hint=credited.group(2),
        )

    debited = re.search(
        r"Tk\s*([\d, ]+(?:\.\d+)?)\s+has been debited from your AC:([*\d]+)(?:\s+using\s+([^.\n]+))?",
        text,
        re.I,
    )
    if debited:
        channel = (debited.group(3) or "debit").strip()
        return make_row(
            raw,
            "bank_debit",
            parse_amount(debited.group(1)),
            merchant_or_counterparty=channel,
            direction="expense",
            confidence="high",
            card_or_account_hint=debited.group(2),
        )

    withdrawal = re.search(
        r"Cash Withdrawal\s+BDT\s*([\d, ]+(?:\.\d+)?)\s+at\s+(.+?)(?:\s+Card:|\s+Balance:)",
        text,
        re.I,
    )
    if withdrawal:
        return make_row(
            raw,
            "cash_withdrawal",
            parse_amount(withdrawal.group(1)),
            merchant_or_counterparty=withdrawal.group(2).strip(),
            category="cash",
            direction="expense",
            confidence="high",
        )

    purchase = re.search(
        r"Purchase\s+BDT\s*([\d, ]+(?:\.\d+)?)\s+at\s+(.+?)(?:\s+Card:|\s+Balance:)",
        text,
        re.I,
    )
    if purchase:
        return make_row(
            raw,
            "purchase",
            parse_amount(purchase.group(1)),
            merchant_or_counterparty=purchase.group(2).strip(),
            direction="expense",
            confidence="high",
        )

    fund_transfer = re.search(
        r"Fund Transfer\s+BDT\s*([\d, ]+(?:\.\d+)?).*?Beneficiary:\s*(\d+)",
        text,
        re.I | re.S,
    )
    if fund_transfer:
        return make_row(
            raw,
            "transfer_out",
            parse_amount(fund_transfer.group(1)),
            merchant_or_counterparty=f"Beneficiary {fund_transfer.group(2)}",
            direction="expense",
            confidence="medium",
        )

    card_payment = re.search(
        r"payment of\s+BDT\s*([\d, ]+(?:\.\d+)?)\s+to your Dhaka Bank Credit Card",
        text,
        re.I,
    )
    if card_payment:
        return make_row(
            raw,
            "card_payment",
            parse_amount(card_payment.group(1)),
            merchant_or_counterparty="Dhaka Bank credit card payment",
            category="credit card payment",
            direction="transfer_in",
            confidence="high",
        )

    generic = money_match(text, r"(?:BDT|Tk)")
    if generic and re.search(r"debit|withdrawal|purchase|payment", text, re.I):
        return make_row(
            raw,
            "bank_debit",
            parse_amount(generic.group(1)),
            merchant_or_counterparty="Dhaka Bank",
            direction="expense",
            confidence="low",
            review_flag="yes",
            review_reason="generic_dhaka_bank_match",
        )

    return None
