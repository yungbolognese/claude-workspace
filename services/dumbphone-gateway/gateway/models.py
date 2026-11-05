"""Plain data types shared across the gateway."""

import hashlib
import hmac
import os
import re
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Place:
    address: str
    name: Optional[str] = None  # saved-place name like "home"
    lat: Optional[float] = None
    lng: Optional[float] = None

    @property
    def has_coords(self) -> bool:
        return self.lat is not None and self.lng is not None

    def short(self, limit: int = 32) -> str:
        """Compact label that fits in an SMS."""
        if self.name:
            return self.name.upper()
        return self.address if len(self.address) <= limit else self.address[: limit - 1] + "…"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Place":
        return cls(**d)


@dataclass
class User:
    phone: str
    name: str = ""
    pin_hash: Optional[str] = None


@dataclass
class Inbound:
    phone: str
    text: str
    channel: str = "sms"  # sms | voice


def normalize_phone(raw: str, default_cc: str = "1") -> str:
    """Best-effort E.164 normalization ("(555) 123-4567" -> "+15551234567")."""
    raw = (raw or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        raise ValueError(f"not a phone number: {raw!r}")
    if raw.startswith("+"):
        return "+" + digits
    if digits.startswith("00"):
        return "+" + digits[2:]
    if default_cc and digits.startswith(default_cc) and len(digits) > 10:
        return "+" + digits
    return "+" + default_cc + digits


# PINs are short, so a hash only slows offline guessing; the real protection
# is the attempt limit. Still, never store them in plain text.
_PIN_ITERATIONS = 100_000


def hash_pin(pin: str) -> str:
    if not re.fullmatch(r"\d{4,6}", pin or ""):
        raise ValueError("PIN must be 4-6 digits")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, _PIN_ITERATIONS)
    return salt.hex() + "$" + digest.hex()


def verify_pin(pin: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
    except (AttributeError, ValueError):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", (pin or "").encode(), bytes.fromhex(salt_hex), _PIN_ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)
