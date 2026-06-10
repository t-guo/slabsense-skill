# SlabSense Examples

## Analyze From Files

```bash
python3 scripts/analyze.py assets/sample-listing.json --comps assets/sample-comps.csv
```

## Export A Free-Chat Prompt

```bash
python3 scripts/prompt.py assets/sample-listing.json --comps assets/sample-comps.csv
```

Paste the generated prompt into Codex or ChatGPT if you want model reasoning without wiring an API into the project.

## Ask Codex Directly

```text
Use SlabSense to analyze this PSA 9 Moonbreon listing. Asking is $1,250. I have three comps: $1,050, $1,100, and $1,075. Front looks clean but back photo is missing. Investment intent.
```
