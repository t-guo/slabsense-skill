#!/usr/bin/env python3
"""Minimal SlabSense eval runner."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_case() -> dict:
    output = subprocess.check_output(
        [
            sys.executable,
            str(ROOT / "scripts" / "analyze.py"),
            str(ROOT / "assets" / "sample-listing.json"),
            "--comps",
            str(ROOT / "assets" / "sample-comps.csv"),
        ],
        text=True,
    )
    return json.loads(output)


def main() -> int:
    result = run_case()
    checks = {
        "verdict_is_watch_or_pass": result["verdict"] in {"watch", "pass"},
        "mentions_photo_or_condition_risk": any(
            "condition" in flag or "photo" in flag for flag in result["red_flags"]
        ),
        "has_missing_info": bool(result["missing_info"]),
        "has_offer_price": result["suggested_offer"] > 0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({"checks": checks, "result": result}, indent=2))
    if failed:
        print(f"Failed checks: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
