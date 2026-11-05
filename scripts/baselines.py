"""Phase 2 acceptance: random vs oracle-myopic on the baseline grid (docs/PROTOCOL.md §11).

Each (agent, cell, seed) runs as its own run_one.py subprocess (3 in parallel). Completed runs are
skipped (resumable). Then every finished run is aggregated with the protocol statistics into
results/baselines/{runs.csv, summary.csv, paired.csv}.

    python scripts/baselines.py            # run missing jobs, then aggregate
    python scripts/baselines.py --aggregate-only
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from slateq_study import io, stats
from slateq_study.config import from_dict

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
OUT = RESULTS / "baselines"
CFG_DIR = RESULTS / "raw" / "baselines" / "_configs"
AGENTS = ["random", "oracle_myopic"]
CELLS = [(5, 2), (10, 3), (20, 5)]
SEEDS = [0, 1, 2, 3, 4]
EVAL_EPISODES = 2400  # PROTOCOL §6
TRACE_EPISODES = 5  # PROTOCOL §8
WORKERS = 3


def job_config(agent: str, n: int, k: int) -> dict:
    return {
        "experiment": "baselines",
        "env": {"num_candidates": n, "slate_size": k},
        "agent": {"name": agent},
        "eval_episodes": EVAL_EPISODES,
        "trace_episodes": TRACE_EPISODES,
    }


def run_job(agent: str, n: int, k: int, seed: int) -> tuple[str, int]:
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    path = CFG_DIR / f"{agent}_N{n}_k{k}.yaml"
    path.write_text(yaml.safe_dump(job_config(agent, n, k)), "utf-8")
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "run_one.py"),
        "--config",
        str(path),
        "--seed",
        str(seed),
    ]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    status = {0: "ok", 3: "ok (already done)"}.get(proc.returncode, f"FAILED ({proc.returncode})")
    print(f"{agent:>13} N={n:>2} k={k} seed={seed}: {status}", flush=True)
    return status, proc.returncode


def episodes(rd: Path) -> dict[int, float]:
    with (rd / "episodes.csv").open(encoding="utf-8") as f:
        return {int(r["env_seed"]): float(r["total_reward"]) for r in csv.DictReader(f)}


def aggregate() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    runs = []
    for agent in AGENTS:
        for n, k in CELLS:
            cfg = from_dict(job_config(agent, n, k))
            for seed in SEEDS:
                rd = io.run_dir(RESULTS, cfg, seed)
                done = (rd / "DONE").exists()
                row = {
                    "agent": agent,
                    "N": n,
                    "k": k,
                    "seed": seed,
                    "status": "ok" if done else "missing_or_failed",
                    "run_dir": str(rd),
                }
                if done:
                    meta = json.loads((rd / "meta.json").read_text("utf-8"))
                    row.update(meta["summary"])
                    row["git_sha"] = meta.get("git_sha")
                runs.append(row)
    _write_csv(OUT / "runs.csv", runs)

    summary, paired = [], []
    metrics = ["mean_total_reward", "mean_length", "mean_clicks", "mean_clicked_quality"]
    for n, k in CELLS:
        for agent in AGENTS:
            ok = [
                r
                for r in runs
                if (r["agent"], r["N"], r["k"]) == (agent, n, k) and r["status"] == "ok"
            ]
            row = {"agent": agent, "N": n, "k": k, "n_seeds": len(ok)}
            for m in metrics:
                if ok:
                    s = stats.seed_summary([r[m] for r in ok])
                    row.update(
                        {
                            f"{m}_mean": s["mean"],
                            f"{m}_std": s["std"],
                            f"{m}_ci95_low": s["ci95_low"],
                            f"{m}_ci95_high": s["ci95_high"],
                        }
                    )
            summary.append(row)
        # paired oracle - random, per seed (only seeds where both runs completed)
        per_seed, within = {}, []
        for seed in SEEDS:
            rds = {a: io.run_dir(RESULTS, from_dict(job_config(a, n, k)), seed) for a in AGENTS}
            if not all((rd / "DONE").exists() for rd in rds.values()):
                continue
            eo, er = episodes(rds["oracle_myopic"]), episodes(rds["random"])
            if set(eo) != set(er):
                raise RuntimeError(f"env seeds differ between agents for N={n} k={k} seed={seed}")
            keys = sorted(eo)
            p = stats.paired_episode_stats([eo[s] for s in keys], [er[s] for s in keys])
            per_seed[seed] = p["mean_diff"]
            within.append({"N": n, "k": k, "seed": seed, **p})
        if per_seed:
            s = stats.seed_summary(list(per_seed.values()))
            paired.append(
                {
                    "comparison": "oracle_myopic - random",
                    "N": n,
                    "k": k,
                    "n_seeds": s["n_seeds"],
                    "mean_diff": s["mean"],
                    "std_diff": s["std"],
                    "ci95_low": s["ci95_low"],
                    "ci95_high": s["ci95_high"],
                    **{f"seed{sd}_diff": v for sd, v in per_seed.items()},
                }
            )
            _write_csv(OUT / f"paired_within_seed_N{n}_k{k}.csv", within)
    _write_csv(OUT / "summary.csv", summary)
    _write_csv(OUT / "paired.csv", paired)
    print(f"wrote {OUT.relative_to(REPO)}/runs.csv, summary.csv, paired.csv")


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aggregate-only", action="store_true")
    args = ap.parse_args()
    failed = 0
    if not args.aggregate_only:
        jobs = [(a, n, k, s) for a in AGENTS for n, k in CELLS for s in SEEDS]
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            results = list(pool.map(lambda j: run_job(*j), jobs))
        failed = sum(code not in (0, 3) for _, code in results)
        print(f"jobs: {len(jobs)}, failed: {failed}")
    aggregate()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
