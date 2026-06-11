#!/usr/bin/env python3
"""Tests for saved listing HTML parsing."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "parse_saved_listing.py"


def run_parser(html_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(html_path), *args],
        check=False,
        text=True,
        capture_output=True,
    )


class ParseSavedListingTest(unittest.TestCase):
    def test_parse_saved_listing_extracts_metadata(self) -> None:
        html = """<!doctype html>
        <html>
          <head>
            <title>PSA 10 Charizard VMAX SV107 Shining Fates | eBay</title>
            <meta property="og:price:amount" content="299.99">
            <meta property="og:image" content="https://i.ebayimg.com/images/g/card/s-l1600.jpg">
          </head>
          <body>Listing body</body>
        </html>
        """
        with tempfile.TemporaryDirectory() as tmp:
            html_path = Path(tmp) / "listing.html"
            html_path.write_text(html, encoding="utf-8")

            result = run_parser(html_path, "--url", "https://www.ebay.com/itm/123", "--pretty")
            self.assertEqual(result.returncode, 0, result.stderr)
            listing = json.loads(result.stdout)
            self.assertEqual(listing["listing_url"], "https://www.ebay.com/itm/123")
            self.assertEqual(listing["card_name"], "Charizard VMAX #SV107 Shining Fates PSA 10")
            self.assertEqual(listing["card_title"], "Charizard VMAX")
            self.assertEqual(listing["card_number"], "SV107")
            self.assertEqual(listing["set"], "Shining Fates")
            self.assertEqual(listing["grading_company"], "PSA")
            self.assertEqual(listing["grade"], 10.0)
            self.assertEqual(listing["asking_price"], 299.99)
            self.assertEqual(listing["extraction_status"], "ok")
            self.assertTrue(listing["image_url"].startswith("https://i.ebayimg.com/"))

    def test_parse_saved_listing_blocks_error_pages(self) -> None:
        html = """<!doctype html>
        <html>
          <head><title>Error Page | eBay</title></head>
          <body>Something went wrong on our end</body>
        </html>
        """
        with tempfile.TemporaryDirectory() as tmp:
            html_path = Path(tmp) / "blocked.html"
            html_path.write_text(html, encoding="utf-8")

            result = run_parser(html_path, "--url", "https://www.ebay.com/itm/blocked")
            self.assertEqual(result.returncode, 3)
            self.assertIn("eBay returned a generic marketplace error page", result.stderr)


if __name__ == "__main__":
    unittest.main()
