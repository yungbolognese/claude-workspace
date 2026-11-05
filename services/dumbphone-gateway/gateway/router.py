"""The gateway core: one inbound message in, reply text(s) out.

Channel-agnostic: SMS and voice both reduce to `Inbound(phone, text)`.
"""

import logging
import time
from collections import defaultdict, deque
from typing import Callable, Iterable, List, Optional, Tuple

from .config import Config
from .llm import IntentRewriter
from .models import Inbound, normalize_phone
from .parser import Command, parse
from .services.base import Context, Service
from .store import Session, Store

log = logging.getLogger(__name__)

# Free-text rewrites from the LLM may only produce commands that are safe on
# their own. Anything that spends money or deletes data (YES, CANCEL, FORGET)
# must come from the user's own keystrokes.
LLM_ALLOWED = {"RIDE", "STATUS", "PLACES", "HELP"}


class Gateway:
    def __init__(
        self,
        store: Store,
        services: List[Service],
        config: Config,
        rewriter: Optional[IntentRewriter] = None,
        clock: Callable[[], float] = time.time,
    ):
        self.store = store
        self.services = services
        self.config = config
        self.rewriter = rewriter
        self.clock = clock
        self.by_command = {}
        self.by_name = {}
        for svc in services:
            self.by_name[svc.name] = svc
            for c in svc.commands:
                if c in self.by_command:
                    raise ValueError(f"command {c} claimed by both {self.by_command[c].name} and {svc.name}")
                self.by_command[c] = svc
        self._recent = defaultdict(deque)

    # -- public --------------------------------------------------------------
    def normalize(self, phone: str) -> str:
        return normalize_phone(phone, self.config.default_country_code)

    def current_session(self, phone: str) -> Optional[Session]:
        return self.store.get_session(self.normalize(phone))

    def handle(self, inbound: Inbound) -> List[str]:
        phone = self.normalize(inbound.phone)
        text = (inbound.text or "").strip()
        if self.config.log_messages:
            self.store.log_message(phone, "in", inbound.channel, text)
        replies = self._handle(phone, text, inbound.channel)
        if self.config.log_messages:
            for r in replies:
                self.store.log_message(phone, "out", inbound.channel, r)
        return replies

    def help_text(self) -> str:
        lines = [line for svc in self.services for line in svc.help_lines]
        return "Text: " + " | ".join(lines) + " | MENU"

    def poll_updates(self) -> Iterable[Tuple[str, str]]:
        for svc in self.services:
            try:
                yield from svc.poll_updates()
            except Exception:
                log.exception("poll_updates failed for %s", svc.name)

    # -- internals -----------------------------------------------------------
    def _rate_limited(self, phone: str) -> bool:
        now = self.clock()
        q = self._recent[phone]
        while q and q[0] < now - self.config.rate_limit_window_seconds:
            q.popleft()
        q.append(now)
        return len(q) > self.config.rate_limit_count

    def _handle(self, phone: str, text: str, channel: str) -> List[str]:
        # Drop silently when flooded: this also stops reply loops with other bots.
        if self._rate_limited(phone):
            log.warning("rate limited %s", phone)
            return []
        user = self.store.get_user(phone)
        if user is None:
            if not self.config.allow_open_signup:
                return ["This number isn't signed up for this service."]
            user = self.store.add_user(phone)
            welcome = "Welcome! " + self.help_text()
            if not text:
                return [welcome]
        ctx = Context(user=user, store=self.store, channel=channel, clock=self.clock)
        try:
            reply = self._dispatch(ctx, parse(text))
        except Exception:
            log.exception("error handling message from %s", phone)
            reply = "Sorry, something went wrong. Please try again."
        return [reply] if reply else []

    def _dispatch(self, ctx: Context, cmd: Command) -> str:
        if cmd.name == "HELP":
            return self.help_text()

        session = ctx.session()
        if session and cmd.name in ("YES", "NO", "UNKNOWN"):
            svc = self.by_name.get(session.service)
            if svc:
                return svc.resume(ctx, cmd, session)

        if cmd.name in ("YES", "NO"):
            return "Nothing to confirm right now. Text MENU for options."

        if cmd.name == "UNKNOWN" and self.rewriter:
            cmd = self._rewrite(cmd)
            if cmd.name == "HELP":
                return self.help_text()

        svc = self.by_command.get(cmd.name)
        if svc is None:
            return "Sorry, I didn't get that. Text MENU for options."
        return svc.handle(ctx, cmd)

    def _rewrite(self, cmd: Command) -> Command:
        rewritten = self.rewriter.rewrite(cmd.raw)
        if not rewritten:
            return cmd
        new = parse(rewritten)
        if new.name not in LLM_ALLOWED:
            return cmd
        log.info("LLM rewrote %r -> %r", cmd.raw, rewritten)
        return new
