"""PROTOCOL S2: size the number of evaluation episodes from measured variance.

Runs random and oracle-myopic on the TUNE seed stream (never the eval stream), paired by env seed,
for each baseline cell and seed. For every (cell, seed) it records the SD of the episode-level
paired difference oracle - random and the n needed for SE <= TARGET_SE. The protocol uses the
MAXIMUM n over all cells and seeds (conservative), rounded up to a multiple of 50.

Output: results/protocol/variance_study.json
"""

from __future__ import annotations

import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from slateq_study import runtime

CELLS = [(5, 2), (10, 3), (20, 5)]
SEEDS = [0, 1, 2, 3, 4]
EPISODES = 500
TARGET_SE = 0.5  # PROTOCOL S2
OUT = Path(__file__).resolve().parents[1] / "results" / "protocol" / "variance_study.json"


def run_cell(cell: tuple[int, int]) -> list[dict]:
    runtime.configure_process(threads=1)
    from slateq_study import stats
    from slateq_study.agents import make_agent
    from slateq_study.config import EnvConfig
    from slateq_study.envs import make_env
    from slateq_study.harness import evaluate

    n, k = cell
    env_cfg = EnvConfig(num_candidates=n, slate_size=k)
    space = make_env(env_cfg, 0).action_space
    rows = []
    for seed in SEEDS:
        rew = {}
        for name in ("random", "oracle_myopic"):
            agent = make_agent(name, space, seed)
            recs, _ = evaluate(agent, env_cfg, seed, EPISODES, stream="tune")
            rew[name] = [r.total_reward for r in recs]
        p = stats.paired_episode_stats(rew["oracle_myopic"], rew["random"])
        rows.append(
            {
                "N": n,
                "k": k,
                "seed": seed,
                "stream": "tune",
                **p,
                "sd_random": float(_sd(rew["random"])),
                "sd_oracle": float(_sd(rew["oracle_myopic"])),
                "n_needed": stats.episodes_for_target_se(p["sd_diff"], TARGET_SE),
            }
        )
    return rows


def _sd(x):
    m = sum(x) / len(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))


def main() -> None:
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = [r for cell_rows in pool.map(run_cell, CELLS) for r in cell_rows]
    n_max = max(r["n_needed"] for r in rows)
    chosen = int(math.ceil(n_max / 50) * 50)
    out = {
        "target_se": TARGET_SE,
        "episodes_per_seed_measured": EPISODES,
        "cells": CELLS,
        "seeds": SEEDS,
        "rows": rows,
        "max_n_needed": n_max,
        "eval_episodes_chosen": chosen,
        "rule": "max n_needed over cells x seeds, rounded up to a multiple of 50",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), "utf-8")
    for r in rows:
        print(
            f"N={r['N']:>2} k={r['k']} seed={r['seed']} mean_diff={r['mean_diff']:6.2f} "
            f"sd_diff={r['sd_diff']:5.2f} n_needed={r['n_needed']}"
        )
    print(f"max n_needed={n_max} -> eval_episodes={chosen}")


if __name__ == "__main__":
    main()
