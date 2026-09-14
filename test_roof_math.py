"""Unit tests for roof_math. No network."""

import math
import unittest

import roof_math as rm


class RoofMathTests(unittest.TestCase):
    def test_unit_square_pixels(self):
        self.assertEqual(rm.polygon_area_px([(0, 0), (10, 0), (10, 10), (0, 10)]), 100.0)

    def test_six_twelve_multiplier(self):
        self.assertAlmostEqual(rm.sloped_area_sqft(1000, "6/12"), 1118.0, places=1)

    def test_waste_default(self):
        self.assertEqual(rm.apply_waste_factor(1000), 1120.0)

    def test_geodesic_100ft_square(self):
        lat0, lng0 = 29.4241, -98.4936
        m_lat, m_lng = rm.meters_per_degree(lat0)
        dlat = (100 / rm.FT_PER_M) / m_lat
        dlng = (100 / rm.FT_PER_M) / m_lng
        ring = [
            (lat0, lng0),
            (lat0, lng0 + dlng),
            (lat0 + dlat, lng0 + dlng),
            (lat0 + dlat, lng0),
        ]
        area = rm.geodesic_ring_area_sqft(ring)
        self.assertTrue(9900 < area < 10100, area)
        peri = rm.geodesic_ring_perimeter_ft(ring)
        self.assertTrue(395 < peri < 405, peri)

    def test_error_pct(self):
        self.assertAlmostEqual(rm.error_pct(110, 100), 10.0)
        self.assertIsNone(rm.error_pct(10, 0))

    def test_fit_gsd_scale(self):
        traces = [
            {
                "summary": {"total_area_with_pitch_multiplier_sqft": 90, "gsd_scale": 1.0},
                "ev": {"total_roof_area_sqft": 100},
            },
            {
                "summary": {"total_area_with_pitch_multiplier_sqft": 80, "gsd_scale": 1.0},
                "ev": {"total_roof_area_sqft": 100},
            },
        ]
        fitted = rm.fit_gsd_scale(traces)
        self.assertEqual(fitted["n"], 2)
        self.assertTrue(fitted["gsd_scale"] > 1.0)

    def test_summarize_one_facet(self):
        lat0, lng0 = 39.74, -104.99
        m_lat, m_lng = rm.meters_per_degree(lat0)
        dlat = (50 / rm.FT_PER_M) / m_lat
        dlng = (40 / rm.FT_PER_M) / m_lng
        facets = [
            {
                "pitch": "4/12",
                "latlngs": [
                    [lat0, lng0],
                    [lat0, lng0 + dlng],
                    [lat0 + dlat, lng0 + dlng],
                    [lat0 + dlat, lng0],
                ],
            }
        ]
        summary = rm.summarize_facets(facets, waste_pct=12, gsd_scale=1.0)
        self.assertEqual(summary["facet_count"], 1)
        self.assertTrue(1900 < summary["total_flat_area_sqft"] < 2100)
        self.assertGreater(summary["total_area_with_pitch_multiplier_sqft"], summary["total_flat_area_sqft"])


if __name__ == "__main__":
    unittest.main()
