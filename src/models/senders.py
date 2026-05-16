"""Senders configuration and Classification model."""

from dataclasses import dataclass


@dataclass
class Classification:
    """Classification result for an SMS."""
    type: str  # transaction, otp, login, promotional, chat, unknown
    confidence: float = 0.5
    reason: str = ""

    def is_transaction(self) -> bool:
        return self.type == "transaction"


# Financial senders configuration
FINANCIAL_SENDERS = {
    # Banks - Credit Cards
    "NRB Bank": True,
    "16216": True,           # DBBL
    "DHAKA BANK": True,
    "DHAKABANK.": True,
    "ONE Bank.": True,

    # Mobile Banking
    "bKash": True,
    "bKashNotice": True,
    "bKash Offer": True,
    "NAGAD": True,

    # Mobile Operators (recharge) - disabled by default
    "Robi": False,
    "GP": False,
    "GP 250MIN": False,
    "GP10GB200TK": False,
    "GP20GB300TK": False,
    "GP 5GB100TK": False,
    "GP Bundle": False,
    "GP 300MIN": False,
    "GP10GB145TK": False,
    "GP25GB350TK": False,
    "GP 4GB100TK": False,
    "GP BILL": False,
    "GP Internet": False,
    "GP Postpaid": False,
    "GP Discount": False,
    "GP offer": False,
    "GPPOINTS": False,
    "GP Balance": False,
    "MYGPINFO": False,

    # Others
    "PathaoPay": True,
    "Meter Token": False,
    "1213": False,

    # Not financial
    "GovtInfo": False,
    "BTRC": False,
    "H CONNECT": False,
    "DailyShop": False,
    "My Usage": False,
    "DOMINOS": False,
    "SUNDARBAN": False,
    "RedX": False,
    "AMAZON": False,
    "MUNCHIES": False,
    "TAAGA": False,
    "Othoba": False,
    "SSLCOMMERZ": False,
    "FlexiLoad": False,
    "Offer Info": False,
}


def is_financial_sender(sender: str) -> bool:
    """Check if sender is a financial source (enabled in config)."""
    if sender in FINANCIAL_SENDERS:
        return FINANCIAL_SENDERS[sender]
    sender_upper = sender.upper()
    for key, enabled in FINANCIAL_SENDERS.items():
        if key.upper() in sender_upper or sender_upper in key.upper():
            return enabled
    return False
