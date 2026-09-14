"""Discover extra Flip Fixer / flpfx folders. No network."""

import unittest
from pathlib import Path

from flip_folders import discover_flip_folders, ingest_roots, looks_like_flip_folder


class FlipFolderTests(unittest.TestCase):
    def test_looks_like_flip_folder_accepts_typos_and_spaces(self):
        self.assertTrue(looks_like_flip_folder("flpfx"))
        self.assertTrue(looks_like_flip_folder("flpfxr"))
        self.assertTrue(looks_like_flip_folder("FLP Fixer"))
        self.assertTrue(looks_like_flip_folder("The Flip Fixer"))
        self.assertTrue(looks_like_flip_folder("flipfixer-old"))
        self.assertFalse(looks_like_flip_folder("Downloads"))
        self.assertFalse(looks_like_flip_folder("trading-bot"))

    def test_discover_and_ingest_includes_named_copies(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / "Desktop").mkdir()
            (home / "Desktop" / "flpfx").mkdir()
            (home / "Desktop" / "Flip Fixer backup").mkdir()
            (home / "Desktop" / "notes").mkdir()
            (home / "Downloads").mkdir()

            found = {path.name for path in discover_flip_folders(home=home)}
            self.assertEqual(found, {"flpfx", "Flip Fixer backup"})

            names = {path.name for path in ingest_roots(home=home)}
            self.assertIn("Desktop", names)
            self.assertIn("Downloads", names)
            self.assertIn("flpfx", names)
            self.assertIn("Flip Fixer backup", names)
            self.assertNotIn("notes", names)

    def test_collect_reports_from_a_named_copy(self):
        import tempfile

        from collect_reports import collect

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            src = home / "Desktop" / "flpfx"
            dest = home / "reports"
            src.mkdir(parents=True)
            (src / "EagleView roof report.pdf").write_bytes(b"%PDF-1.4 fake")
            (src / "random.pdf").write_bytes(b"%PDF-1.4 skip")
            copied = collect(ingest_roots(home=home), dest)
            self.assertEqual([path.name for path in copied], ["EagleView roof report.pdf"])
            self.assertTrue((dest / "EagleView roof report.pdf").exists())


if __name__ == "__main__":
    unittest.main()
