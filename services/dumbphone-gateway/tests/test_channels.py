import base64
import hashlib
import hmac
import unittest
import urllib.parse

from gateway.channels import twilio as tw
from gateway.server import handle_request

from .helpers import PHONE, make_app


class SignatureTest(unittest.TestCase):
    URL = "https://example.ts.net/sms"
    PARAMS = {"From": "+15550001111", "Body": "RIDE home", "To": "+15559990000"}

    def test_matches_independent_computation(self):
        payload = self.URL + "BodyRIDE homeFrom+15550001111To+15559990000"
        expected = base64.b64encode(hmac.new(b"secret", payload.encode(), hashlib.sha1).digest()).decode()
        self.assertEqual(tw.compute_signature("secret", self.URL, self.PARAMS), expected)
        self.assertTrue(tw.validate_signature("secret", self.URL, self.PARAMS, expected))

    def test_rejects_tampering_and_missing(self):
        sig = tw.compute_signature("secret", self.URL, self.PARAMS)
        self.assertFalse(tw.validate_signature("secret", self.URL, {**self.PARAMS, "Body": "YES"}, sig))
        self.assertFalse(tw.validate_signature("secret", self.URL, self.PARAMS, ""))
        self.assertFalse(tw.validate_signature("", self.URL, self.PARAMS, sig))


def form(**kw) -> bytes:
    return urllib.parse.urlencode(kw).encode()


class HttpTest(unittest.TestCase):
    def test_sms_webhook_returns_twiml(self):
        app, _, _ = make_app()
        status, ctype, body = handle_request(app, "POST", "/sms", {}, form(From=PHONE, Body="RIDE home"))
        self.assertEqual(status, 200)
        self.assertIn("xml", ctype)
        self.assertIn("<Response><Message>Where should the driver pick you up?", body)

    def test_twiml_escapes_user_text(self):
        app, _, _ = make_app()
        handle_request(app, "POST", "/sms", {}, form(From=PHONE, Body="ride"))
        _, _, body = handle_request(app, "POST", "/sms", {}, form(From=PHONE, Body="<b>&"))
        _, _, body = handle_request(app, "POST", "/sms", {}, form(From=PHONE, Body="home"))
        self.assertIn("&lt;b&gt;&amp;", body)

    def test_signature_enforced(self):
        app, _, _ = make_app(twilio_auth_token="secret", public_base_url="https://gw.example")
        app.config.validate_signatures = True
        params = {"From": PHONE, "Body": "menu"}
        status, _, _ = handle_request(app, "POST", "/sms", {}, form(**params))
        self.assertEqual(status, 403)
        sig = tw.compute_signature("secret", "https://gw.example/sms", params)
        status, _, body = handle_request(app, "POST", "/sms", {"x-twilio-signature": sig}, form(**params))
        self.assertEqual(status, 200)
        self.assertIn("RIDE", body)

    def test_health_and_404(self):
        app, _, _ = make_app()
        self.assertEqual(handle_request(app, "GET", "/health", {}, b"")[0], 200)
        self.assertEqual(handle_request(app, "GET", "/nope", {}, b"")[0], 404)


class VoiceTest(unittest.TestCase):
    def test_unregistered_caller_hung_up(self):
        app, _, _ = make_app(register=False)
        self.assertIn("<Hangup/>", app.voice.incoming(PHONE))

    def test_press_1_ride_home_by_voice(self):
        app, _, _ = make_app()
        menu = app.voice.incoming(PHONE)
        self.assertIn("Press 1 for a ride home", menu)
        self.assertIn('action="/voice/input"', menu)

        twiml = app.voice.handle_input(PHONE, digits="1")
        self.assertIn("Say the address", twiml)

        twiml = app.voice.handle_input(PHONE, speech="work")
        self.assertIn("from WORK to HOME", twiml)
        self.assertIn("Press 1 to book", twiml)

        twiml = app.voice.handle_input(PHONE, digits="1")
        self.assertIn("Booked!", twiml)
        self.assertIsNotNone(app.store.active_ride(PHONE))

    def test_speech_destination_becomes_ride(self):
        app, _, _ = make_app()
        twiml = app.voice.handle_input(PHONE, speech="work")
        self.assertIn("pick you up", twiml)

    def test_voice_pin_entry(self):
        app, _, _ = make_app(pin="4321")
        app.voice.handle_input(PHONE, speech="work")
        twiml = app.voice.handle_input(PHONE, speech="home")
        self.assertIn('finishOnKey="#"', twiml)
        self.assertIn("Booked!", app.voice.handle_input(PHONE, digits="4321"))


if __name__ == "__main__":
    unittest.main()
