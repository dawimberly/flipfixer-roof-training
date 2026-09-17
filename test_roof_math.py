"""Stdlib tests for roof math and the 1-story sanity band."""

import unittest

from roof_math import (
    apply_waste_factor,
    diagnose_measured_squares,
    one_story_expected_squares,
    rectangle_perimeter_ft,
    sloped_area_sqft,
    trace_sanity,
)


class RoofMathTests(unittest.TestCase):
    def test_pitch_and_waste(self):
        self.assertAlmostEqual(sloped_area_sqft(1000, "4/12"), 1054.0)
        self.assertEqual(apply_waste_factor(1000, 12), 1120.0)

    def test_ranch_perimeter(self):
        peri = rectangle_perimeter_ft(2293, aspect=1.9)
        # ~66 x 35 ranch should be around 200 lf of wall.
        self.assertGreater(peri, 180)
        self.assertLess(peri, 230)

    def test_one_story_expected_near_living_plus_garage(self):
        squares = one_story_expected_squares(1673, 620, pitch="4/12")
        # Plan is footprint + overhangs, then 4/12. Should land mid-20s, not 39.
        self.assertGreater(squares, 24.0)
        self.assertLess(squares, 30.0)

    def test_thirty_nine_squares_is_high_for_1700_sf_ranch(self):
        self.assertEqual(trace_sanity(39.0, 1673, 620, stories=1, pitch="4/12"), "high")
        self.assertEqual(trace_sanity(39.0, 1673, 620, stories=1, pitch="6/12"), "high")
        mid = one_story_expected_squares(1673, 620, pitch="4/12")
        self.assertEqual(trace_sanity(mid, 1673, 620, stories=1, pitch="4/12"), "ok")
        self.assertEqual(trace_sanity(19.5, 1673, 620, stories=1, pitch="4/12"), "low")

    def test_thirty_nine_is_doubled_living_plus_waste(self):
        msg = diagnose_measured_squares(39.0, 1673, 620, pitch="4/12")
        self.assertIn("counted twice", msg)
        self.assertIn("garage", msg)
        living_sloped = sloped_area_sqft(1673, "4/12") / 100
        self.assertAlmostEqual(living_sloped * 2 * 1.12, 39.46, delta=0.05)


if __name__ == "__main__":
    unittest.main()
