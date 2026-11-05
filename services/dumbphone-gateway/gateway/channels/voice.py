"""Voice IVR: for people who'd rather call than type on a keypad, or whose
phone can't text well. Keypresses and speech are converted into the same text
commands SMS uses, then the replies are read aloud.

Main menu: 1 = ride home, 2 = ride status, 3 = cancel ride, or just say where
you want to go ("the airport").
"""

from typing import Optional

from ..models import Inbound
from ..parser import parse
from ..router import Gateway
from . import twilio as tw

MENU = ("Press 1 for a ride home. Press 2 for your ride status. Press 3 to cancel a ride. "
        "Or say where you want to go.")
INPUT_PATH = "/voice/input"


class VoiceIVR:
    def __init__(self, gateway: Gateway, language: str = "en-US"):
        self.gateway = gateway
        self.language = language

    def incoming(self, phone: str) -> str:
        if self.gateway.store.get_user(self.gateway.normalize(phone)) is None:
            return tw.response(tw.say("This number isn't signed up for this service. Goodbye."), tw.hangup())
        return self._menu()

    def handle_input(self, phone: str, digits: str = "", speech: str = "") -> str:
        digits, speech = (digits or "").strip(), (speech or "").strip()
        session = self.gateway.current_session(phone)
        if session is None and digits == "0":
            return self._menu()
        text = self._to_text(session, digits, speech)
        if text is None:
            if session is None:
                return self._menu("Sorry, I didn't get that. ")
            return self._follow_up(phone, "Sorry, I didn't get that.")
        replies = self.gateway.handle(Inbound(phone=phone, text=text, channel="voice"))
        return self._follow_up(phone, " ".join(replies))

    # -- helpers -------------------------------------------------------------
    def _to_text(self, session, digits: str, speech: str) -> Optional[str]:
        if session and session.state == "confirm":
            if digits == "2":
                return "NO"
            if digits == "1":
                return "YES"
            if len(digits) >= 4:
                return f"YES {digits}"
            return speech or None
        if session:  # waiting for an address
            if digits == "0":
                return "NO"
            return speech or None
        if digits == "1":
            return "RIDE home"
        if digits == "2":
            return "STATUS"
        if digits == "3":
            return "CANCEL"
        if speech:
            # "the airport" -> "RIDE the airport"; "status" stays "status"
            return speech if parse(speech).name != "UNKNOWN" else f"RIDE {speech}"
        return None

    def _gather(self, prompt: str, *, digits_only_one: bool = True, speech: bool = True, pin: bool = False) -> str:
        attrs = [("action", INPUT_PATH), ("method", "POST"), ("timeout", "6"), ("language", self.language)]
        attrs.append(("input", "dtmf speech" if speech else "dtmf"))
        if speech:
            attrs.append(("speechTimeout", "auto"))
        if pin:
            attrs.append(("finishOnKey", "#"))
        elif digits_only_one:
            attrs.append(("numDigits", "1"))
        return tw.gather(tw.say(prompt), attrs)

    def _menu(self, prefix: str = "") -> str:
        return tw.response(self._gather(prefix + MENU), tw.say("Goodbye."), tw.hangup())

    def _follow_up(self, phone: str, spoken: str) -> str:
        session = self.gateway.current_session(phone)
        if session and session.state == "confirm":
            user = self.gateway.store.get_user(self.gateway.normalize(phone))
            needs_pin = bool(user and user.pin_hash)
            g = self._gather(spoken, speech=not needs_pin, pin=needs_pin)
        elif session:
            g = self._gather(spoken)
        else:
            g = self._gather(spoken + " Press 0 for the main menu, or hang up.")
        return tw.response(g, tw.say("Goodbye."), tw.hangup())
