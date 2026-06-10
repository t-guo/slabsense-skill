# SlabSense Skill

SlabSense is a local Codex skill for analyzing PSA-graded Pokemon card listings without requiring API keys. The skill packages a collector-focused risk rubric, a deterministic analyzer, a prompt exporter, sample data, and a small eval smoke test.

## Install

From this repo:

```bash
cp -R slabsense ~/.codex/skills/slabsense
```

Restart Codex if the skill does not appear immediately.

## Use In Codex

Ask Codex:

```text
Use SlabSense to analyze this PSA card listing.
```

Provide the card name, grade, asking price, listing notes, image observations, buyer intent, and any comps you have. SlabSense is designed to separate supplied facts from inferences and to avoid inventing PSA population data, cert details, sold prices, or condition flaws.

SlabSense now treats comp validation as a regular part of every price recommendation: exact same-card same-grade sold comps first, active asks and nearby-grade sales separated, and blocked or unavailable comp sources called out in the result.

## Use Locally

Start a dedicated Chrome debugging session once:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/slabsense-chrome
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

`fetch_listing.py` is kept for offline parsing of saved HTML or explicit debugging. It is not the normal marketplace URL path.

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
