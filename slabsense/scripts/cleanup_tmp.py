#!/usr/bin/env python3
"""Clean SlabSense temporary listing artifacts and optional Chrome profile data."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path


DEFAULT_TMP_DIR = Path("/private/tmp")
DEFAULT_PROFILE_DIR = Path(tempfile.gettempdir()) / "slabsense-chrome"
DEFAULT_MIN_AGE_HOURS = 24
ARTIFACT_RE = re.compile(r"^slabsense-.*\.(json|png|jpg|jpeg|webp|html)$", re.I)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean SlabSense temp listing artifacts. Dry-run by default.",
    )
    parser.add_argument("--tmp-dir", type=Path, default=DEFAULT_TMP_DIR)
    parser.add_argument("--min-age-hours", type=float, default=DEFAULT_MIN_AGE_HOURS)
    parser.add_argument("--all", action="store_true", help="Match artifacts regardless of age.")
    parser.add_argument("--profile", action="store_true", help="Also remove the isolated Chrome profile.")
    parser.add_argument("--profile-dir", type=Path, default=DEFAULT_PROFILE_DIR)
    parser.add_argument("--execute", action="store_true", help="Actually delete matched paths.")
    args = parser.parse_args(argv)
    if args.min_age_hours < 0:
        parser.error("--min-age-hours must be non-negative")
    if args.all:
        args.min_age_hours = 0
    return args


def artifact_candidates(tmp_dir: Path, min_age_hours: float) -> list[Path]:
    if not tmp_dir.exists():
        return []
    cutoff = time.time() - min_age_hours * 60 * 60
    candidates: list[Path] = []
    for item in tmp_dir.iterdir():
        if not item.is_file() or not ARTIFACT_RE.match(item.name):
            continue
        if item.stat().st_mtime <= cutoff:
            candidates.append(item)
    return sorted(candidates)


def remove_path(target: Path, execute: bool) -> None:
    if execute:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)
    action = "deleted" if execute else "would delete"
    print(f"{action} {target}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    files = artifact_candidates(args.tmp_dir, args.min_age_hours)
    for file_path in files:
        remove_path(file_path, args.execute)

    profile_exists = args.profile and args.profile_dir.exists()
    if profile_exists:
        remove_path(args.profile_dir, args.execute)

    if not files and not profile_exists:
        print("No matching SlabSense temp artifacts found.")

    if not args.execute:
        print("Dry run only. Add --execute to delete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
