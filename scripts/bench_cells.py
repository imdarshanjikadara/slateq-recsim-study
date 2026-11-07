"""Measure per-cell throughput for sweep wall-clock estimates (Phase 4 dry run).

For each (N, k): SlateQ with the frozen Phase 3 config trains 20K warm-up steps (no updates), then
is timed for 10K steps WITH updates; then 50 eval episodes are timed for SlateQ and for random.
Each cell runs in its own subprocess, `--workers` at a time, to mimic sweep contention. Uses the
train stream (and seed 900, outside every reserved range) so no eval/tune data is touched.

    python scripts/bench_cells.py [--workers 4] -> results/protocol/timing.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from slateq_study import io

CELLS = [(n, k) for n in (5, 10, 20, 40, 80) for k in (2, 3, 5) if k <= n]
BENCH_SEED = 900
OUT = io.REPO_ROOT / "results" / "protocol" / "timing.json"


def one_cell(n: int, k: int) -> dict:
    from slateq_study import runtime

    runtime.configure_process(threads=1)
    from slateq_study import seeding
    from slateq_study.agents import make_agent
    from slateq_study.config import EnvConfig
    from slateq_study.envs import make_env
    from slateq_study.harness import evaluate, train

    tune = json.loads((io.REPO_ROOT / "results" / "phase3" / "tune.json").read_text("utf-8"))
    params = {
        key: tune["selected"]["slateq"][key] for key in ("learning_rate", "target_update_period")
    }
    env_cfg = EnvConfig(num_candidates=n, slate_size=k)
    space = make_env(env_cfg, seeding.env_seed("train", BENCH_SEED, 0)).action_space
    seeding.seed_torch(seeding.agent_seed(BENCH_SEED))
    agent = make_agent("slateq", space, seeding.agent_seed(BENCH_SEED), **params)
    train(agent, env_cfg, BENCH_SEED, 20_000)
    t = time.perf_counter()
    train(agent, env_cfg, BENCH_SEED, 10_000)
    sec_per_step = (time.perf_counter() - t) / 10_000
    out = {"num_candidates": n, "slate_size": k, "train_sec_per_step": sec_per_step}
    for name, ag in (("slateq", agent), ("random", make_agent("random", space, 1))):
        t = time.perf_counter()
        evaluate(ag, env_cfg, BENCH_SEED, 50, stream="train", quiet=True)
        out[f"eval_sec_per_episode_{name}"] = (time.perf_counter() - t) / 50
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--cell", nargs=2, type=int, help=argparse.SUPPRESS)  # child mode
    args = ap.parse_args()
    if args.cell:
        print(json.dumps(one_cell(*args.cell)))
        return 0

    def run(cell):
        cmd = [sys.executable, __file__, "--cell", str(cell[0]), str(cell[1])]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=io.REPO_ROOT)
        if res.returncode != 0:
            return {"num_candidates": cell[0], "slate_size": cell[1], "error": res.stderr[-500:]}
        return json.loads(res.stdout.strip().splitlines()[-1])

    t0 = time.time()
    with ThreadPoolExecutor(args.workers) as pool:
        rows = list(pool.map(run, CELLS))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "workers": args.workers,
                "bench_seed": BENCH_SEED,
                "wall_clock_sec": time.time() - t0,
                "provenance": io.provenance(),
                "cells": rows,
            },
            indent=2,
        ),
        "utf-8",
    )
    for r in rows:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
