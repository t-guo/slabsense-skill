# SlabSense

SlabSense is a portable agent skill for evaluating PSA-graded Pokemon card listings. It is designed for Codex, Claude, and other local agents that can read a skill folder and run bundled scripts. It turns a listing URL or structured card facts into a collector-facing Buy / Watch / Pass recommendation with comps, fair value, offer guidance, downside, liquidity, investability, regret risk, confidence, red flags, and missing information.

Fair value is comp-anchored but not blindly limited to the last few sales. When a card has sourced low population and strong chase demand, the analyzer can include a scarcity premium in the fair-value range.

It does not require API keys. The agent provides the reasoning layer; the bundled scripts handle listing capture, deterministic scoring, prompt export, temp cleanup, and smoke evals.

## Install

### Codex

Install the skill from this repo:

```bash
cp -R slabsense ~/.codex/skills/slabsense
```

Restart Codex if the skill does not appear immediately.

### Claude

Claude Skills are also folder-style bundles of instructions, scripts, and resources. Package or import the `slabsense/` folder as a Claude Skill according to the Claude surface you use.

Runtime support matters:

- Claude Code or another local Claude agent with shell access can use the bundled Python and Node scripts.
- Hosted Claude surfaces may not allow local Chrome DevTools automation. In that case, provide structured listing facts, saved HTML, screenshots, or manually sourced comps instead of relying on `browser_listing.js`.

## Use In An Agent

Use the skill directly in an agent message:

```text
slabsense https://www.ebay.com/itm/123456789012
```

You can also provide structured facts instead of a URL:

```text
slabsense Charizard VMAX SV107 PSA 10, ask $300, personal collection
```

SlabSense should:

1. load the skill instructions,
2. capture marketplace URLs with Chrome-backed browsing,
3. normalize the listing title into canonical card identity fields,
4. source exact same-card same-grade sold comps,
5. source PSA population data when available and cite the source,
6. separate sold comps from active asks and nearby-grade context,
7. return a concise Buy / Watch / Pass recommendation.

SlabSense must not invent PSA population data, cert facts, sold prices, seller terms, or condition flaws. Missing facts should be labeled as missing information and reduce confidence.

## Workflow

Marketplace URLs are browser-first. Plain HTTP fetching is not the normal path because eBay and similar marketplaces often return bot checks, generic error pages, or incomplete metadata.

For URL listings, a local agent should use:

```bash
python3 slabsense/scripts/cleanup_tmp.py --execute
node slabsense/scripts/ensure_chrome.js
node slabsense/scripts/browser_listing.js "<listing-url>" --output listing.json
```

Screenshots are opt-in and should be used only when the recommendation depends on visual evidence:

```bash
node slabsense/scripts/browser_listing.js "<listing-url>" \
  --output listing.json \
  --screenshot listing.png
```

The cleanup step deletes only matching `/private/tmp/slabsense-*` artifacts older than 24 hours. It does not delete the current run, and it does not delete the isolated Chrome profile. The isolated Chrome profile lives at `/tmp/slabsense-chrome`. Screenshots, listing JSON, saved HTML, and extracted image files are separate temp artifacts, usually under `/private/tmp/slabsense-*`.

## Local Scripts

These scripts are useful for debugging or scripted runs outside the chat workflow.

Analyze structured listing data:

```bash
python3 slabsense/scripts/analyze.py listing.json \
  --comps slabsense/assets/sample-comps.csv \
  --format text
```

Use `--format json` for machine-readable output or `--format both` when you want readable text plus the full JSON payload.

Parse PriceCharting price or population pages:

```bash
python3 slabsense/scripts/pricecharting.py \
  --set "EX Dragon Frontiers" \
  --card-title "Charizard Gold Star" \
  --card-number 100 \
  --grade 3
```

Parse saved marketplace HTML for debugging:

```bash
python3 slabsense/scripts/parse_saved_listing.py saved-listing.html \
  --url "https://www.ebay.com/itm/123456789012" \
  --output listing.json \
  --pretty
```

Preview temp cleanup:

```bash
python3 slabsense/scripts/cleanup_tmp.py
```

Delete SlabSense temp screenshots, JSON, HTML, and image files older than 24 hours:

```bash
python3 slabsense/scripts/cleanup_tmp.py --execute
```

Remove the isolated Chrome profile only when you want to reset Chrome session/cache state:

```bash
python3 slabsense/scripts/cleanup_tmp.py --profile --execute
```

Export a prompt you can paste into an agent chat:

```bash
python3 slabsense/scripts/prompt.py \
  slabsense/assets/sample-listing.json \
  --comps slabsense/assets/sample-comps.csv
```

Run the smoke eval:

```bash
python3 slabsense/scripts/eval.py
```

Run the focused unit tests:

```bash
python3 -m unittest discover -s slabsense/tests
```

## Repo Structure

```text
slabsense/
├── SKILL.md
├── agents/
├── assets/
├── references/
├── scripts/
└── tests/
```

The `slabsense/` folder is the skill package. Keep repo documentation like this README outside the skill folder.
