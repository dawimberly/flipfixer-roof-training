"""Unit tests for roof_math. No network."""

import math
import unittest

import roof_math as rm
import roof_views as rv


class RoofMathTests(unittest.TestCase):
    def test_unit_square_pixels(self):
        self.assertEqual(rm.polygon_area_px([(0, 0), (10, 0), (10, 10), (0, 10)]), 100.0)

    def test_six_twelve_multiplier(self):
        self.assertAlmostEqual(rm.sloped_area_sqft(1000, "6/12"), 1118.0, places=1)

    def test_waste_default(self):
        self.assertEqual(rm.apply_waste_factor(1000), 1120.0)

    def test_side_photos_hold_the_rise(self):
        self.assertEqual(rv.pitch_from_profile(8, 12), "8/12")
        self.assertEqual(rv.pitch_from_profile(4, 12), "4/12")
        self.assertEqual(rv.profile_views(0), ("east", "west"))
        self.assertEqual(rv.profile_views(90), ("north", "south"))
        self.assertEqual(rv.facing_view(180), "south")
        self.assertEqual(rv.VIEWS["top"]["holds"], "run")
        self.assertIsNone(rv.VIEWS["top"]["drain_deg"])

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
        self.assertIsNone(summary["eaves_ft"])

    def test_gable_sides_are_the_triangles(self):
        # 40 ft ridge, 12 ft run each side, 4/12. Two planes drain away from the ridge.
        facets = [
            {"pitch": "4/12", "slope_deg": 180, "latlngs": self._feet([(0, 0), (40, 0), (40, 12), (0, 12)])},
            {"pitch": "4/12", "slope_deg": 0, "latlngs": self._feet([(0, 12), (40, 12), (40, 24), (0, 24)])},
        ]
        summary = rm.summarize_facets(facets, waste_pct=0)
        self.assertEqual(summary["facet_count"], 2)
        self.assertAlmostEqual(summary["eaves_ft"], 80.0, delta=0.8)
        self.assertAlmostEqual(summary["ridges_ft"], 40.0, delta=0.8)
        self.assertAlmostEqual(summary["hips_ft"], 0.0, delta=0.2)
        self.assertAlmostEqual(summary["valleys_ft"], 0.0, delta=0.2)
        self.assertAlmostEqual(summary["rakes_ft"], 4 * math.sqrt(12 ** 2 + 4 ** 2), delta=1.0)
        self.assertEqual(summary["shared_edges"], 1)
        ridge = [edge for edge in summary["edges"] if edge["kind"] == "ridge"]
        self.assertEqual(len(ridge), 1)
        self.assertEqual(len(ridge[0]["latlngs"]), 2)

    def test_hip_is_not_pitch_times_plan(self):
        # 40 x 30 equal-pitch hip, 6/12. Ridge is 10. Each hip plan is 15*sqrt(2), rise 7.5, length 22.5.
        facets = [
            {"pitch": "6/12", "slope_deg": 180, "latlngs": self._feet([(0, 0), (40, 0), (25, 15), (15, 15)])},
            {"pitch": "6/12", "slope_deg": 0, "latlngs": self._feet([(0, 30), (15, 15), (25, 15), (40, 30)])},
            {"pitch": "6/12", "slope_deg": 270, "latlngs": self._feet([(0, 0), (15, 15), (0, 30)])},
            {"pitch": "6/12", "slope_deg": 90, "latlngs": self._feet([(40, 0), (40, 30), (25, 15)])},
        ]
        summary = rm.summarize_facets(facets, waste_pct=0)
        self.assertAlmostEqual(summary["eaves_ft"], 140.0, delta=1.2)
        self.assertAlmostEqual(summary["ridges_ft"], 10.0, delta=0.6)
        self.assertAlmostEqual(summary["hips_ft"], 90.0, delta=1.5)
        self.assertAlmostEqual(summary["valleys_ft"], 0.0, delta=0.2)
        self.assertAlmostEqual(summary["rakes_ft"], 0.0, delta=0.2)
        self.assertLess(summary["hips_ft"], 4 * (15 * math.sqrt(2)) * rm.pitch_multiplier("6/12"))

    def test_valley_is_the_shared_hypotenuse(self):
        facets = [
            {"pitch": "6/12", "slope_deg": 0, "latlngs": self._feet([(0, 0), (16, 0), (8, 8)])},
            {"pitch": "6/12", "slope_deg": 90, "latlngs": self._feet([(0, 0), (8, 8), (0, 8)])},
        ]
        summary = rm.summarize_facets(facets, waste_pct=0)
        self.assertAlmostEqual(summary["valleys_ft"], 12.0, delta=0.6)
        compare = rm.compare_to_eagleview(summary, {"total_valleys_ft": 12, "total_ridges_ft": 0})
        self.assertAlmostEqual(compare["valleys_error_pct"], 0.0, delta=5.0)

    def test_shed_high_edge_is_step_not_ridge(self):
        # One plane against a wall. The high level edge has no opposing roof.
        facets = [
            {"pitch": "4/12", "slope_deg": 180, "latlngs": self._feet([(0, 0), (40, 0), (40, 12), (0, 12)])},
        ]
        summary = rm.summarize_facets(facets, waste_pct=0)
        self.assertAlmostEqual(summary["eaves_ft"], 40.0, delta=0.8)
        self.assertAlmostEqual(summary["ridges_ft"], 0.0, delta=0.2)
        self.assertAlmostEqual(summary["steps_ft"], 40.0, delta=0.8)
        self.assertAlmostEqual(summary["rakes_ft"], 2 * math.sqrt(12 ** 2 + 4 ** 2), delta=1.0)

    def test_wall_edges_mark_step(self):
        # Same gable as the triangle test; north hypotenuses flagged as wall.
        facets = [
            {"pitch": "4/12", "slope_deg": 180, "wall_edges": [1], "latlngs": self._feet([(0, 0), (40, 0), (40, 12), (0, 12)])},
            {"pitch": "4/12", "slope_deg": 0, "wall_edges": [1], "latlngs": self._feet([(0, 12), (40, 12), (40, 24), (0, 24)])},
        ]
        summary = rm.summarize_facets(facets, waste_pct=0)
        self.assertAlmostEqual(summary["ridges_ft"], 40.0, delta=0.8)
        self.assertAlmostEqual(summary["eaves_ft"], 80.0, delta=0.8)
        self.assertAlmostEqual(summary["steps_ft"], 2 * math.sqrt(12 ** 2 + 4 ** 2), delta=1.0)
        self.assertAlmostEqual(summary["rakes_ft"], 2 * math.sqrt(12 ** 2 + 4 ** 2), delta=1.0)

    def test_wall_shed_does_not_steal_gable_eave(self):
        # Two-plane gable plus a west shed that dies into the wall, not the eave.
        hypot = math.sqrt(12 ** 2 + 4 ** 2)
        facets = [
            {"pitch": "4/12", "slope_deg": 270, "latlngs": self._feet([(-12, 12), (0, 12), (0, -12), (-12, -12)])},
            {"pitch": "4/12", "slope_deg": 90, "latlngs": self._feet([(12, 12), (0, 12), (0, -12), (12, -12)])},
            {
                "pitch": "4/12",
                "slope_deg": 270,
                "wall": True,
                "wall_edges": [0],
                "latlngs": self._feet([(-26, 10), (-14, 10), (-14, -10), (-26, -10)]),
            },
        ]
        summary = rm.summarize_facets(facets, waste_pct=0)
        self.assertAlmostEqual(summary["ridges_ft"], 24.0, delta=0.8)
        self.assertAlmostEqual(summary["eaves_ft"], 24.0 + 24.0 + 20.0, delta=1.2)
        self.assertAlmostEqual(summary["steps_ft"], 20.0 + hypot, delta=1.2)
        self.assertEqual(summary["valleys_ft"] or 0.0, 0.0)

    def _feet(self, pts):
        lat0, lng0 = 29.4417, -98.6790
        m_lat, m_lng = rm.meters_per_degree(lat0)
        ring = []
        for east, north in pts:
            lat = lat0 + (north / rm.FT_PER_M) / m_lat
            lng = lng0 + (east / rm.FT_PER_M) / m_lng
            ring.append([lat, lng])
        return ring


if __name__ == "__main__":
    unittest.main()
