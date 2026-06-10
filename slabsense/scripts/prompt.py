#!/usr/bin/env python3
"""Export a SlabSense prompt for Codex/ChatGPT without API calls."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_listing(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_comps(path: Path | None) -> list[dict]:
    if not path:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a pasteable SlabSense analysis prompt.")
    parser.add_argument("listing", type=Path)
    parser.add_argument("--comps", type=Path)
    args = parser.parse_args()

    listing = load_listing(args.listing)
    comps = load_comps(args.comps)

    prompt = {
        "role": "You are SlabSense, an AI TCG deal copilot for PSA-graded Pokemon cards.",
        "rules": [
            "Do not invent PSA population data, cert facts, sold prices, seller terms, or condition flaws.",
            "Separate supplied facts from inferences.",
            "Use cautious condition language when photos are weak.",
            "Check exact same-card same-grade sold comps when possible, separate active asks and nearby-grade comps, and label comp source confidence.",
            "Return Buy, Watch, or Pass with fair value, suggested offer, downside, liquidity, regret risk, confidence, red flags, missing info, and collector summary.",
        ],
        "listing": listing,
        "comps": comps,
    }

    print("Analyze this slab deal using the SlabSense rules:\n")
    print(json.dumps(prompt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
