"""Saved places: typing a full address on a keypad is painful, so users save
HOME, WORK, CLINIC, etc. once and refer to them by name afterwards."""

from ..geocode import Geocoder
from .base import Context, Service

RESERVED = {"from", "to", "yes", "no", "me", "here"}


class PlacesService(Service):
    name = "places"
    commands = frozenset({"SAVE", "PLACES", "FORGET"})
    help_lines = ("SAVE <name> <address>", "PLACES", "FORGET <name>")

    def __init__(self, geocoder: Geocoder, max_places: int = 20):
        self.geocoder = geocoder
        self.max_places = max_places

    def handle(self, ctx: Context, cmd) -> str:
        if cmd.name == "SAVE":
            return self._save(ctx, cmd.args["name"], cmd.args["address"])
        if cmd.name == "PLACES":
            places = ctx.store.list_places(ctx.phone)
            if not places:
                return "No saved places. Example: SAVE home 123 Main St, Springfield"
            return "Saved: " + "; ".join(f"{p.name.upper()}={p.address}" for p in places)
        if cmd.name == "FORGET":
            if ctx.store.delete_place(ctx.phone, cmd.args["name"]):
                return f"Forgot {cmd.args['name'].upper()}."
            return f"No saved place called {cmd.args['name'].upper()}. Text PLACES to list them."
        return "Unknown command."

    def _save(self, ctx: Context, name: str, address: str) -> str:
        name = name.lower()
        if name in RESERVED:
            return f"'{name}' can't be used as a place name. Try another."
        existing = {p.name for p in ctx.store.list_places(ctx.phone)}
        if name not in existing and len(existing) >= self.max_places:
            return f"You can save up to {self.max_places} places. FORGET one first."
        place = self.geocoder.geocode(address)
        if place is None:
            return "Couldn't find that address. Include street, city and state."
        place.name = name
        ctx.store.save_place(ctx.phone, place)
        return f"Saved {name.upper()}: {place.address}. Now try: RIDE {name}"
