#!/usr/bin/env python3
"""Tests for SlabSense temp cleanup."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cleanup_tmp.py"


def run_cleanup(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        text=True,
        capture_output=True,
    )


class CleanupTmpTest(unittest.TestCase):
    def test_cleanup_dry_run_and_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            target = tmp_dir / "slabsense-listing-123.json"
            keep_name = tmp_dir / "other-listing.json"
            keep_ext = tmp_dir / "slabsense-listing-123.txt"
            target.write_text("{}", encoding="utf-8")
            keep_name.write_text("{}", encoding="utf-8")
            keep_ext.write_text("keep", encoding="utf-8")

            dry_run = run_cleanup("--tmp-dir", str(tmp_dir), "--all")
            self.assertEqual(dry_run.returncode, 0)
            self.assertIn(f"would delete {target}", dry_run.stdout)
            self.assertTrue(target.exists())
            self.assertTrue(keep_name.exists())
            self.assertTrue(keep_ext.exists())

            executed = run_cleanup("--tmp-dir", str(tmp_dir), "--all", "--execute")
            self.assertEqual(executed.returncode, 0)
            self.assertIn(f"deleted {target}", executed.stdout)
            self.assertFalse(target.exists())
            self.assertTrue(keep_name.exists())
            self.assertTrue(keep_ext.exists())

    def test_execute_default_keeps_current_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            current = tmp_dir / "slabsense-listing-current.json"
            stale = tmp_dir / "slabsense-listing-stale.json"
            current.write_text("{}", encoding="utf-8")
            stale.write_text("{}", encoding="utf-8")
            old_time = time.time() - 25 * 60 * 60
            os.utime(stale, (old_time, old_time))

            executed = run_cleanup("--tmp-dir", str(tmp_dir), "--execute")
            self.assertEqual(executed.returncode, 0)
            self.assertIn(f"deleted {stale}", executed.stdout)
            self.assertTrue(current.exists())
            self.assertFalse(stale.exists())

    def test_cleanup_profile_is_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            profile_dir = tmp_dir / "slabsense-chrome"
            profile_dir.mkdir()
            (profile_dir / "cache-file").write_text("cache", encoding="utf-8")

            without_profile = run_cleanup("--tmp-dir", str(tmp_dir), "--all", "--execute")
            self.assertEqual(without_profile.returncode, 0)
            self.assertTrue(profile_dir.exists())

            with_profile = run_cleanup(
                "--tmp-dir",
                str(tmp_dir),
                "--profile-dir",
                str(profile_dir),
                "--profile",
                "--execute",
            )
            self.assertEqual(with_profile.returncode, 0)
            self.assertIn(f"deleted {profile_dir}", with_profile.stdout)
            self.assertFalse(profile_dir.exists())


if __name__ == "__main__":
    unittest.main()
