"""Ollama-based filter with parallel processing.

Only unknown senders (not in FINANCIAL_SENDERS with True) go to Ollama.
Known financial senders are classified as transaction directly.
"""

import json
import re
import logging
import subprocess
import time
from typing import Any
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from src.models.senders import is_financial_sender, Classification, FINANCIAL_SENDERS

logger = logging.getLogger(__name__)

FILTER_PROMPT = """Classify this SMS. Return ONLY JSON: {"type": "transaction"|"otp"|"login"|"promotional"|"chat"|"unknown", "confidence": 0.0-1.0}"""


def extract_json(text: str) -> dict | None:
    """Extract JSON from text."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{.+\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def classify_single(args: tuple) -> tuple:
    """Classify a single SMS using Ollama (for parallel execution)."""
    index, content, sender, model = args
    prompt = f"{FILTER_PROMPT}\n\nSMS: {content[:300]}\nFrom: {sender}"

    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=45
        )
        if result.returncode == 0:
            parsed = extract_json(result.stdout.strip())
            if parsed:
                sms_type = parsed.get("type", "unknown")
                valid = ("transaction", "otp", "login", "promotional", "chat", "unknown")
                if sms_type not in valid:
                    sms_type = "unknown"
                return index, sms_type, parsed.get("confidence", 0.5)
    except Exception as e:
        pass

    return index, "unknown", 0.3


class OllamaFilter:
    """Parallel Ollama classifier."""

    name = "ollama"
    enabled = True

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self.model = self.config.get("model", "gemma4:e4b")
        self.workers = self.config.get("workers", multiprocessing.cpu_count())

    def classify_batch(self, raw_rows: list, show_progress: bool = True) -> list[Classification]:
        """Classify all rows - known senders skip Ollama."""
        total = len(raw_rows)
        results: list[Classification | None] = [None] * total

        # Separate known vs unknown senders
        known_indices = []
        unknown_indices = []
        unknown_args = []

        for i, raw in enumerate(raw_rows):
            sender = raw.get("From", "")
            if is_financial_sender(sender):
                # TRUE senders go to Ollama for classification
                unknown_indices.append(i)
                content = raw.get("Content", "")
                unknown_args.append((i, content, sender, self.model))
            else:
                # Non-TRUE senders are promotional (skip Ollama)
                known_indices.append(i)
                results[i] = Classification(
                    type="promotional",
                    confidence=0.95,
                    reason=f"Non-financial: {sender}"
                )

        if show_progress:
            print(f"\n✓ Non-financial senders: {len(known_indices)} ({len(known_indices)*100//total}%)")
            print(f"⚡ Financial (TRUE): {len(unknown_indices)} ({len(unknown_indices)*100//total}%)")

        # Process TRUE senders in parallel via Ollama
        if unknown_args and show_progress:
            print(f"⚡ Running {self.workers} parallel Ollama agents on {len(unknown_args)} financial SMS...")

        start_time = time.time()

        if unknown_args:
            # Use ProcessPoolExecutor for true parallelism
            try:
                with ProcessPoolExecutor(max_workers=self.workers) as executor:
                    futures = {executor.submit(classify_single, arg): arg[0] for arg in unknown_args}

                    completed = 0
                    for future in as_completed(futures):
                        idx, sms_type, conf = future.result()
                        results[idx] = Classification(
                            type=sms_type,
                            confidence=conf,
                            reason=f"Ollama: {sms_type}"
                        )
                        completed += 1

                        if show_progress and completed % 10 == 0:
                            elapsed = time.time() - start_time
                            rate = completed / elapsed if elapsed > 0 else 0
                            eta = (len(unknown_indices) - completed) / rate if rate > 0 else 0
                            pct = completed * 100 // len(unknown_indices)
                            print(f"\r  [{pct}% | {completed}/{len(unknown_indices)}] ETA: {eta:.0f}s", end="", flush=True)

            except Exception as e:
                logger.error(f"Parallel processing failed: {e}")
                # Fallback to sequential
                for arg in unknown_args:
                    idx, sms_type, conf = classify_single(arg)
                    results[idx] = Classification(
                        type=sms_type,
                        confidence=conf,
                        reason=f"Ollama: {sms_type}"
                    )

        if show_progress:
            elapsed = time.time() - start_time
            print(f"\n✓ Classification done in {elapsed:.1f}s")

        return results

    def classify(self, raw: dict) -> Classification:
        """Single classification."""
        sender = raw.get("From", "")
        if is_financial_sender(sender):
            # TRUE senders go to Ollama for classification
            idx, sms_type, conf = classify_single((0, raw.get("Content", ""), sender, self.model))
            return Classification(type=sms_type, confidence=conf, reason=f"Ollama: {sms_type}")
        else:
            # Non-TRUE senders are promotional
            return Classification(type="promotional", confidence=0.95, reason=f"Non-financial: {sender}")


plugin = OllamaFilter
