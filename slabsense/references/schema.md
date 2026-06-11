# SlabSense Schema

## Listing JSON

```json
{
  "card_name": "Charizard Gold Star",
  "card_title": "Charizard Gold Star",
  "card_number": "100/101",
  "card_number_full": "100/101",
  "set": "EX Dragon Frontiers",
  "year": 2006,
  "language": "English",
  "grading_company": "PSA",
  "grade": 3,
  "psa_population_grade": 75,
  "psa_population_total": 600,
  "psa_population_source": "PSA Pop Report",
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

`card_name` should be the canonical identity used for comp search when available:

```text
Charizard VMAX #SV107 Shining Fates PSA 10
```

Keep parsed identity components in `card_title`, `card_number`, `card_number_full`, `set`, `year`, `language`, `grading_company`, and `grade` when available. `card_number` is the comp-search number; for printed numbers like `GG69/GG70`, keep `card_number` as `GG69` and `card_number_full` as `GG69/GG70`.

Use `psa_population_grade`, `psa_population_total`, and `psa_population_source` only when population data is sourced from PSA, eBay grader data, or another cited source. Do not infer or estimate population values.

## URL Import

Use the Chrome-backed importer to create listing JSON from marketplace URLs:

```bash
python3 slabsense/scripts/cleanup_tmp.py --execute
```

```bash
node slabsense/scripts/ensure_chrome.js
```

```bash
node slabsense/scripts/browser_listing.js \
  "https://www.ebay.com/itm/123456789012" \
  --output listing.json
```

The cleanup step deletes only matching `/private/tmp/slabsense-*` artifacts older than 24 hours. Do not use `--all` or `--profile` as part of automatic URL import.

Add `--screenshot listing.png` only when the recommendation depends on visual evidence. `ensure_chrome.js` reuses `http://127.0.0.1:9222` when it is already running, otherwise it launches an isolated Chrome profile at `/tmp/slabsense-chrome`.

The importer may produce `extraction_status: partial` when title, price, grade, or image metadata is missing. It may fail with `extraction_status: blocked` when eBay or another marketplace returns an error page, login wall, or bot protection. In blocked cases, manually provide listing facts rather than treating the URL as evidence.

Use `parse_saved_listing.py` only for offline parsing of already-saved HTML or explicit debugging:

```bash
python3 slabsense/scripts/parse_saved_listing.py saved-listing.html \
  --url "https://www.ebay.com/itm/123456789012" \
  --output listing.json \
  --pretty
```

Do not use plain HTTP fetching as the routine marketplace URL importer.

## Temp Cleanup

Browser screenshots and listing JSON are not stored inside `/tmp/slabsense-chrome`; that directory is the isolated Chrome profile. Preview removable SlabSense temp artifacts with:

```bash
python3 slabsense/scripts/cleanup_tmp.py
```

Delete matching temp artifacts older than 24 hours with:

```bash
python3 slabsense/scripts/cleanup_tmp.py --execute
```

Remove the isolated Chrome profile only when you want to reset session/cache state:

```bash
python3 slabsense/scripts/cleanup_tmp.py --profile --execute
```

## Comps CSV

Columns:

```csv
card_name,set,year,language,grade,sold_price,sold_date,source,cert_number,confidence,notes
```

The analyzer prioritizes same card, same language, same grade, and recent sales. Nearby-grade comps are weaker evidence and should be labeled as such.

## Comp Sources

Recommendations should include comp provenance:

```json
{
  "comp_sources_checked": [
    {
      "source": "Fanatics Collect",
      "status": "checked | blocked | unavailable",
      "notes": "Visible in-page sales history"
    }
  ],
  "comp_summary": [
    {
      "sold_price": 1075,
      "sold_date": "2026-06-01",
      "source": "Fanatics Collect",
      "confidence": "high",
      "notes": "Exact PSA 8 same-card sale"
    }
  ],
  "nearby_grade_or_active_ask_context": [
    {
      "price": 1250,
      "source": "eBay",
      "type": "active ask",
      "notes": "Not used as a sold comp"
    }
  ]
}
```

## Output JSON

```json
{
  "verdict": "buy | watch | pass",
  "fair_value_low": 0,
  "fair_value_high": 0,
  "suggested_offer": 0,
  "expected_downside": "low | medium | high",
  "liquidity_score": 0,
  "investability_score": 0,
  "demand_score": 0,
  "scarcity_score": 0,
  "hold_quality": "low | medium | high",
  "psa_population_grade": 0,
  "psa_population_total": 0,
  "psa_population_source": "",
  "investment_thesis": [],
  "investment_risks": [],
  "regret_risk_score": 0,
  "confidence": 0,
  "condition_notes": [],
  "comp_sources_checked": [],
  "comp_summary": [],
  "nearby_grade_or_active_ask_context": [],
  "red_flags": [],
  "missing_info": [],
  "collector_summary": ""
}
```
