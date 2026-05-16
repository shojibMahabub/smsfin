"""Ollama-based parser plugin for intelligent transaction parsing."""

import json
import logging
import subprocess
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from src.models.ledger import LedgerRow

logger = logging.getLogger(__name__)

PARSER_PROMPT = """You are a financial SMS parser. Extract transaction details from this SMS.

SMS from {sender}:
{content}

Extract as JSON (return null if not a transaction):
{{
  "date": "YYYY-MM-DD",
  "time": "HH:MM:SS",
  "amount": number,
  "currency": "BDT",
  "merchant_or_counterparty": "string",
  "type": "purchase|transfer_in|transfer_out|cashback|bank_credit|bank_debit|payment|withdrawal|refund",
  "direction": "expense|income|transfer_in|transfer_out",
  "category": "groceries|food|fuel|transport|utilities|shopping|transfer|cashback|income|uncategorized",
  "balance_after": number or null,
  "transaction_id": "string"
}}

Only return valid JSON, no explanation."""


class OllamaParser:
    """Ollama-powered transaction parser using local LLM."""

    name = "ollama"
    enabled = True

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self.model = self.config.get("model", "gemma4:e4b")
        self._regex_parser = None  # Fallback

    def _call_ollama(self, prompt: str) -> dict | None:
        """Call Ollama API."""
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                # Try to extract JSON
                if "{" in output:
                    start = output.find("{")
                    end = output.rfind("}") + 1
                    return json.loads(output[start:end])
            else:
                logger.warning(f"Ollama error: {result.stderr}")
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
        return None

    def _parse_date(self, date_str: str, time_str: str = "") -> tuple[str, str, str]:
        """Parse date string to date, time, month."""
        if not date_str:
            return "", "", ""

        try:
            # Try various formats
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    date = dt.strftime("%Y-%m-%d")
                    month = dt.strftime("%Y-%m")
                    time = time_str or dt.strftime("%H:%M:%S")
                    return date, time, month
                except ValueError:
                    continue
        except Exception:
            pass
        return "", "", ""

    def _parse_amount(self, value: Any) -> Optional[Decimal]:
        """Parse amount to Decimal."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            cleaned = value.replace(",", "").strip()
            try:
                return Decimal(cleaned)
            except InvalidOperation:
                return None
        return None

    def parse(self, raw: dict[str, str]) -> Optional[LedgerRow]:
        """Parse SMS using Ollama LLM."""
        content = raw.get("Content", "")
        sender = raw.get("From", "")

        # Build prompt
        prompt = PARSER_PROMPT.format(sender=sender, content=content[:500])

        # Call Ollama
        result = self._call_ollama(prompt)

        if not result:
            # Fallback to regex parser
            return self._fallback_parse(raw)

        try:
            date, time, month = self._parse_date(
                result.get("date", ""),
                result.get("time", "")
            )
            amount = self._parse_amount(result.get("amount"))

            row = LedgerRow(
                date=date,
                time=time,
                month=month,
                source=sender,
                account=sender,
                type=result.get("type", "unknown"),
                amount=amount,
                currency=result.get("currency", "BDT"),
                merchant_or_counterparty=result.get("merchant_or_counterparty", ""),
                category=result.get("category", "uncategorized"),
                direction=result.get("direction", "expense"),
                balance_after=self._parse_amount(result.get("balance_after")),
                transaction_id=result.get("transaction_id", ""),
                original_sms=content,
                confidence="medium",
            )

            # Mark for review if missing data
            if not date or amount is None:
                row.review_flag = "yes"
                row.review_reason = "missing_date_or_amount"
                row.confidence = "low"

            return row

        except Exception as e:
            logger.error(f"Failed to parse Ollama result: {e}")
            return self._fallback_parse(raw)

    def _fallback_parse(self, raw: dict) -> Optional[LedgerRow]:
        """Fallback to regex parser."""
        if self._regex_parser is None:
            from src.parsers.implementations.regex_parser import RegexParser
            self._regex_parser = RegexParser(self.config.get("regex_config"))
        return self._regex_parser.parse(raw)


plugin = OllamaParser
