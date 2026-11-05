"""Rideshare over SMS/voice.

Conversation:
    > RIDE home                    (or: RIDE from work to home)
    < Where should the driver pick you up? ...
    > 400 Elm St, Springfield
    < Standard from 400 Elm St to HOME: $12-16, pickup ~4 min. Reply YES to book, NO to cancel.
    > YES                          (or YES 1234 if the user has a PIN)
    < Booked! Finding you a driver...
    ... push texts as the ride progresses ...
"""

import logging
from typing import Optional, Tuple

from ..geocode import Geocoder
from ..models import Place, verify_pin
from ..store import Store
from .base import Context, Service
from .ride_providers import ACTIVE_STATUSES, ProviderError, Quote, RideInfo, RideProvider

log = logging.getLogger(__name__)

SESSION_TTL = 600  # seconds to answer "where to?" / "pickup?"

PROMPTS = {
    "sms": {
        "dropoff": "Where to? Reply with an address or saved place (e.g. HOME). Reply NO to stop.",
        "pickup": "Where should the driver pick you up? Reply with an address or saved place. Reply NO to stop.",
        "confirm": "Reply YES to book, NO to cancel.",
        "confirm_pin": "Reply YES and your PIN (e.g. YES 1234) to book, NO to cancel.",
    },
    "voice": {
        "dropoff": "Where are you going? Say the address or a saved place name. Press 0 to stop.",
        "pickup": "Where should the driver pick you up? Say the address or a saved place name. Press 0 to stop.",
        "confirm": "Press 1 to book, or 2 to cancel.",
        "confirm_pin": "Enter your PIN then press pound to book. Or press 2 then pound to cancel.",
    },
}


def describe(info: RideInfo) -> str:
    who = info.driver_name or "Your driver"
    car = f" in a {info.vehicle}" if info.vehicle else ""
    plate = f", plate {info.plate}" if info.plate else ""
    if info.status == "searching":
        return "Finding you a driver..."
    if info.status == "accepted":
        eta = f", ~{info.eta_min} min away" if info.eta_min else ""
        return f"{who} is coming{car}{plate}{eta}."
    if info.status == "arriving":
        return f"{who} is arriving now{car}{plate}."
    if info.status == "in_progress":
        return "You're on your way. Enjoy the ride."
    if info.status == "completed":
        fare = f" Fare: {info.fare_display}." if info.fare_display else ""
        return f"You've arrived.{fare}"
    if info.status == "no_drivers":
        return "No drivers available right now. Text RIDE to try again."
    return "Your ride was cancelled."


class RideshareService(Service):
    name = "ride"
    commands = frozenset({"RIDE", "STATUS", "CANCEL"})
    help_lines = ("RIDE <place>", "RIDE from <A> to <B>", "STATUS", "CANCEL")

    def __init__(self, provider: RideProvider, geocoder: Geocoder, store: Store, quote_ttl: int = 300,
                 max_pin_attempts: int = 3):
        self.provider = provider
        self.store = store  # the status poller runs outside any user context
        self.geocoder = geocoder
        self.quote_ttl = quote_ttl
        self.max_pin_attempts = max_pin_attempts

    # -- entry points --------------------------------------------------------
    def handle(self, ctx: Context, cmd) -> str:
        if cmd.name == "RIDE":
            return self._start(ctx, cmd.args.get("pickup"), cmd.args.get("dropoff"))
        if cmd.name == "STATUS":
            return self._status(ctx)
        if cmd.name == "CANCEL":
            return self._cancel(ctx)
        return "Unknown command."

    def resume(self, ctx: Context, cmd, session) -> str:
        data = session.data
        if session.state in ("need_pickup", "need_dropoff"):
            if cmd.name == "NO":
                ctx.clear_session()
                return "OK, stopped. Text RIDE any time."
            text = cmd.raw.strip()
            if not text:
                return self._prompt(ctx, session.state[5:])
            place, err = self._resolve(ctx, text)
            if err:
                return err
            data["pickup" if session.state == "need_pickup" else "dropoff"] = place.to_dict()
            return self._advance(ctx, data)

        if session.state == "confirm":
            if cmd.name == "NO":
                ctx.clear_session()
                return "OK, not booked."
            if cmd.name == "YES":
                return self._book(ctx, session, cmd.args.get("pin"))
            return self._prompt(ctx, "confirm_pin" if ctx.user.pin_hash else "confirm")

        return super().resume(ctx, cmd, session)

    def poll_updates(self):
        updates = []
        for ride in self.store.active_rides(provider=self.provider.name):
            try:
                info, changed = self._refresh(ride)
            except ProviderError:
                log.exception("status poll failed for ride %s", ride.id)
                continue
            if changed:
                updates.append((ride.phone, describe(info)))
        return updates

    # -- flow ----------------------------------------------------------------
    def _prompt(self, ctx: Context, key: str) -> str:
        return PROMPTS.get(ctx.channel, PROMPTS["sms"])[key]

    def _resolve(self, ctx: Context, text: str) -> Tuple[Optional[Place], Optional[str]]:
        saved = ctx.store.get_place(ctx.phone, text)
        if saved:
            return saved, None
        place = self.geocoder.geocode(text)
        if place is None:
            return None, f"Couldn't find '{text[:40]}'. Try street, city and state, or a saved place name."
        if self.provider.requires_coords and not place.has_coords:
            return None, f"Couldn't locate '{text[:40]}' precisely. Try a fuller address."
        return place, None

    def _start(self, ctx: Context, pickup_text, dropoff_text) -> str:
        if ctx.store.active_ride(ctx.phone):
            return "You already have a ride. Text STATUS for updates or CANCEL to cancel it."
        data = {}
        for key, text in (("pickup", pickup_text), ("dropoff", dropoff_text)):
            if text:
                place, err = self._resolve(ctx, text)
                if err:
                    ctx.clear_session()
                    return err
                data[key] = place.to_dict()
        return self._advance(ctx, data)

    def _advance(self, ctx: Context, data: dict) -> str:
        if "dropoff" not in data:
            ctx.set_session(self.name, "need_dropoff", data, SESSION_TTL)
            return self._prompt(ctx, "dropoff")
        if "pickup" not in data:
            ctx.set_session(self.name, "need_pickup", data, SESSION_TTL)
            return self._prompt(ctx, "pickup")

        pickup, dropoff = Place.from_dict(data["pickup"]), Place.from_dict(data["dropoff"])
        try:
            quote = self.provider.quote(pickup, dropoff)
        except ProviderError as e:
            ctx.clear_session()
            return f"Sorry, {e}"
        data.update(quote=quote.to_dict(), pin_failures=0)
        ctx.set_session(self.name, "confirm", data, self.quote_ttl)
        eta = f", pickup ~{quote.pickup_eta_min} min" if quote.pickup_eta_min else ""
        confirm = self._prompt(ctx, "confirm_pin" if ctx.user.pin_hash else "confirm")
        return f"{quote.product_name} from {pickup.short()} to {dropoff.short()}: {quote.fare_display}{eta}. {confirm}"

    def _book(self, ctx: Context, session, pin: Optional[str]) -> str:
        data = session.data
        if ctx.user.pin_hash and not (pin and verify_pin(pin, ctx.user.pin_hash)):
            if pin:
                data["pin_failures"] = data.get("pin_failures", 0) + 1
                if data["pin_failures"] >= self.max_pin_attempts:
                    ctx.clear_session()
                    return "Too many wrong PINs. Booking cancelled."
                ctx.update_session(session)
                return "Wrong PIN. " + self._prompt(ctx, "confirm_pin")
            return "PIN needed. " + self._prompt(ctx, "confirm_pin")

        quote = Quote.from_dict(data["quote"])
        pickup, dropoff = Place.from_dict(data["pickup"]), Place.from_dict(data["dropoff"])
        ctx.clear_session()  # clear first so a double "YES" can't double-book
        try:
            info = self.provider.request(quote, pickup, dropoff, ctx.user)
        except ProviderError as e:
            return f"Booking failed: {e}"
        ctx.store.create_ride(ctx.phone, self.provider.name, info.ride_id, info.status, pickup, dropoff, info.to_dict())
        return f"Booked! {describe(info)} Text STATUS for updates, CANCEL to cancel."

    def _refresh(self, ride) -> Tuple[RideInfo, bool]:
        info = self.provider.status(ride.provider_ride_id)
        changed = info.status != ride.status
        self.store.update_ride(ride.id, info.status, info.to_dict(), active=info.status in ACTIVE_STATUSES)
        return info, changed

    def _status(self, ctx: Context) -> str:
        session = ctx.session()
        if session and session.service == self.name and session.state == "confirm":
            return "You have a ride quote waiting. " + self._prompt(ctx, "confirm_pin" if ctx.user.pin_hash else "confirm")
        ride = ctx.store.active_ride(ctx.phone)
        if not ride:
            return "No active ride. Text RIDE <place> to get one."
        try:
            info, _ = self._refresh(ride)
        except ProviderError as e:
            return f"Couldn't get status: {e}"
        return describe(info)

    def _cancel(self, ctx: Context) -> str:
        session = ctx.session()
        if session and session.service == self.name:
            ctx.clear_session()
            return "OK, cancelled. Nothing was booked."
        ride = ctx.store.active_ride(ctx.phone)
        if not ride:
            return "No active ride to cancel."
        try:
            self.provider.cancel(ride.provider_ride_id)
        except ProviderError as e:
            return f"Couldn't cancel: {e} Try again or call the driver."
        ctx.store.update_ride(ride.id, "cancelled", ride.info, active=False)
        fee = " A cancellation fee may apply." if ride.status in ("accepted", "arriving") else ""
        return f"Your ride is cancelled.{fee}"
