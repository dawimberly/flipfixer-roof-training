"""Classify shop files and cluster jobs by address or name. No real PDFs."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from bundle_projects import build_bundles
from file_kinds import classify_document, classify_photo, photo_role
from path_keys import keys_from_path, street_keys


class FileKindTests(unittest.TestCase):
    def test_eagleview_filename(self):
        path = Path("Desktop/flpfx/job/EagleView roof report.pdf")
        self.assertEqual(classify_document(path, data=b"%PDF"), "eagleview")

    def test_shop_named_insurance_filename(self):
        path = Path("Downloads/Wimberly Allstate estimate.pdf")
        self.assertEqual(classify_document(path, data=b"%PDF"), "insurance")

    def test_xactimate_bytes(self):
        path = Path("Scan.pdf")
        self.assertEqual(classify_document(path, data=b"%PDF Xactimate estimate"), "xactimate")

    def test_tiny_icon_is_not_a_job_photo(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "logo.png"
            path.write_bytes(b"tiny")
            self.assertIsNone(classify_photo(path))

    def test_photo_roles(self):
        self.assertEqual(photo_role(Path("before-front.jpg")), "before")
        self.assertEqual(photo_role(Path("after-street.jpg")), "after")
        self.assertEqual(photo_role(Path("hail-damage.jpg")), "damage")


class ClusterTests(unittest.TestCase):
    def test_street_pair_keeps_st_vs_way_apart(self):
        st = street_keys("2519 Blue Quail St, San Antonio, TX 78232")
        way = street_keys("2519 Blue Quail Way, San Antonio, TX 78232")
        self.assertIn("2519|blue quail st", st)
        self.assertIn("2519|blue quail way", way)
        self.assertFalse(st & way)

    def test_photos_join_eagleview_by_address_folder(self):
        ev = pd.DataFrame(
            [
                {
                    "source_file": "EV.pdf",
                    "address": "1803 Caraselle Loop CT, San Antonio, TX 78253",
                }
            ]
        )
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw) / "1803 Caraselle Loop"
            folder.mkdir()
            before = folder / "before.jpg"
            after = folder / "after.jpg"
            before.write_bytes(b"x" * 30_000)
            after.write_bytes(b"y" * 30_000)
            photos = [
                {
                    "source_path": str(before),
                    "filename": before.name,
                    "role": "before",
                    "join_keys": ";;".join(keys_from_path(before)),
                },
                {
                    "source_path": str(after),
                    "filename": after.name,
                    "role": "after",
                    "join_keys": ";;".join(keys_from_path(after)),
                },
            ]
        bundles, stats = build_bundles(ev, pd.DataFrame(), photos)
        self.assertEqual(stats["n_projects"], 1)
        self.assertEqual(stats["n_photos"], 2)
        self.assertEqual(stats["n_before_after"], 1)
        self.assertTrue(bundles[0]["eagleview_n"])

    def test_client_name_joins_ticket_and_photos(self):
        xm = pd.DataFrame(
            [
                {
                    "source_file": "ESCOBAR.pdf",
                    "address": "",
                    "estimate_number": "ESCOBAR",
                }
            ]
        )
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw) / "Escobar"
            folder.mkdir()
            photo = folder / "roof.jpg"
            photo.write_bytes(b"z" * 30_000)
            photos = [
                {
                    "source_path": str(photo),
                    "filename": photo.name,
                    "role": "roof",
                    "join_keys": ";;".join(keys_from_path(photo)),
                }
            ]
        bundles, stats = build_bundles(pd.DataFrame(), xm, photos)
        self.assertEqual(stats["n_projects"], 1)
        self.assertEqual(bundles[0]["xactimate_n"], 1)
        self.assertEqual(bundles[0]["photo_n"], 1)


if __name__ == "__main__":
    unittest.main()
