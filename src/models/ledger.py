"""Ledger data models and types."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class LedgerRow:
    """Represents a single financial transaction."""
    date: str = ""
    time: str = ""
    month: str = ""
    source: str = ""
    account: str = ""
    type: str = ""
    amount: Optional[Decimal] = None
    currency: str = "BDT"
    merchant_or_counterparty: str = ""
    category: str = ""
    direction: str = ""
    balance_after: Optional[Decimal] = None
    transaction_id: str = ""
    card_or_account_hint: str = ""
    confidence: str = "medium"
    review_flag: str = "no"
    review_reason: str = ""
    original_sms: str = ""


# Ledger headers for Excel output
LEDGER_HEADERS = [
    "date",
    "time",
    "month",
    "source",
    "account",
    "type",
    "amount",
    "currency",
    "merchant_or_counterparty",
    "category",
    "direction",
    "balance_after",
    "transaction_id",
    "card_or_account_hint",
    "confidence",
    "review_flag",
    "review_reason",
    "original_sms",
]


# Category rules for automatic categorization
CATEGORY_RULES = [
    ("groceries", ["SHWAPNO", "DAILY SHOPPING", "SORKAR STORE", "HR TRADERS"]),
    ("fuel", ["FILLING STATION", "PETROL", "OCTANE", "CNG"]),
    ("pharmacy", ["PHARMA", "PHARMACY", "MEDICINE"]),
    ("food", ["FOODI", "CAFE", "RIO", "RESTAURANT", "KFC", "PIZZA", "PATHAO LIMITED", "DUE ADJUSTMENT"]),
    ("utilities", ["DPDC", "BILLER", "PREPAID", "METER TOKEN", "DESCO", "WASA"]),
    ("mobile recharge", ["GRAMEENPHONE", "MYGP", "ROBI", "BANGLALINK", "TELETALK", "AIRTEL", "MOBILE RECHARGE"]),
    ("charity", ["AS SUNNAH", "AS-SUNNAH", "FOUNDATION"]),
    ("transport", ["PATHAO", "UBER", "RIDE"]),
    ("subscriptions", ["NETFLIX", "SUBSCRIPTION", "GOOGLE", "APPLE", "TIGO"]),
    ("loan", ["DIGITAL LOAN", "LOAN REPAYMENT", "CITY BANK"]),
    ("fees", ["VAT", "ANNUAL FEE", "FEE"]),
    ("cash", ["ATM", "CASH WITHDRAWAL", "CASH OUT"]),
    ("wallet transfer", ["BKASH", "VISA CARD", "IBANKING", "NEXUSPAY"]),
    ("credit card payment", ["CREDIT CARD PAYMENT", "BILL PAY", "CARD PAYMENT"]),
]

