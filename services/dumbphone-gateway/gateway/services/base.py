"""The plugin interface every gateway service implements.

To add a new capability (transit times, food delivery, bank balance, ...):
subclass Service, declare the command keywords it owns, add a parser rule for
them in parser.py, and register it in app.py.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Tuple

from ..models import User
from ..parser import Command
from ..store import Session, Store


@dataclass
class Context:
    user: User
    store: Store
    channel: str  # "sms" or "voice": lets services phrase prompts for the medium
    clock: Callable[[], float]

    @property
    def phone(self) -> str:
        return self.user.phone

    def session(self) -> Optional[Session]:
        return self.store.get_session(self.phone)

    def set_session(self, service: str, state: str, data: dict, ttl: float) -> None:
        self.store.set_session(self.phone, service, state, data, self.clock() + ttl)

    def update_session(self, session: Session) -> None:
        """Save changed session data without extending its expiry."""
        self.store.set_session(self.phone, session.service, session.state, session.data, session.expires_at)

    def clear_session(self) -> None:
        self.store.clear_session(self.phone)


class Service(ABC):
    name: str = "base"
    commands: frozenset = frozenset()
    help_lines: Tuple[str, ...] = ()

    @abstractmethod
    def handle(self, ctx: Context, cmd: Command) -> str:
        """Handle a command this service owns. Return the reply text."""

    def resume(self, ctx: Context, cmd: Command, session: Session) -> str:
        """Continue a multi-step conversation this service started."""
        ctx.clear_session()
        return "Sorry, that conversation expired. Text MENU for options."

    def poll_updates(self) -> Iterable[Tuple[str, str]]:
        """Return (phone, text) push notifications. Called periodically."""
        return []
