"""bKash SMS parser."""

import re
from typing import Optional

from src.models.ledger import LedgerRow
from src.parsers.base import make_row
from src.utils.text import normalize_text, parse_amount


def parse_bkash(raw: dict[str, str]) -> Optional[LedgerRow]:
    """Parse bKash SMS (sender: bKash, bKashNotice)."""
    text = normalize_text(raw["Content"])
    if re.search(r"otp|verification code", text, re.I):
        return None

    deposit_ib = re.search(
        r"received deposit from iBanking of Tk\s*([\d, ]+(?:\.\d+)?)\s+from\s+(.+?)\.",
        text,
        re.I,
    )
    if deposit_ib:
        return make_row(
            raw,
            "transfer_in",
            parse_amount(deposit_ib.group(1)),
            merchant_or_counterparty=deposit_ib.group(2).strip(),
            direction="income",
            confidence="high",
        )

    deposit_card = re.search(
        r"received deposit of Tk\s*([\d, ]+(?:\.\d+)?)\s+from\s+([^.]+)",
        text,
        re.I,
    )
    if deposit_card:
        return make_row(
            raw,
            "transfer_in",
            parse_amount(deposit_card.group(1)),
            merchant_or_counterparty=deposit_card.group(2).strip(),
            direction="income",
            confidence="high",
        )

    received = re.search(
        r"You have received Tk\s*([\d, ]+(?:\.\d+)?)\s+from\s+(.+?)\.\s+Fee",
        text,
        re.I,
    )
    if received:
        return make_row(
            raw,
            "transfer_in",
            parse_amount(received.group(1)),
            merchant_or_counterparty=received.group(2).strip(),
            direction="income",
            confidence="high",
        )

    payment = re.search(
        r"Payment of Tk\s*([\d, ]+(?:\.\d+)?)\s+to\s+(.+?)\s+is successful",
        text,
        re.I,
    )
    if payment:
        return make_row(
            raw,
            "purchase",
            parse_amount(payment.group(1)),
            merchant_or_counterparty=payment.group(2).strip(),
            direction="expense",
            confidence="high",
        )

    bill = re.search(
        r"Bill successfully paid\..*?Biller:\s*([^;\n]+).*?Amount:\s*Tk\s*([\d, ]+(?:\.\d+)?)",
        text,
        re.I | re.S,
    )
    if bill:
        return make_row(
            raw,
            "bill_payment",
            parse_amount(bill.group(2)),
            merchant_or_counterparty=bill.group(1).strip(),
            category="utilities",
            direction="expense",
            confidence="high",
        )

    subscription = re.search(
        r"Scheduled cycle payment was successful for bKash subscription with\s+(.+?)\s+for\s+.*?of\s+([\d, ]+(?:\.\d+)?)\s*tk",
        text,
        re.I,
    )
    if subscription:
        return make_row(
            raw,
            "subscription_payment",
            parse_amount(subscription.group(2)),
            merchant_or_counterparty=subscription.group(1).strip(),
            category="subscriptions",
            direction="expense",
            confidence="medium",
        )

    cash_out = re.search(
        r"Cash Out Tk\s*([\d, ]+(?:\.\d+)?)\s+from\s+(.+?)\s+is successful",
        text,
        re.I,
    )
    if cash_out:
        return make_row(
            raw,
            "cash_out",
            parse_amount(cash_out.group(1)),
            merchant_or_counterparty=cash_out.group(2).strip(),
            category="cash",
            direction="expense",
            confidence="high",
        )

    send_money = re.search(
        r"Send Money Tk\s*([\d, ]+(?:\.\d+)?)\s+to\s+(.+?)\s+successful",
        text,
        re.I,
    )
    if send_money:
        return make_row(
            raw,
            "transfer_out",
            parse_amount(send_money.group(1)),
            merchant_or_counterparty=send_money.group(2).strip(),
            direction="expense",
            confidence="high",
        )

    return None
