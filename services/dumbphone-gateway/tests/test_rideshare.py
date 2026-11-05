import unittest

from gateway.llm import IntentRewriter

from .helpers import PHONE, make_app, text


class RideFlowTest(unittest.TestCase):
    def test_full_ride_with_push_updates(self):
        app, clock, _ = make_app()
        reply = text(app, "RIDE home")
        self.assertIn("pick you up", reply)

        reply = text(app, "work")  # answer with a saved place
        self.assertIn("from WORK to HOME", reply)
        self.assertIn("Reply YES", reply)

        reply = text(app, "YES")
        self.assertTrue(reply.startswith("Booked!"), reply)
        self.assertIsNotNone(app.store.active_ride(PHONE))

        clock.advance(20)
        updates = list(app.gateway.poll_updates())
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0][0], PHONE)
        self.assertIn("Sam is coming in a gray Toyota Camry, plate 7ABC123", updates[0][1])
        self.assertEqual(list(app.gateway.poll_updates()), [])  # no change, no push

        clock.advance(110)
        self.assertIn("arriving now", text(app, "STATUS"))
        clock.advance(1000)
        updates = list(app.gateway.poll_updates())
        self.assertIn("You've arrived", updates[0][1])
        self.assertIsNone(app.store.active_ride(PHONE))

    def test_one_shot_ride_from_to(self):
        app, _, _ = make_app()
        self.assertIn("from WORK to HOME", text(app, "ride from work to home"))

    def test_bare_ride_asks_destination_then_pickup(self):
        app, _, _ = make_app()
        self.assertIn("Where to?", text(app, "RIDE"))
        self.assertIn("pick you up", text(app, "123 Fake St"))
        self.assertIn("from HOME to 123 Fake St", text(app, "home"))

    def test_no_aborts_flow(self):
        app, _, _ = make_app()
        text(app, "RIDE home")
        self.assertIn("stopped", text(app, "no"))
        self.assertIn("Nothing to confirm", text(app, "yes"))

    def test_quote_expires(self):
        app, clock, _ = make_app(quote_ttl_seconds=300)
        text(app, "ride from work to home")
        clock.advance(301)
        self.assertIn("Nothing to confirm", text(app, "YES"))
        self.assertIsNone(app.store.active_ride(PHONE))

    def test_cannot_double_book(self):
        app, _, _ = make_app()
        text(app, "ride from work to home")
        text(app, "yes")
        self.assertIn("Nothing to confirm", text(app, "yes"))
        self.assertIn("already have a ride", text(app, "ride home"))

    def test_cancel_pending_and_active(self):
        app, clock, _ = make_app()
        text(app, "ride from work to home")
        self.assertIn("Nothing was booked", text(app, "cancel"))
        text(app, "ride from work to home")
        text(app, "yes")
        clock.advance(20)
        list(app.gateway.poll_updates())
        reply = text(app, "cancel")
        self.assertIn("cancelled", reply)
        self.assertIn("fee may apply", reply)
        self.assertIsNone(app.store.active_ride(PHONE))
        self.assertIn("No active ride", text(app, "status"))


class PinTest(unittest.TestCase):
    def test_pin_required_and_attempts_limited(self):
        app, _, _ = make_app(pin="4321", max_pin_attempts=3)
        self.assertIn("YES and your PIN", text(app, "ride from work to home"))
        self.assertIn("PIN needed", text(app, "yes"))
        self.assertIn("Wrong PIN", text(app, "yes 1111"))
        self.assertIn("Wrong PIN", text(app, "yes 2222"))
        self.assertIn("Too many wrong PINs", text(app, "yes 3333"))
        self.assertIsNone(app.store.active_ride(PHONE))

    def test_correct_pin_books(self):
        app, _, _ = make_app(pin="4321")
        text(app, "ride from work to home")
        self.assertTrue(text(app, "YES 4321").startswith("Booked!"))


class AccessTest(unittest.TestCase):
    def test_unknown_number_rejected(self):
        app, _, _ = make_app(register=False)
        self.assertIn("isn't signed up", text(app, "RIDE home"))

    def test_open_signup(self):
        app, _, _ = make_app(register=False, allow_open_signup=True)
        self.assertIn("Where to?", text(app, "ride"))
        self.assertIsNotNone(app.store.get_user(PHONE))

    def test_rate_limit_drops_messages(self):
        app, clock, _ = make_app(rate_limit_count=3, rate_limit_window_seconds=60)
        for _ in range(3):
            self.assertTrue(text(app, "menu"))
        self.assertEqual(text(app, "menu"), "")
        clock.advance(61)
        self.assertTrue(text(app, "menu"))

    def test_phone_formats_map_to_same_user(self):
        app, _, _ = make_app()
        self.assertIn("pick you up", text(app, "ride home", phone="(555) 000-1111"))


class PlacesTest(unittest.TestCase):
    def test_save_list_forget(self):
        app, _, _ = make_app()
        self.assertIn("Saved CLINIC", text(app, "SAVE clinic 12 Elm St, Springfield"))
        self.assertIn("CLINIC=12 Elm St, Springfield", text(app, "places"))
        self.assertIn("Forgot CLINIC", text(app, "forget clinic"))
        self.assertIn("No saved place", text(app, "forget clinic"))

    def test_reserved_name(self):
        app, _, _ = make_app()
        self.assertIn("can't be used", text(app, "save to 1 Main St"))


class FakeRewriter(IntentRewriter):
    def __init__(self, answer):
        self.answer = answer

    def rewrite(self, text):
        return self.answer


class LlmFallbackTest(unittest.TestCase):
    def test_rewrite_to_ride(self):
        app, _, _ = make_app()
        app.gateway.rewriter = FakeRewriter("RIDE home")
        self.assertIn("pick you up", text(app, "can u get me a car home pls"))

    def test_rewrite_cannot_confirm_or_cancel(self):
        app, _, _ = make_app()
        for unsafe in ("YES", "CANCEL", "FORGET home"):
            app.gateway.rewriter = FakeRewriter(unsafe)
            self.assertIn("didn't get that", text(app, "blah blah"))
        self.assertIsNotNone(app.store.get_place(PHONE, "home"))

    def test_answers_to_pending_questions_skip_llm(self):
        app, _, _ = make_app()
        app.gateway.rewriter = FakeRewriter("STATUS")
        text(app, "RIDE home")
        self.assertIn("from 400 Elm St to HOME", text(app, "400 Elm St"))


if __name__ == "__main__":
    unittest.main()
