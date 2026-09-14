"""Retrain defaults from tables. No PDFs. Never invent a bid mid."""

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import roof_defaults


class RoofDefaultsTests(unittest.TestCase):
    def test_eagleview_averages_and_pitch_mix(self):
        ev = pd.DataFrame(
            [
                {"total_squares": 28, "waste_table_pct": 10, "num_facets": 8, "predominant_pitch": "6/12"},
                {"total_squares": 32, "waste_table_pct": 14, "num_facets": 12, "predominant_pitch": "6/12"},
                {"total_squares": 30, "waste_table_pct": 12, "num_facets": 10, "predominant_pitch": "4/12"},
            ]
        )
        geometry = roof_defaults.from_eagleview(ev)
        self.assertEqual(geometry["n_eagleview_reports"], 3)
        self.assertEqual(geometry["avg_squares"], 30.0)
        self.assertEqual(geometry["median_waste_pct"], 12.0)
        self.assertEqual(geometry["avg_facets"], 10.0)
        self.assertEqual(geometry["predominant_pitch"], "6/12")
        self.assertEqual(geometry["pitch_mix"]["6/12"], 2)

    def test_spread_does_not_recommend_a_mid(self):
        spread = pd.DataFrame(
            [
                {"carrier_total": 9000, "code_total": 12000, "delta": 3000, "xm_count": 2},
                {"carrier_total": 8000, "code_total": 10000, "delta": 2000, "xm_count": 2},
                {"carrier_total": 5000, "code_total": 5000, "delta": 0, "xm_count": 1},
            ]
        )
        info = roof_defaults.from_spread(spread)
        self.assertEqual(info["properties"], 3)
        self.assertEqual(info["with_2plus_tickets"], 2)
        self.assertEqual(info["median_code_minus_carrier"], 2500)
        self.assertEqual(info["note"], "never average tickets; no recommended mid")

    def test_payload_writes_without_addresses(self):
        ev = pd.DataFrame(
            [{"total_squares": 20, "waste_table_pct": 12, "num_facets": 6, "predominant_pitch": "5/12", "address": "secret"}]
        )
        payload = roof_defaults.build_payload(ev, pd.DataFrame(), [])
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "roof_defaults.json"
            roof_defaults.write_defaults(payload, path)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("secret", text)
            loaded = json.loads(text)
            self.assertEqual(loaded["n_eagleview_reports"], 1)
            self.assertEqual(loaded["waste_pct"], 12.0)


if __name__ == "__main__":
    unittest.main()
