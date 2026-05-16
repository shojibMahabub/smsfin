"""Date parsing utilities."""

import re
from datetime import datetime


def parse_sms_datetime(value: str) -> datetime | None:
    """Parse datetime from SMS message."""
    value = re.sub(r"\s+", " ", value.strip())
    value = re.sub(r"(?i)(\d{1,2}:\d{2})(AM|PM)$", r"\1 \2", value)
    formats = [
        "%B %d, %Y at %I:%M %p",
        "%B %d, %Y at %I:%M:%S %p",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None
