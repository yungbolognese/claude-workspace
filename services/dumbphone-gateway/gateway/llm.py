"""Optional: understand free text ("can u get me a car to the airport") by asking a
local Ollama model to rewrite it into the command grammar. Runs on your own
hardware, so message text never leaves the machine.

The model can only *suggest* a command; the router re-parses the suggestion and
only accepts safe commands (see router.LLM_ALLOWED). Bookings still need YES.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from .http import request_json

log = logging.getLogger(__name__)

PROMPT = """You convert text messages into commands for an SMS service used from basic phones.
Valid commands:
RIDE <destination>
RIDE from <pickup> to <destination>
STATUS
PLACES
MENU
Copy places and addresses exactly as written; never invent or complete them.
If the message is not clearly one of these, use UNKNOWN.
Reply as JSON: {"command": "<command>"}

Message: """


class IntentRewriter(ABC):
    @abstractmethod
    def rewrite(self, text: str) -> Optional[str]: ...


class OllamaRewriter(IntentRewriter):
    def __init__(self, url: str, model: str, http=request_json, timeout: float = 20):
        self.url = url.rstrip("/")
        self.model = model
        self.http = http
        self.timeout = timeout

    def rewrite(self, text: str) -> Optional[str]:
        try:
            resp = self.http(
                "POST",
                self.url + "/api/generate",
                json_body={
                    "model": self.model,
                    "prompt": PROMPT + text[:300],
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0},
                },
                timeout=self.timeout,
            )
            command = str(json.loads(resp["response"]).get("command", "")).strip()
        except Exception:
            log.exception("LLM rewrite failed")
            return None
        if not command or command.upper() == "UNKNOWN":
            return None
        return command
