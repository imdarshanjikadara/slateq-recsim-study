"""Smoke test: run the random agent for 3 episodes through run_one.py in a subprocess and check
that the run directory is complete. Exits non-zero on any failure."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "configs" / "smoke.yaml"
SEED = 0


def main() -> int:
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "run_one.py"),
        "--config",
        str(CONFIG),
        "--seed",
        str(SEED),
        "--force",
    ]
    print("running:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=REPO)
    if proc.returncode != 0:
        print(f"SMOKE FAIL: run_one.py exited {proc.returncode}")
        return 1

    from slateq_study import io
    from slateq_study.config import load_config

    rd = io.run_dir(REPO / "results", load_config(CONFIG), SEED)
    required = ["config.yaml", "meta.json", "episodes.csv", "run.log", "DONE"]
    missing = [f for f in required if not (rd / f).exists()]
    if missing or (rd / "error.json").exists():
        print(f"SMOKE FAIL: missing {missing} or error.json present in {rd}")
        return 1
    with (rd / "episodes.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    meta = json.loads((rd / "meta.json").read_text("utf-8"))
    if len(rows) != 3 or meta.get("status") != "ok":
        print(
            f"SMOKE FAIL: expected 3 episodes and status ok, got {len(rows)} / {meta.get('status')}"
        )
        return 1
    print(f"SMOKE OK: {rd.relative_to(REPO)}")
    for r in rows:
        print(
            f"  episode {r['episode']}: total_reward={float(r['total_reward']):.3f} "
            f"length={r['length']} terminated={r['terminated']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
