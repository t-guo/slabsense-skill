#!/usr/bin/env python3
"""Tests for SlabSense investability scoring."""

from __future__ import annotations

import unittest

from slabsense.scripts.analyze import Comp, score


class InvestabilityTest(unittest.TestCase):
    def test_low_pop_chase_card_can_have_high_investability(self) -> None:
        listing = {
            "card_name": "Charizard Gold Star #100 EX Dragon Frontiers PSA 8",
            "card_title": "Charizard Gold Star",
            "set": "EX Dragon Frontiers",
            "year": 2006,
            "grade": 8,
            "asking_price": 1200,
            "psa_population_grade": 75,
            "psa_population_total": 600,
            "psa_population_source": "PSA Pop Report",
        }
        comps = [
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 8", 8, 1100, "2026-06-01", "eBay", "high", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 8", 8, 1180, "2026-05-15", "eBay", "high", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 8", 8, 1150, "2026-05-02", "eBay", "high", ""),
        ]
        result = score(listing, comps)
        self.assertGreaterEqual(result["investability_score"], 75)
        self.assertEqual(result["hold_quality"], "high")
        self.assertEqual(result["psa_population_grade"], 75)
        self.assertNotIn("PSA population data", result["missing_info"])

    def test_high_pop_modern_card_has_lower_scarcity(self) -> None:
        listing = {
            "card_name": "Venusaur #15 Celebrations Classic Collection PSA 10",
            "card_title": "Venusaur",
            "set": "Celebrations Classic Collection",
            "year": 2021,
            "grade": 10,
            "asking_price": 190,
            "psa_population_grade": 9000,
            "psa_population_total": 13000,
            "psa_population_source": "PSA Pop Report",
        }
        comps = [
            Comp("Venusaur #15 Celebrations Classic Collection PSA 10", 10, 130, "2026-06-01", "eBay", "high", ""),
            Comp("Venusaur #15 Celebrations Classic Collection PSA 10", 10, 140, "2026-06-02", "eBay", "high", ""),
            Comp("Venusaur #15 Celebrations Classic Collection PSA 10", 10, 150, "2026-06-03", "eBay", "high", ""),
        ]
        result = score(listing, comps)
        self.assertLess(result["scarcity_score"], 40)
        self.assertIn("high sourced grade population (9000)", result["investment_risks"])


if __name__ == "__main__":
    unittest.main()
