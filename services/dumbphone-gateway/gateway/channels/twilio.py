"""Twilio plumbing shared by SMS and voice: webhook parsing, request signature
validation, TwiML rendering, and outbound SMS for push notifications."""

import base64
import hashlib
import hmac
import logging
import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Tuple
from xml.sax.saxutils import escape, quoteattr

from ..http import request_json

log = logging.getLogger(__name__)


def parse_form(body: bytes) -> Dict[str, str]:
    parsed = urllib.parse.parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
    return {k: v[0] for k, v in parsed.items()}


def compute_signature(auth_token: str, url: str, params: Dict[str, str]) -> str:
    """Twilio's X-Twilio-Signature: HMAC-SHA1 over the full URL followed by
    every POST parameter (sorted by name) as name+value, base64-encoded."""
    payload = url + "".join(k + params[k] for k in sorted(params))
    digest = hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def validate_signature(auth_token: str, url: str, params: Dict[str, str], signature: str) -> bool:
    if not (auth_token and signature):
        return False
    return hmac.compare_digest(compute_signature(auth_token, url, params), signature)


# -- TwiML -------------------------------------------------------------------
XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'


def response(*parts: str) -> str:
    return f"{XML_HEADER}<Response>{''.join(parts)}</Response>"


def message(text: str) -> str:
    return f"<Message>{escape(text)}</Message>"


def say(text: str) -> str:
    return f"<Say>{escape(text)}</Say>"


def gather(inner: str, attrs: Iterable[Tuple[str, str]]) -> str:
    rendered = "".join(f" {k}={quoteattr(str(v))}" for k, v in attrs)
    return f"<Gather{rendered}>{inner}</Gather>"


def hangup() -> str:
    return "<Hangup/>"


# -- outbound SMS ------------------------------------------------------------
class Sender(ABC):
    @abstractmethod
    def send(self, to: str, body: str) -> None: ...


class TwilioSender(Sender):
    def __init__(self, account_sid: str, auth_token: str, from_number: str, http=request_json):
        self.account_sid, self.auth_token, self.from_number = account_sid, auth_token, from_number
        self.http = http

    def send(self, to, body):
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        self.http("POST", url, form={"To": to, "From": self.from_number, "Body": body},
                  basic_auth=(self.account_sid, self.auth_token))


class ConsoleSender(Sender):
    def __init__(self, prefix: str = "[push]"):
        self.prefix = prefix

    def send(self, to, body):
        print(f"\n{self.prefix} to {to}: {body}", flush=True)


class MemorySender(Sender):
    def __init__(self):
        self.sent: List[Tuple[str, str]] = []

    def send(self, to, body):
        self.sent.append((to, body))
