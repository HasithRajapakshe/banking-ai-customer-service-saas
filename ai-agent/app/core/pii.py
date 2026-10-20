"""Mask personal data in log output.

Card numbers keep their last 4 digits, NIC numbers their last 2, phone
numbers their last 2. Applied as a logging filter so every log line written
by the service (including third-party libraries) is masked.
"""

import logging
import re

# 13-19 digits, optionally grouped by spaces or dashes (PANs; also masks long
# account numbers, which is acceptable for logs).
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
# Sri Lankan NIC: old format 9 digits + V/X, new format 12 digits.
NIC_RE = re.compile(r"(?<![\dA-Za-z])(?:\d{9}[VvXx]|\d{12})(?![\dA-Za-z])")
# Sri Lankan mobile numbers: 07X XXX XXXX, +94 7X XXX XXXX, 0094...
PHONE_RE = re.compile(r"(?<!\d)(?:\+94|0094|0)[ -]?7\d(?:[ -]?\d){7}(?!\d)")


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def _mask_card(match: re.Match) -> str:
    digits = _digits(match.group(0))
    return "*" * (len(digits) - 4) + digits[-4:]


def _mask_keep(n: int):
    def mask(match: re.Match) -> str:
        value = match.group(0)
        return "*" * (len(value) - n) + value[-n:]

    return mask


def mask_pii(text: str) -> str:
    # NIC before card: a 12-digit NIC would otherwise match as a card number.
    text = NIC_RE.sub(_mask_keep(2), text)
    text = PHONE_RE.sub(lambda m: "*" * (len(_digits(m.group(0))) - 2) + _digits(m.group(0))[-2:], text)
    text = CARD_RE.sub(_mask_card, text)
    return text


class PiiMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        masked = mask_pii(message)
        if masked != message:
            record.msg = masked
            record.args = None
        return True


def install_pii_masking() -> None:
    """Attach the filter to the root and uvicorn handlers."""
    pii_filter = PiiMaskingFilter()
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        for handler in logging.getLogger(name).handlers:
            if not any(isinstance(f, PiiMaskingFilter) for f in handler.filters):
                handler.addFilter(pii_filter)
