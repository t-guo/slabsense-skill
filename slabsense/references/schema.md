# SlabSense Schema

## Listing JSON

```json
{
  "card_name": "Charizard Gold Star",
  "set": "EX Dragon Frontiers",
  "year": 2006,
  "language": "English",
  "grading_company": "PSA",
  "grade": 3,
  "cert_number": "12345678",
  "asking_price": 1200,
  "listing_url": "https://...",
  "listing_notes": "Seller says clean front, back photo missing.",
  "buyer_intent": "personal_collection | investment | trade_candidate | unknown",
  "front_image_notes": "Visible crease near holo, decent centering.",
  "back_image_notes": "Back not shown.",
  "photo_quality": "clear | mixed | poor | unknown",
  "extraction_status": "ok | partial | blocked",
  "extraction_warnings": ["asking price was not found"],
  "image_url": "https://..."
}
```

Required fields for deterministic scoring: `card_name`, `grade`, and `asking_price`.

## URL Import

Use the URL importer to create listing JSON when a marketplace exposes public metadata:

```bash
python3 slabsense/scripts/fetch_listing.py \
  "https://www.ebay.com/itm/123456789012" \
  --output listing.json \
  --pretty
```

The importer may produce `extraction_status: partial` when title, price, grade, or image metadata is missing. It may fail with `extraction_status: blocked` when eBay or another marketplace returns an error page, login wall, or bot protection. In blocked cases, manually provide listing facts rather than treating the URL as evidence.

## Comps CSV

Columns:

```csv
card_name,set,year,language,grade,sold_price,sold_date,source,cert_number,notes
```

The analyzer prioritizes same card, same language, same grade, and recent sales. Nearby-grade comps are weaker evidence and should be labeled as such.

## Output JSON

```json
{
  "verdict": "buy | watch | pass",
  "fair_value_low": 0,
  "fair_value_high": 0,
  "suggested_offer": 0,
  "expected_downside": "low | medium | high",
  "liquidity_score": 0,
  "regret_risk_score": 0,
  "confidence": 0,
  "condition_notes": [],
  "comp_summary": [],
  "red_flags": [],
  "missing_info": [],
  "collector_summary": ""
}
```
