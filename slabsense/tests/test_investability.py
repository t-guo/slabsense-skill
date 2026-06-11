#!/usr/bin/env python3
"""Tests for SlabSense investability scoring."""

from __future__ import annotations

import unittest

from slabsense.scripts.analyze import Comp, render_text, score


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
        self.assertEqual(result["hold_verdict"], "high")
        self.assertIn(result["deal_verdict"], {"buy", "watch", "pass"})
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

    def test_low_seller_feedback_flags_high_value_slab(self) -> None:
        listing = {
            "card_name": "Charizard Gold Star #100 EX Dragon Frontiers PSA 3",
            "card_title": "Charizard Gold Star",
            "set": "EX Dragon Frontiers",
            "year": 2006,
            "grade": 3,
            "asking_price": 4800,
            "seller_feedback_count": 24,
            "seller_positive_percent": 100,
        }
        comps = [
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 3000, "2026-06-01", "eBay", "high", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 3400, "2026-05-15", "eBay", "high", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 3800, "2026-05-02", "eBay", "high", ""),
        ]
        result = score(listing, comps)
        self.assertIn("seller feedback count is low for a high-value slab", result["red_flags"])

    def test_low_pop_chase_card_fair_value_includes_scarcity_premium(self) -> None:
        listing = {
            "card_name": "Charizard Gold Star #100 EX Dragon Frontiers PSA 3",
            "card_title": "Charizard Gold Star",
            "set": "EX Dragon Frontiers",
            "year": 2006,
            "grade": 3,
            "asking_price": 4800,
            "psa_population_grade": 377,
            "psa_population_total": 4543,
            "psa_population_source": "PriceCharting population report",
        }
        comps = [
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 3899.79, "2026-05-28", "PriceCharting", "medium", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 2986.86, "2026-05-17", "PriceCharting", "medium", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 3999.00, "2026-05-05", "PriceCharting", "medium", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 3371.00, "2026-05-02", "PriceCharting", "medium", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 3001.00, "2026-04-29", "PriceCharting", "medium", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 2855.00, "2026-04-29", "PriceCharting", "medium", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 3551.00, "2026-04-23", "PriceCharting", "medium", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 2650.00, "2026-04-16", "PriceCharting", "medium", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 2999.00, "2026-03-24", "PriceCharting", "medium", ""),
            Comp("Charizard Gold Star #100 EX Dragon Frontiers PSA 3", 3, 2476.00, "2026-03-01", "PriceCharting", "medium", ""),
        ]
        result = score(listing, comps)
        self.assertEqual(result["fair_value_low"], 3210)
        self.assertEqual(result["fair_value_high"], 3810)
        self.assertEqual(result["verdict"], "pass")

    def test_text_render_uses_not_available_without_comps(self) -> None:
        result = score({"card_name": "Giratina VSTAR #GG69 Crown Zenith PSA 10", "asking_price": 0}, [])
        text = render_text(result)
        self.assertIn("Fair value: not available", text)
        self.assertIn("Suggested offer: not available", text)


if __name__ == "__main__":
    unittest.main()
