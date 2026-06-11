#!/usr/bin/env python3
"""Tests for SlabSense title canonicalization."""

from __future__ import annotations

import unittest

from slabsense.scripts.canonicalize import canonicalize_title


class CanonicalizeTest(unittest.TestCase):
    def test_charizard_shining_fates(self) -> None:
        result = canonicalize_title(
            "PSA 10 NEW SLAB 2021 CHARIZARD VMAX POKEMON SWORD & SHIELD SHINING FATES #SV107 | eBay"
        )
        self.assertEqual(result["canonical_card_name"], "Charizard VMAX #SV107 Shining Fates PSA 10")
        self.assertEqual(result["card_title"], "Charizard VMAX")
        self.assertEqual(result["card_number"], "SV107")
        self.assertEqual(result["set"], "Shining Fates")
        self.assertEqual(result["year"], 2021)

    def test_celebrations_venusaur(self) -> None:
        result = canonicalize_title("Venusaur - 2021 Pokemon Celebrations Classic Collection Holo #15 - PSA 10 | eBay")
        self.assertEqual(result["canonical_card_name"], "Venusaur #15 Celebrations Classic Collection PSA 10")
        self.assertEqual(result["card_title"], "Venusaur")
        self.assertEqual(result["card_number"], "15")
        self.assertEqual(result["set"], "Celebrations Classic Collection")

    def test_crown_zenith_giratina(self) -> None:
        result = canonicalize_title("Giratina VSTAR (Secret) GG69/GG70 SWSH: Crown Zenith PSA 10 | eBay")
        self.assertEqual(result["canonical_card_name"], "Giratina VSTAR #GG69 Crown Zenith PSA 10")
        self.assertEqual(result["card_title"], "Giratina VSTAR")
        self.assertEqual(result["card_number"], "GG69")
        self.assertEqual(result["card_number_full"], "GG69/GG70")
        self.assertEqual(result["set"], "Crown Zenith")


if __name__ == "__main__":
    unittest.main()
