"""Minimal parallel job runner: each (config dict, seed) runs as its own run_one.py subprocess.

Resumable (run_one exits 3 for completed runs, which counts as ok), failure-isolated (a failed job
never stops the others), with a progress file. Phase 4 extends this into the sweep runner.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from slateq_study import io
from slateq_study.config import from_dict

RESULTS = io.REPO_ROOT / "results"
RUN_ONE = io.REPO_ROOT / "scripts" / "run_one.py"


def run_dir(cfg: dict, seed: int, results_root: Path = RESULTS) -> Path:
    return io.run_dir(results_root, from_dict(cfg), seed)


def _config_file(cfg: dict, results_root: Path) -> Path:
    c = from_dict(cfg)
    path = Path(results_root) / "raw" / c.experiment / "_configs" / f"{c.config_hash}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(cfg, sort_keys=True), "utf-8")
    return path


def run_jobs(
    jobs: list[tuple[dict, int]],
    workers: int = 3,
    results_root: Path = RESULTS,
    progress_file: Path | None = None,
) -> list[int]:
    """Run all jobs; returns exit codes in job order (0 ok, 3 already done, 1/2 failed)."""
    lock, done, t0 = threading.Lock(), [0], time.time()

    def one(job):
        cfg, seed = job
        cmd = [
            sys.executable,
            str(RUN_ONE),
            "--config",
            str(_config_file(cfg, results_root)),
            "--seed",
            str(seed),
            "--results-root",
            str(results_root),
        ]
        code = subprocess.run(cmd, cwd=io.REPO_ROOT, capture_output=True, text=True).returncode
        with lock:
            done[0] += 1
            msg = (
                f"{done[0]}/{len(jobs)} done, {time.time() - t0:.0f}s elapsed; last: "
                f"{cfg['agent']['name']} {cfg['env']} seed={seed} exit={code}"
            )
            print(msg, flush=True)
            if progress_file:
                progress_file.parent.mkdir(parents=True, exist_ok=True)
                progress_file.write_text(msg + "\n", "utf-8")
        return code

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, jobs))


def load_run(cfg: dict, seed: int, results_root: Path = RESULTS) -> dict | None:
    """Meta, per-episode rewards (by env seed), curves and diagnostics of a COMPLETED run."""
    rd = run_dir(cfg, seed, results_root)
    if not (rd / "DONE").exists():
        return None

    def rows(name):
        p = rd / name
        if not p.exists():
            return []
        with p.open(encoding="utf-8") as f:
            return [{k: _num(v) for k, v in r.items()} for r in csv.DictReader(f)]

    episodes = rows("episodes.csv")
    return {
        "dir": rd,
        "meta": json.loads((rd / "meta.json").read_text("utf-8")),
        "rewards": {int(e["env_seed"]): float(e["total_reward"]) for e in episodes},
        "curves": rows("curves.csv"),
        "diagnostics": rows("diagnostics.csv"),
    }


def _num(v: str):
    try:
        f = float(v)
    except ValueError:
        return v
    return int(f) if f.is_integer() and "." not in v and "e" not in v.lower() else f
