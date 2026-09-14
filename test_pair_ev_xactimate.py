"""Pairing and carrier/code classification. No PDFs."""

import unittest
from pathlib import Path

import pandas as pd

from extract_xactimate_data import address_keys, dummy_address, parse_fields, property_key, ticket_notes
from pair_ev_xactimate import build_spread, classify_role, pair_rows


class AddressTests(unittest.TestCase):
    def test_zip_separates_repeat_streets(self):
        a = address_keys("100 Main St, Austin, TX 78701")
        b = address_keys("100 Main St, Dallas, TX 75201")
        self.assertTrue(a & b)
        self.assertIn("100|main|78701", a)
        self.assertNotIn("100|main|78701", b)

    def test_blue_quail_st_vs_way(self):
        st = property_key("2519 Blue Quail St, San Antonio, TX 78232")
        way = property_key("2519 Blue Quail Way, San Antonio, TX 78232")
        self.assertNotEqual(st, way)

    def test_dummy_address_skipped(self):
        self.assertTrue(dummy_address("Anywhere, IL 00000-0000"))
        self.assertEqual(address_keys("Anywhere, IL 00000-0000"), set())


class ExtractTests(unittest.TestCase):
    def test_claim_and_ice_water(self):
        text = """
Property: 1803 CARASELLE LOOP CT
San Antonio, TX 78253
Claim Number: 0790054506 Policy Number: 000886309155 Type of Loss: Hail
Date of Loss: 3/31/2025 8:51 PM Date Received:
Date Entered: 5/14/2025 12:58 PM
Insurance Company: Allstate Vehicle and Property Insurance Company
Price List: TXSA8X_MAY25
Estimate: ESCOBAR
1. Remove Laminated - comp. shingle 32.45 SQ 74.24 0.00 0.00 2,409.09
2. Laminated - comp. shingle rfg. - 39.00 SQ 0.00 285.49 336.74 11,470.85
11. Ice & water barrier 180.00 SF 0.00 1.75 6.30 321.30
24. Additional charge for steep roof - 45.00 SQ 0.00 46.63 0.00 2,098.35
Line Item Totals: Dwelling 1.00 2,098.35 0.00 33,300.85
"""
        fields = parse_fields(text)
        self.assertEqual(fields["claim_number"], "0790054506")
        self.assertEqual(fields["estimate_number"], "ESCOBAR")
        self.assertEqual(fields["ice_water"], 180.0)
        self.assertEqual(fields["insurance_company"].split()[0], "Allstate")
        self.assertIn("carrier header", ticket_notes(text, "Escobar insurance.pdf"))

    def test_street_not_dropped_when_claim_number_is_on_the_same_line(self):
        text = """
Property: 9119 Alpine Trail St Claim Number: 5385S250W
San Antonio, TX 78250-3047
Estimate: ROXANNE_ARCOS
"""
        fields = parse_fields(text)
        self.assertIn("9119", fields["address"])
        self.assertIn("Alpine", fields["address"])

    def test_street_not_dropped_when_cellular_is_on_the_same_line(self):
        text = """
Property: 9119 Alpine Trail St Cellular: (210) 386-4171
San Antonio, TX 78250-3047
Estimate: ROXANNE_ARCOS
"""
        fields = parse_fields(text)
        self.assertIn("9119 Alpine Trail", fields["address"])


class RoleTests(unittest.TestCase):
    def test_insurance_filename_is_carrier(self):
        role, notes = classify_role(
            {
                "insurance_company": "Allstate",
                "ice_water": 180,
                "steep_charge": 2500,
                "grand_total": 29493,
                "ticket_note": "insurance; carrier header",
            },
            "Escobar insurance.pdf",
        )
        self.assertEqual(role, "carrier")
        self.assertIn("carrier", notes)

    def test_mrc_with_code_lines_is_code(self):
        role, _notes = classify_role(
            {
                "ice_water": 180,
                "steep_charge": 2098,
                "felt_30": 32,
                "grand_total": 33300,
                "ticket_note": "mrc; contractor header",
            },
            "MRC ESTIMATE ESCOBAR.pdf",
        )
        self.assertEqual(role, "code")

    def test_unknown_when_signals_conflict_or_thin(self):
        role, _notes = classify_role({"grand_total": 18000}, "Roof Estimate.pdf")
        self.assertEqual(role, "unknown")


class PairTests(unittest.TestCase):
    def test_one_ev_many_xm(self):
        ev = pd.DataFrame(
            [
                {
                    "address": "1803 Caraselle Loop Ct, San Antonio, TX 78253",
                    "source_file": "Justine Escobar Eagle.PDF",
                    "total_squares": 35.0,
                    "total_roof_area_sqft": 3500,
                    "predominant_pitch": "6/12",
                    "num_facets": 10,
                }
            ]
        )
        xa = pd.DataFrame(
            [
                {
                    "source_file": "Escobar insurance.pdf",
                    "address": "1803 CARASELLE LOOP CT, SAN ANTONIO, TX 78253",
                    "grand_total": 23647.72,
                    "roof_squares": 35.08,
                    "insurance_company": "Allstate",
                    "ticket_note": "insurance; carrier header",
                    "ice_water": 180,
                    "steep_charge": 2529,
                },
                {
                    "source_file": "MRC ESTIMATE ESCOBAR.pdf",
                    "address": "1803 Caraselle Loop Ct, San Antonio, TX 78253",
                    "grand_total": 33300.85,
                    "roof_squares": 39.0,
                    "ticket_note": "mrc; contractor header",
                    "ice_water": 180,
                    "steep_charge": 2098,
                    "felt_30": 32,
                },
            ]
        )
        paired = pair_rows(ev, xa, pair_map_path=None)
        self.assertEqual(len(paired), 2)
        self.assertEqual(paired["ev_source_file"].nunique(), 1)
        self.assertEqual(set(paired["role"]), {"carrier", "code"})
        spread = build_spread(paired, ev)
        self.assertEqual(len(spread), 1)
        self.assertAlmostEqual(spread.iloc[0]["carrier_total"], 23647.72)
        self.assertAlmostEqual(spread.iloc[0]["code_total"], 33300.85)
        self.assertAlmostEqual(spread.iloc[0]["delta"], 33300.85 - 23647.72)
        self.assertNotIn("recommended_mid", spread.columns)
        self.assertEqual(int(spread.iloc[0]["xm_count"]), 2)

    def test_dummy_does_not_folder_onto_a_real_roof(self):
        ev = pd.DataFrame(
            [
                {
                    "address": "9119 Alpine Trail St, San Antonio, TX 78250",
                    "source_file": "66129541.PDF",
                    "total_squares": 18.0,
                    "predominant_pitch": "6/12",
                    "num_facets": 9,
                }
            ]
        )
        xa = pd.DataFrame(
            [
                {
                    "source_file": "State Farm Initial.pdf",
                    "address": "Anywhere, IL 00000",
                    "grand_total": 380.93,
                    "insurance_company": "State Farm",
                    "ticket_note": "state farm",
                }
            ]
        )
        pair_map = Path("_tmp_pairs.csv")
        pd.DataFrame(
            [{"ev_source_file": "66129541.PDF", "xact_files": "State Farm Initial.pdf"}]
        ).to_csv(pair_map, index=False)
        try:
            paired = pair_rows(ev, xa, pair_map_path=pair_map)
        finally:
            pair_map.unlink(missing_ok=True)
        self.assertTrue(pd.isna(paired.iloc[0]["ev_source_file"]))

    def test_untagged_spread_uses_min_max_not_a_mid(self):
        ev = pd.DataFrame(
            [
                {
                    "address": "10102 Silver Branch Rd, San Antonio, TX 78254",
                    "source_file": "66614519.PDF",
                    "total_squares": 18.66,
                    "predominant_pitch": "5/12",
                    "num_facets": 12,
                }
            ]
        )
        xa = pd.DataFrame(
            [
                {
                    "source_file": "ticket_a.pdf",
                    "address": "10102 Silver Branch Rd, San Antonio, TX 78254",
                    "grand_total": 33595.42,
                },
                {
                    "source_file": "ticket_b.pdf",
                    "address": "10102 Silver Branch Rd, San Antonio, TX 78254",
                    "grand_total": 82305.59,
                },
            ]
        )
        paired = pair_rows(ev, xa, pair_map_path=None)
        self.assertTrue((paired["role"] == "unknown").all())
        spread = build_spread(paired, ev)
        self.assertAlmostEqual(spread.iloc[0]["carrier_total"], 33595.42)
        self.assertAlmostEqual(spread.iloc[0]["code_total"], 82305.59)
        self.assertIn("untagged", spread.iloc[0]["role_guess_notes"])
        self.assertNotIn("recommended", spread.iloc[0]["role_guess_notes"].lower())


if __name__ == "__main__":
    unittest.main()
