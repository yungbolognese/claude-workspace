"""Rideshare provider adapters.

Every provider speaks the same small interface (quote -> request -> status ->
cancel) and normalizes its statuses to the set below, so the SMS/voice side
never needs to know which company is driving.
"""

import math
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Callable, Optional

from ..http import HttpError, request_json
from ..models import Place, User

ACTIVE_STATUSES = {"searching", "accepted", "arriving", "in_progress"}
TERMINAL_STATUSES = {"completed", "cancelled", "no_drivers"}


class ProviderError(Exception):
    """Raised with a short, user-presentable message."""


@dataclass
class Quote:
    product_id: str
    product_name: str
    fare_display: str
    pickup_eta_min: Optional[int] = None
    fare_id: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class RideInfo:
    ride_id: str
    status: str
    driver_name: Optional[str] = None
    vehicle: Optional[str] = None
    plate: Optional[str] = None
    eta_min: Optional[int] = None
    fare_display: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class RideProvider(ABC):
    name = "base"
    requires_coords = False

    @abstractmethod
    def quote(self, pickup: Place, dropoff: Place) -> Quote: ...

    @abstractmethod
    def request(self, quote: Quote, pickup: Place, dropoff: Place, rider: User) -> RideInfo: ...

    @abstractmethod
    def status(self, ride_id: str) -> RideInfo: ...

    @abstractmethod
    def cancel(self, ride_id: str) -> None: ...


def haversine_km(a: Place, b: Place) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (a.lat, a.lng, b.lat, b.lng))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


class MockRideProvider(RideProvider):
    """Simulated provider for development and demos. Rides progress on a timer:
    searching -> accepted -> arriving -> in_progress -> completed."""

    name = "mock"
    # (seconds since request, status) — divided by `speed`
    TIMELINE = [(0, "searching"), (15, "accepted"), (120, "arriving"), (180, "in_progress"), (600, "completed")]

    def __init__(self, clock: Callable[[], float] = time.time, speed: float = 1.0):
        self.clock = clock
        self.speed = speed
        self._rides = {}
        self._lock = threading.Lock()
        self._seq = 0

    def quote(self, pickup, dropoff):
        if pickup.has_coords and dropoff.has_coords:
            km = haversine_km(pickup, dropoff)
        else:  # deterministic fake distance
            km = 2 + sum(map(ord, pickup.address + dropoff.address)) % 15
        fare = 3.0 + 1.6 * km
        return Quote("mock-standard", "Standard", f"${fare - 1:.0f}-{fare + 3:.0f}", pickup_eta_min=4)

    def request(self, quote, pickup, dropoff, rider):
        with self._lock:
            self._seq += 1
            ride_id = f"mock-{self._seq}"
            self._rides[ride_id] = {"t0": self.clock(), "cancelled": False, "fare": quote.fare_display}
        return self.status(ride_id)

    def status(self, ride_id):
        ride = self._rides.get(ride_id)
        if ride is None:  # e.g. the gateway restarted; mock state is in memory
            return RideInfo(ride_id, "cancelled")
        if ride["cancelled"]:
            return RideInfo(ride_id, "cancelled")
        elapsed = (self.clock() - ride["t0"]) * self.speed
        status = [s for t, s in self.TIMELINE if elapsed >= t][-1]
        info = RideInfo(ride_id, status, fare_display=ride["fare"])
        if status in ("accepted", "arriving"):
            info.driver_name, info.vehicle, info.plate = "Sam", "gray Toyota Camry", "7ABC123"
        if status == "accepted":
            info.eta_min = max(1, math.ceil((120 - elapsed) / 60))
        return info

    def cancel(self, ride_id):
        if ride_id in self._rides:
            self._rides[ride_id]["cancelled"] = True


class UberGuestRidesProvider(RideProvider):
    """Uber for Business — Guest Rides API.

    Uber's consumer "ride request on behalf of a user" API is closed to new
    apps; Guest Rides is the supported way to book a ride for someone who has
    no Uber app. It needs an approved Uber for Business account, and trips are
    billed to that account.

    UNVERIFIED: written from the public docs
    (https://developer.uber.com/docs/guest-rides) without live credentials.
    Run it against the sandbox (DPG_UBER_SANDBOX=1) and compare response
    shapes before using it for real rides.
    """

    name = "uber"
    requires_coords = True
    TOKEN_URL = "https://auth.uber.com/oauth/v2/token"
    STATUS_MAP = {
        "processing": "searching",
        "scheduled": "searching",
        "no_drivers_available": "no_drivers",
        "accepted": "accepted",
        "arriving": "arriving",
        "in_progress": "in_progress",
        "driver_canceled": "cancelled",
        "rider_canceled": "cancelled",
        "canceled": "cancelled",
        "completed": "completed",
    }

    def __init__(self, client_id, client_secret, scope, sandbox=True, sandbox_run_id="", http=request_json,
                 clock=time.time):
        if not (client_id and client_secret):
            raise ValueError("uber_guest provider needs DPG_UBER_CLIENT_ID and DPG_UBER_CLIENT_SECRET")
        self.client_id, self.client_secret, self.scope = client_id, client_secret, scope
        self.base = "https://sandbox-api.uber.com" if sandbox else "https://api.uber.com"
        self.sandbox_run_id = sandbox_run_id if sandbox else ""
        self.http = http
        self.clock = clock
        self._token = None
        self._token_expiry = 0.0

    def _auth_header(self):
        if not self._token or self.clock() > self._token_expiry - 60:
            resp = self.http("POST", self.TOKEN_URL, form={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": self.scope,
            })
            self._token = resp["access_token"]
            self._token_expiry = self.clock() + float(resp.get("expires_in", 3600))
        return {"Authorization": f"Bearer {self._token}"}

    def _call(self, method, path, body=None):
        headers = self._auth_header()
        if self.sandbox_run_id:
            headers["x-uber-sandbox-runuuid"] = self.sandbox_run_id
        try:
            return self.http(method, self.base + path, json_body=body, headers=headers)
        except HttpError as e:
            raise ProviderError(f"Uber returned an error ({e.status}). Please try again.") from e

    @staticmethod
    def _coords(p: Place):
        if not p.has_coords:
            raise ProviderError(f"couldn't locate '{p.short()}'. Try a full street address with city.")
        return {"latitude": p.lat, "longitude": p.lng}

    def quote(self, pickup, dropoff):
        resp = self._call("POST", "/v1/guests/trips/estimates",
                          {"pickup": self._coords(pickup), "dropoff": self._coords(dropoff)})
        estimates = [e for e in (resp or {}).get("product_estimates", []) if e.get("product")]
        if not estimates:
            raise ProviderError("no Uber rides are available for that trip right now.")
        est = estimates[0]  # Uber lists the default product first
        info = est.get("estimate_info") or {}
        fare = info.get("fare") or {}
        display = fare.get("display") or (info.get("estimate") or {}).get("display") or "price shown at pickup"
        return Quote(
            product_id=est["product"]["product_id"],
            product_name=est["product"].get("display_name", "Uber"),
            fare_display=display,
            pickup_eta_min=info.get("pickup_estimate"),
            fare_id=fare.get("fare_id"),
        )

    def request(self, quote, pickup, dropoff, rider):
        first, _, last = (rider.name or "Guest").partition(" ")
        body = {
            "guest": {"first_name": first, "last_name": last, "phone_number": rider.phone},
            "pickup": self._coords(pickup),
            "dropoff": self._coords(dropoff),
            "product_id": quote.product_id,
        }
        if quote.fare_id:
            body["fare_id"] = quote.fare_id
        return self._info(self._call("POST", "/v1/guests/trips", body))

    def status(self, ride_id):
        return self._info(self._call("GET", f"/v1/guests/trips/{ride_id}"))

    def cancel(self, ride_id):
        self._call("DELETE", f"/v1/guests/trips/{ride_id}")

    def _info(self, resp):
        driver = resp.get("driver") or {}
        vehicle = resp.get("vehicle") or {}
        pickup = resp.get("pickup") or {}
        make_model = " ".join(filter(None, [vehicle.get("make"), vehicle.get("model")])) or None
        return RideInfo(
            ride_id=resp.get("request_id") or resp.get("trip_id"),
            status=self.STATUS_MAP.get(resp.get("status", ""), "searching"),
            driver_name=driver.get("name"),
            vehicle=make_model,
            plate=vehicle.get("license_plate"),
            eta_min=pickup.get("eta"),
        )


def build_provider(config, clock=time.time) -> RideProvider:
    if config.ride_provider == "uber_guest":
        return UberGuestRidesProvider(
            config.uber_client_id, config.uber_client_secret, config.uber_scope,
            sandbox=config.uber_sandbox, sandbox_run_id=config.uber_sandbox_run_id, clock=clock,
        )
    if config.ride_provider == "mock":
        return MockRideProvider(clock=clock, speed=config.mock_speed)
    raise ValueError(f"unknown ride provider: {config.ride_provider}")
