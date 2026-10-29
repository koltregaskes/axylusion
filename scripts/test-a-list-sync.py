"""Regression: the legacy hub-cache sync must not overwrite a current arena snapshot.

Reproduces the PR #88 review finding: with a *fresh* shared cache, sync-a-list-benchmarks.py
used to rebuild the legacy snapshot over the Artificial Analysis capture (Elo 1222 replaced by
composite score 78), and arena validation then failed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYNC = ROOT / "scripts" / "sync-a-list-benchmarks.py"
SNAPSHOT = ROOT / "data" / "a-list-benchmarks.json"


def run_sync(source: Path, output: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SYNC), "--source", str(source), "--output", str(output), *extra],
        capture_output=True,
        text=True,
    )


def main() -> int:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if snapshot.get("score_basis") != "artificial_analysis_elo":
        print("SKIP: committed snapshot is not an arena capture; nothing to protect.")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "a-list-benchmarks.json"
        shutil.copyfile(SNAPSHOT, output)
        before = output.read_bytes()

        # A fresh legacy cache row, stamped now, so the stale-cache branch is not taken.
        fresh_cache = tmp_path / "creative_benchmarks.json"
        now = datetime.now(timezone.utc).isoformat()
        fresh_cache.write_text(
            json.dumps([{"category": "image", "model": "Legacy Model", "score": 78, "updated_at": now}]),
            encoding="utf-8",
        )

        failures = []
        for mode in ((), ("--check",)):
            result = run_sync(fresh_cache, output, *mode)
            label = "check" if mode else "write"
            if result.returncode != 0:
                failures.append(f"{label}: exit {result.returncode}: {result.stdout.strip()} {result.stderr.strip()}")
            if output.read_bytes() != before:
                failures.append(f"{label}: arena snapshot was modified")

        after = json.loads(output.read_text(encoding="utf-8"))
        if after.get("score_basis") != "artificial_analysis_elo":
            failures.append("score_basis is no longer artificial_analysis_elo")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("PASS: fresh legacy cache leaves the current arena snapshot untouched (write and --check).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
