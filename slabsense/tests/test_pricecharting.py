#!/usr/bin/env python3
"""Tests for PriceCharting parsing helpers."""

from __future__ import annotations

import unittest

from slabsense.scripts.pricecharting import guess_pop_url, parse_population, parse_price_guide, parse_sales


class PriceChartingTest(unittest.TestCase):
    def test_guess_pop_url(self) -> None:
        self.assertEqual(
            guess_pop_url("EX Dragon Frontiers", "Charizard Gold Star", "100"),
            "https://www.pricecharting.com/pop/item/pokemon-ex-dragon-frontiers/charizard-gold-star-100",
        )

    def test_parse_population(self) -> None:
        payload = parse_population(
            """
            <table>
              <tr><td>1 696 - 696 $3325.00</td></tr>
              <tr><td>3 377 - 377 $3175.19</td></tr>
              <tr><td>10 98 - 98 $58723.00</td></tr>
              <tr><td>Total 4,543 - 4,543</td></tr>
            </table>
            """
        )
        self.assertEqual(payload["population_by_grade"]["3"]["psa"], 377)
        self.assertEqual(payload["population_by_grade"]["10"]["psa"], 98)
        self.assertEqual(payload["psa_population_total"], 4543)

    def test_parse_price_guide_and_sales(self) -> None:
        html = """
        <div>Grade 3 $3,175.19</div>
        <div>Grade 4 $4,096.42</div>
        <div>2026-05-28</div>
        <a>2006 POKEMON EX DRAGON FRONTIERS GOLD STAR #100 CHARIZARD-HOLO PSA 3 #100</a>
        <span>[eBay]</span>
        <span>$3,899.79</span>
        <div>2026-05-17</div>
        <a>2006 POKEMON EX DRAGON FRONTIERS GOLD STAR #100 CHARIZARD-HOLO PSA 4 #100</a>
        <span>[eBay]</span>
        <span>$5,511.43</span>
        """
        self.assertEqual(parse_price_guide(html)["Grade 3"], 3175.19)
        sales = parse_sales(html, grade=3)
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales[0]["sold_price"], 3899.79)
        self.assertEqual(sales[0]["sold_date"], "2026-05-28")


if __name__ == "__main__":
    unittest.main()
