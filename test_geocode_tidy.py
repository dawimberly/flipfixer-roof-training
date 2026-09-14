"""Address tidy for free geocoders. No network."""

import unittest

from serve_tracer import tidy_address


class TidyAddressTests(unittest.TestCase):
    def test_unit_number(self):
        self.assertEqual(
            tidy_address("8101 E. Dartmouth Ave. #78, Denver, CO 80231"),
            "8101 E. Dartmouth Ave., Denver, CO 80231",
        )

    def test_san_antonio_ln_typo(self):
        self.assertEqual(
            tidy_address("5439 Congo LN, San Antonio Ln, TX 78227"),
            "5439 Congo LN, San Antonio, TX 78227",
        )

    def test_creek_abbrev(self):
        self.assertIn(
            "Creek",
            tidy_address("12562 Stillwater Crk, San Antonio, TX 78254-6092"),
        )


if __name__ == "__main__":
    unittest.main()
