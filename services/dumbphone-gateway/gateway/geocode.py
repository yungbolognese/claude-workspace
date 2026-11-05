"""Address -> coordinates. Dumb phones have no GPS to share, so every pickup
is typed (or spoken) and must be resolved here. Saved places are geocoded once
at SAVE time so day-to-day rides ("RIDE home") never hit the network."""

import logging
import threading
import time
import urllib.parse
from abc import ABC, abstractmethod
from typing import Optional

from .http import request_json
from .models import Place

log = logging.getLogger(__name__)


class Geocoder(ABC):
    @abstractmethod
    def geocode(self, query: str) -> Optional[Place]:
        """Return a Place, or None if the address couldn't be found."""


class NullGeocoder(Geocoder):
    """Accepts any text as-is with no coordinates. Fine for the mock provider."""

    def geocode(self, query: str) -> Optional[Place]:
        query = query.strip()
        return Place(address=query) if query else None


class NominatimGeocoder(Geocoder):
    """OpenStreetMap Nominatim. Free; usage policy caps you at 1 request/sec
    and requires an identifying User-Agent. Self-host it for heavier use."""

    URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self, user_agent: str, countries: str = "", http=request_json):
        self.user_agent = user_agent
        self.countries = countries
        self.http = http
        self._lock = threading.Lock()
        self._last = 0.0

    def geocode(self, query: str) -> Optional[Place]:
        params = {"q": query, "format": "jsonv2", "limit": "1"}
        if self.countries:
            params["countrycodes"] = self.countries
        with self._lock:  # stay under 1 req/sec
            wait = 1.0 - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
        try:
            results = self.http(
                "GET", self.URL + "?" + urllib.parse.urlencode(params), headers={"User-Agent": self.user_agent}
            )
        except Exception:
            log.exception("geocoding failed")
            return None
        if not results:
            return None
        top = results[0]
        # "123, Main Street, Springfield, Some County, ..." -> first 3 parts
        short = ", ".join(p.strip() for p in top.get("display_name", query).split(",")[:3])
        return Place(address=short, lat=float(top["lat"]), lng=float(top["lon"]))


def build_geocoder(config) -> Geocoder:
    if config.geocoder == "nominatim":
        return NominatimGeocoder(config.geocoder_user_agent, config.geocoder_countries)
    return NullGeocoder()
