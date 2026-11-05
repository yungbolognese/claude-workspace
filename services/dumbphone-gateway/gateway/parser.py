"""Turn short, typo-prone T9 text into structured commands.

The grammar is deliberately tiny and forgiving: single keywords, case-insensitive,
with a few synonyms. Anything that doesn't match becomes UNKNOWN, which the
router treats as an answer to a pending question (e.g. "what's your pickup
address?") before giving up.
"""

import re
from dataclasses import dataclass, field

RIDE_WORDS = r"(?:ride|cab|taxi|car|uber|lyft)"

# Commands that must be the whole message, so an address like "Status Ave"
# typed as an answer is not mistaken for a command.
EXACT = {
    "HELP": {"help", "menu", "?", "info", "commands"},
    "STATUS": {"status", "where", "eta", "wheres my ride", "where is my ride"},
    "CANCEL": {"cancel", "cancel ride"},
    "PLACES": {"places", "saved", "list"},
    "NO": {"no", "n", "nope", "nevermind", "never mind"},
}

YES_RE = re.compile(r"^(?:yes|y|yep|yeah|ok|okay|confirm|book)(?:\s+(?P<pin>\d{4,6}))?$")
RIDE_RE = re.compile(rf"^{RIDE_WORDS}\b\s*(?P<rest>.*)$", re.I)
SAVE_RE = re.compile(r"^save\s+(?P<name>[a-z0-9_-]{1,20})\s+(?P<address>.+)$")
FORGET_RE = re.compile(r"^(?:forget|delete|remove)\s+(?P<name>[a-z0-9_-]{1,20})$")
FROM_TO_RE = re.compile(r"^(?:from\s+)?(?P<pickup>.+?)\s+(?:to|->|>)\s+(?P<dropoff>.+)$", re.I)


@dataclass
class Command:
    name: str
    args: dict = field(default_factory=dict)
    raw: str = ""


def _clean(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text.rstrip(".!")


def _parse_ride(rest: str) -> dict:
    rest = rest.strip()
    if not rest:
        return {}
    m = FROM_TO_RE.match(rest)
    if m:
        return {"pickup": m["pickup"].strip(), "dropoff": m["dropoff"].strip()}
    lower = rest.lower()
    if lower.startswith("from "):
        return {"pickup": rest[5:].strip()}
    if lower.startswith("to "):
        return {"dropoff": rest[3:].strip()}
    return {"dropoff": rest}


def parse(text: str) -> Command:
    raw = (text or "").strip()
    t = _clean(raw)

    for name, words in EXACT.items():
        if t in words:
            return Command(name, raw=raw)

    m = YES_RE.match(t)
    if m:
        return Command("YES", {"pin": m["pin"]} if m["pin"] else {}, raw=raw)

    # Match RIDE on the original text so addresses keep their capitalization.
    m = RIDE_RE.match(re.sub(r"\s+", " ", raw).rstrip(".!"))
    if m:
        return Command("RIDE", _parse_ride(m["rest"]), raw=raw)

    m = SAVE_RE.match(t)
    if m:
        # Keep the address as typed (minus the keyword and name) for geocoding.
        address = re.sub(r"^\s*save\s+\S+\s+", "", raw, flags=re.I).strip()
        return Command("SAVE", {"name": m["name"], "address": address}, raw=raw)

    m = FORGET_RE.match(t)
    if m:
        return Command("FORGET", {"name": m["name"]}, raw=raw)

    return Command("UNKNOWN", raw=raw)
