import unittest

from gateway.models import hash_pin, normalize_phone, verify_pin
from gateway.parser import parse


class ParserTest(unittest.TestCase):
    def test_ride_variants(self):
        self.assertEqual(parse("RIDE home").args, {"dropoff": "home"})
        self.assertEqual(parse("ride").args, {})
        self.assertEqual(parse("Cab FROM work TO home").args, {"pickup": "work", "dropoff": "home"})
        self.assertEqual(parse("taxi 5 Oak St > airport").args, {"pickup": "5 Oak St", "dropoff": "airport"})
        self.assertEqual(parse("ride From 5 Oak St").args, {"pickup": "5 Oak St"})
        self.assertEqual(parse("ride to Toronto Ave").args, {"dropoff": "Toronto Ave"})
        self.assertEqual(parse("RIDE home.").name, "RIDE")

    def test_ride_keyword_needs_word_boundary(self):
        self.assertEqual(parse("Rideout Rd").name, "UNKNOWN")

    def test_yes_with_and_without_pin(self):
        self.assertEqual(parse("yes").name, "YES")
        self.assertEqual(parse("Y").args, {})
        self.assertEqual(parse("YES 1234").args, {"pin": "1234"})
        self.assertEqual(parse("yes please").name, "UNKNOWN")

    def test_exact_keywords_only_match_whole_message(self):
        self.assertEqual(parse("STATUS").name, "STATUS")
        self.assertEqual(parse("Status Ave").name, "UNKNOWN")
        self.assertEqual(parse("menu").name, "HELP")
        self.assertEqual(parse("?").name, "HELP")
        self.assertEqual(parse("no").name, "NO")

    def test_save_keeps_address_case(self):
        cmd = parse("SAVE Clinic 12 Elm St, Springfield IL")
        self.assertEqual(cmd.name, "SAVE")
        self.assertEqual(cmd.args, {"name": "clinic", "address": "12 Elm St, Springfield IL"})

    def test_forget(self):
        self.assertEqual(parse("forget clinic").args, {"name": "clinic"})


class ModelsTest(unittest.TestCase):
    def test_normalize_phone(self):
        self.assertEqual(normalize_phone("(555) 123-4567"), "+15551234567")
        self.assertEqual(normalize_phone("1-555-123-4567"), "+15551234567")
        self.assertEqual(normalize_phone("+44 20 7946 0000"), "+442079460000")
        self.assertEqual(normalize_phone("0044 20 7946 0000"), "+442079460000")
        with self.assertRaises(ValueError):
            normalize_phone("hello")

    def test_pin_hashing(self):
        h = hash_pin("1234")
        self.assertNotIn("1234", h)
        self.assertTrue(verify_pin("1234", h))
        self.assertFalse(verify_pin("4321", h))
        self.assertFalse(verify_pin("1234", "garbage"))
        with self.assertRaises(ValueError):
            hash_pin("12")


if __name__ == "__main__":
    unittest.main()
