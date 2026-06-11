---
name: slabsense
description: Analyze PSA-graded Pokemon card listings as SlabSense, an AI TCG deal copilot. Use when the user wants Buy / Watch / Pass guidance, regret-risk scoring, comp review, listing risk analysis, offer-price guidance, or a reusable prompt for graded Pokemon card purchases without API keys.
---

# SlabSense

SlabSense is a portable agent skill for evaluating PSA-graded Pokemon card purchases. It is designed to work without API keys: the hosting agent provides the reasoning layer, while bundled scripts provide deterministic scoring, prompt export, browser-backed listing capture, temp cleanup, and eval checks. It can run in Codex, Claude Code, or another local agent environment that can read this skill folder and execute Python/Node scripts.

## Workflow

1. Gather only grounded inputs:
   - canonical card identity, card name, card number, set/year, language, PSA grade, cert number or cert URL if available
   - asking price, listing URL or listing notes
   - front/back image observations or image paths
   - comparable sales from CSV, JSON, or user-provided text
   - PSA population data and source when available from PSA, eBay grader data, or another cited source
   - buyer intent: personal collection, investment, trade candidate, or unknown
2. Separate facts from inferences.
   - Never invent PSA population data, cert facts, sold prices, seller terms, or condition flaws.
   - Mark unavailable facts as missing information.
   - Use cautious condition language when photos are weak.
   - Use canonical identity fields produced by `canonicalize.py` for comp search, but treat them as title-derived inferences unless independently verified.
   - Use PSA population fields only when sourced. Never estimate pop values from vibes, rarity labels, or active listing claims without attribution.
3. Run comp sourcing as a regular part of deal analysis.
   - Use [references/comp-sourcing.md](references/comp-sourcing.md) for exact-match sold comp sourcing, source confidence, and conflict handling.
   - Separate exact sold comps, nearby-grade comps, active asks, and marketplace in-page sales history.
   - For sourced low-pop/high-demand chase cards, let the fair-value range incorporate a transparent scarcity premium above the mechanical recent-comp band.
   - If current web access or source pages are blocked, state which comp sources could not be checked and lower confidence.
4. Prefer deterministic scripts when the user provides structured input files.
   - Analyze: `python3 scripts/analyze.py <listing.json> --comps <comps.csv>`
   - Prompt export: `python3 scripts/prompt.py <listing.json> --comps <comps.csv>`
   - Chrome warm check: `node scripts/ensure_chrome.js`
   - Browser URL import: `node scripts/browser_listing.js <listing-url> --output listing.json`
   - PriceCharting parser: `python3 scripts/pricecharting.py --set <set> --card-title <card-title> --card-number <number> --grade <grade>`
   - Saved HTML parser: `python3 scripts/parse_saved_listing.py <saved-listing.html> --url <listing-url> --output listing.json`
   - Add `--screenshot listing.png` only when photo or condition inspection is needed.
   - Temp cleanup preview: `python3 scripts/cleanup_tmp.py`
   - Temp cleanup execute: `python3 scripts/cleanup_tmp.py --execute`
   - Evals: `python3 scripts/eval.py`
5. For marketplace URLs, skip plain HTTP metadata fetching and use Chrome-backed import first.
   - First run conservative temp cleanup:
     `python3 scripts/cleanup_tmp.py --execute`
   - This deletes only matching `/private/tmp/slabsense-*` artifacts older than 24 hours. Do not use `--all` or `--profile` automatically.
   - Ensure an isolated Chrome debugging session is available:
     `node scripts/ensure_chrome.js`
   - Then run: `node scripts/browser_listing.js <listing-url> --output listing.json`
   - Use `--screenshot listing.png` only when the recommendation depends on photo review, slab/cert visibility, seller terms shown in-page, or other visual evidence.
   - If the browser import returns `extraction_status: ok` or `partial`, use the extracted JSON and clearly label missing facts.
   - Use `pricecharting.py` or direct source pages to gather exact-grade sold comps and sourced population data when available.
   - Do not use plain HTTP fetching as a routine fallback for marketplace URLs. Use `parse_saved_listing.py` only for offline parsing of already-saved HTML or explicit debugging.
   - If both import paths are blocked, do not invent listing facts. Ask for the title, price, grade, photo observations, seller terms, and comps.
   - Screenshots and listing JSON are not stored inside `/tmp/slabsense-chrome`; that path is the isolated Chrome profile. Use `python3 scripts/cleanup_tmp.py` to preview removable `/private/tmp/slabsense-*` artifacts, and add `--execute` to delete them.
6. Return a concise collector-facing recommendation:
   - verdict: Buy, Watch, or Pass
   - fair value range
   - suggested offer
   - downside, liquidity, investability, regret risk, confidence
   - comp sources checked and exact sold comps used
   - top risks, red flags, missing information
   - short rationale grounded in supplied evidence

## Decision Guidance

Use [references/risk-rubric.md](references/risk-rubric.md) for scoring rules and red flags.
Use [references/comp-sourcing.md](references/comp-sourcing.md) for comp source hierarchy and fair-value evidence requirements.
Use [references/schema.md](references/schema.md) for accepted input and output fields.

## Verdict Rules

- **Buy**: asking price is below or near the conservative fair range, comps are relevant, major missing-info risks are low, and regret risk is low or medium.
- **Watch**: price is plausible but key information is missing, comps are thin/noisy, or the card may be acceptable only at a lower offer.
- **Pass**: asking price is materially above comps, red flags are serious, condition confidence is too weak for the price, or regret risk is high.

## Output Contract

When possible, include this JSON-compatible structure after the prose summary:

```json
{
  "verdict": "buy | watch | pass",
  "deal_verdict": "buy | watch | pass",
  "hold_verdict": "low | medium | high",
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

## Local-Only Constraint

Do not require API keys or paid model calls. If the user wants model-backed analysis outside the current agent, suggest exporting a prompt or using another local/hosted model as an optional follow-up, not a requirement. If the current surface cannot run Chrome DevTools automation, ask for structured listing facts, saved HTML, screenshots, or manually sourced comps instead of inventing listing facts.
