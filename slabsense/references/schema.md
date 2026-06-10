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
  "photo_quality": "clear | mixed | poor | unknown"
}
```

Required fields for deterministic scoring: `card_name`, `grade`, and `asking_price`.

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
