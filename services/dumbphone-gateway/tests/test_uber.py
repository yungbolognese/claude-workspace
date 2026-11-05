"""Exercises the Uber adapter's request/response handling with a fake HTTP
client. This checks our own logic, not Uber's real API (see the class docstring)."""

import unittest

from gateway.models import Place, User
from gateway.services.ride_providers import ProviderError, UberGuestRidesProvider
from gateway.http import HttpError

from .helpers import FakeClock

PICKUP = Place(address="A", lat=41.0, lng=-87.0)
DROPOFF = Place(address="B", lat=41.1, lng=-87.1)


class FakeHttp:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, method, url, **kw):
        self.calls.append((method, url, kw))
        for (m, suffix), resp in self.responses.items():
            if m == method and url.endswith(suffix):
                if isinstance(resp, Exception):
                    raise resp
                return resp
        raise AssertionError(f"unexpected call {method} {url}")


TOKEN = {("POST", "/oauth/v2/token"): {"access_token": "tok", "expires_in": 3600}}


class UberTest(unittest.TestCase):
    def provider(self, responses, **kw):
        http = FakeHttp({**TOKEN, **responses})
        return UberGuestRidesProvider("id", "secret", "guests.trips", http=http, clock=FakeClock(), **kw), http

    def test_quote_and_request(self):
        p, http = self.provider({
            ("POST", "/v1/guests/trips/estimates"): {"product_estimates": [{
                "product": {"product_id": "p1", "display_name": "UberX"},
                "estimate_info": {"fare": {"display": "$14.20", "fare_id": "f1"}, "pickup_estimate": 5},
            }]},
            ("POST", "/v1/guests/trips"): {"request_id": "r1", "status": "processing"},
        }, sandbox_run_id="run-1")
        q = p.quote(PICKUP, DROPOFF)
        self.assertEqual((q.product_id, q.fare_display, q.fare_id, q.pickup_eta_min), ("p1", "$14.20", "f1", 5))
        info = p.request(q, PICKUP, DROPOFF, User("+15550001111", "Ann Lee"))
        self.assertEqual((info.ride_id, info.status), ("r1", "searching"))

        method, url, kw = http.calls[-1]
        self.assertTrue(url.startswith("https://sandbox-api.uber.com"))
        self.assertEqual(kw["headers"]["x-uber-sandbox-runuuid"], "run-1")
        self.assertEqual(kw["headers"]["Authorization"], "Bearer tok")
        self.assertEqual(kw["json_body"]["guest"], {"first_name": "Ann", "last_name": "Lee", "phone_number": "+15550001111"})
        self.assertEqual(kw["json_body"]["fare_id"], "f1")
        token_calls = [c for c in http.calls if c[1].endswith("/oauth/v2/token")]
        self.assertEqual(len(token_calls), 1)  # token cached

    def test_status_mapping(self):
        p, _ = self.provider({("GET", "/v1/guests/trips/r1"): {
            "request_id": "r1", "status": "accepted",
            "driver": {"name": "Jo"}, "vehicle": {"make": "Kia", "model": "Niro", "license_plate": "XYZ"},
            "pickup": {"eta": 3},
        }})
        info = p.status("r1")
        self.assertEqual((info.status, info.driver_name, info.vehicle, info.plate, info.eta_min),
                         ("accepted", "Jo", "Kia Niro", "XYZ", 3))

    def test_requires_coordinates(self):
        p, _ = self.provider({})
        with self.assertRaises(ProviderError):
            p.quote(Place(address="somewhere"), DROPOFF)

    def test_http_errors_become_provider_errors(self):
        p, _ = self.provider({("POST", "/v1/guests/trips/estimates"): HttpError(500, "boom")})
        with self.assertRaises(ProviderError):
            p.quote(PICKUP, DROPOFF)

    def test_no_products(self):
        p, _ = self.provider({("POST", "/v1/guests/trips/estimates"): {"product_estimates": []}})
        with self.assertRaises(ProviderError):
            p.quote(PICKUP, DROPOFF)


if __name__ == "__main__":
    unittest.main()
