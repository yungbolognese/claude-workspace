from gateway.app import build_app
from gateway.channels.twilio import MemorySender
from gateway.config import Config
from gateway.models import Inbound, Place, hash_pin
from gateway.services.ride_providers import MockRideProvider
from gateway.store import Store

PHONE = "+15550001111"


class FakeClock:
    def __init__(self, t: float = 1_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def make_app(pin=None, register=True, **config_overrides):
    clock = FakeClock()
    cfg = Config(db_path=":memory:", validate_signatures=False, **config_overrides)
    store = Store(":memory:", clock=clock)
    provider = MockRideProvider(clock=clock)
    app = build_app(cfg, clock=clock, store=store, provider=provider, sender=MemorySender())
    if register:
        store.add_user(PHONE, "Ann Lee", hash_pin(pin) if pin else None)
        store.save_place(PHONE, Place(name="home", address="742 Evergreen Terrace", lat=41.0, lng=-87.0))
        store.save_place(PHONE, Place(name="work", address="100 Industrial Way", lat=41.05, lng=-87.05))
    return app, clock, provider


def text(app, body, phone=PHONE, channel="sms"):
    replies = app.gateway.handle(Inbound(phone, body, channel))
    return " | ".join(replies)
