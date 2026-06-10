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

## Use Locally

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
