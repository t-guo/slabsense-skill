# SlabSense Skill

SlabSense is a local Codex skill for analyzing PSA-graded Pokemon card listings without requiring API keys. The skill packages a collector-focused risk rubric, a deterministic analyzer, a prompt exporter, sample data, and a small eval smoke test.

## Install

From this repo:

```bash
cp -R slabsense ~/.codex/skills/slabsense
```

Restart Codex if the skill does not appear immediately.

## Use In Codex

After installing the skill, use it directly in a Codex message:

```text
slabsense https://www.ebay.com/itm/123456789012
```

Codex should then:

1. load the SlabSense skill,
2. ensure Chrome DevTools is available,
3. capture the listing with `browser_listing.js`,
4. source exact sold comps,
5. return a Buy / Watch / Pass recommendation with fair value, offer guidance, risk, confidence, and missing information.

You can also provide structured facts instead of a URL:

```text
slabsense Charizard VMAX SV107 PSA 10, ask $300, personal collection
```

SlabSense is designed to separate supplied facts from inferences and to avoid inventing PSA population data, cert details, sold prices, or condition flaws.

SlabSense now treats comp validation as a regular part of every price recommendation: exact same-card same-grade sold comps first, active asks and nearby-grade sales separated, and blocked or unavailable comp sources called out in the result.

## Local Scripts

These commands are the implementation path that Codex uses under the hood. They are useful for debugging, scripted runs, or reproducing a listing extraction outside the chat workflow.

Ensure a dedicated Chrome debugging session is available:

```bash
node slabsense/scripts/ensure_chrome.js
```

Then import listing metadata from the page Chrome renders:

```bash
node slabsense/scripts/browser_listing.js \
  "https://www.ebay.com/itm/123456789012" \
  --output listing.json
```

Then analyze the generated JSON:

```bash
python3 slabsense/scripts/analyze.py listing.json \
  --comps slabsense/assets/sample-comps.csv \
  --pretty
```

Add a screenshot only when you need manual photo, cert, seller-term, or condition review:

```bash
node slabsense/scripts/browser_listing.js \
  "https://www.ebay.com/itm/123456789012" \
  --output listing.json \
  --screenshot listing.png
```

This reads the page as Chrome renders it, captures exposed image URLs, and can save a screenshot for manual photo review. If eBay shows a captcha or marketplace error inside Chrome, log in or complete the check in that Chrome window and rerun the command.

The helper reuses `http://127.0.0.1:9222` when it is already running, otherwise it launches an isolated Chrome profile at `/tmp/slabsense-chrome`.

`fetch_listing.py` is kept for offline parsing of saved HTML or explicit debugging. It is not the normal marketplace URL path.

Preview temporary artifact cleanup:

```bash
python3 slabsense/scripts/cleanup_tmp.py
```

Delete SlabSense temp screenshots, JSON, HTML, and image files older than 24 hours:

```bash
python3 slabsense/scripts/cleanup_tmp.py --execute
```

The isolated Chrome profile is separate from screenshots. Remove it only when you want to reset Chrome session/cache state:

```bash
python3 slabsense/scripts/cleanup_tmp.py --profile --execute
```

Run the deterministic analyzer:

```bash
python3 slabsense/scripts/analyze.py \
  slabsense/assets/sample-listing.json \
  --comps slabsense/assets/sample-comps.csv \
  --pretty
```

Export a prompt you can paste into Codex or ChatGPT:

```bash
python3 slabsense/scripts/prompt.py \
  slabsense/assets/sample-listing.json \
  --comps slabsense/assets/sample-comps.csv
```

Run the smoke eval:

```bash
python3 slabsense/scripts/eval.py
```

## Repo Structure

```text
slabsense/
├── SKILL.md
├── agents/
├── scripts/
├── references/
└── assets/
```

The `slabsense/` folder is the skill package. Keep repo documentation like this README outside the skill folder.
