"""Phase 6 analysis: sweep runs -> small, committed result tables (PROTOCOL §7, §14, §15).

Reads completed runs from results/raw (via the sweep manifest) and writes, per experiment:
  runs.csv            one row per job, status explicit (ok / failed / missing)
  agents.csv          per (condition, cell, agent): across-seed mean/std/CI of every metric
  gaps.csv            per (condition, cell, comparison): per-seed paired differences, mean, std,
                      seed-bootstrap CI, sign consistency, verdict (PROTOCOL 14.6)
  gaps_episodes.csv   per (condition, cell, comparison, seed): within-seed episode-paired mean +- SE
  curves.csv          learning curves (tune stream) where recorded
  traces/             per-step traces of the primary cell (all agents, all seeds) for figures/web
Nothing here is tuned or chosen after looking: comparisons and rules are those of PROTOCOL §14.
"""

from __future__ import annotations

import csv
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from slateq_study import stats, sweep
from slateq_study.sweep import RESULTS, Job

PRIMARY_CELL = (10, 3)
METRICS = (
    "mean_total_reward",
    "mean_length",
    "mean_clicks",
    "mean_clicked_quality",
    "mean_reward_per_step",
    "truncated_episodes",
    "duplicate_slates",
)
# (A, B, label, primary?) -- PROTOCOL 14.3: primary = SlateQ - learned-myopic; the rest secondary
COMPARISONS = (
    ("slateq", "learned_myopic", "SlateQ - learned-myopic", True),
    ("slateq", "oracle_myopic", "SlateQ - oracle-myopic", False),
    ("slateq", "random", "SlateQ - random", False),
    ("learned_myopic", "oracle_myopic", "learned-myopic - oracle-myopic", False),
    ("oracle_myopic", "random", "oracle-myopic - random", False),
)
MIN_SEEDS = 3  # PROTOCOL 3: never fewer than 3 seeds for an aggregate


@dataclass
class Run:
    job: Job
    status: str
    summary: dict | None
    rewards: dict[int, float] | None  # eval env seed -> total reward
    dir: Path


def load(jobs: list[Job], results_root: Path = RESULTS) -> list[Run]:
    out = []
    for j in jobs:
        rd = sweep.run_dir(j, results_root)
        st = sweep.job_status(j, results_root)
        summary = rewards = None
        if st == "ok":
            summary = json.loads((rd / "meta.json").read_text("utf-8"))["summary"]
            with (rd / "episodes.csv").open(encoding="utf-8") as f:
                rewards = {int(r["env_seed"]): float(r["total_reward"]) for r in csv.DictReader(f)}
        out.append(Run(j, st, summary, rewards, rd))
    return out


def _groups(runs: list[Run]) -> dict[tuple, dict[str, dict[int, Run]]]:
    """(condition, cell, control) -> agent -> seed -> run (ok runs only)."""
    g: dict[tuple, dict[str, dict[int, Run]]] = {}
    for r in runs:
        key = (r.job.condition, r.job.cell, r.job.control)
        g.setdefault(key, {}).setdefault(r.job.agent, {})
        if r.status == "ok":
            g[key][r.job.agent][r.job.seed] = r
    return g


def agent_table(runs: list[Run]) -> list[dict]:
    rows = []
    for (cond, cell, control), agents in sorted(_groups(runs).items()):
        for agent, by_seed in sorted(agents.items()):
            row = {
                "condition": cond,
                "num_candidates": cell[0],
                "slate_size": cell[1],
                "control": control,
                "agent": agent,
                "n_seeds": len(by_seed),
                "seeds": " ".join(map(str, sorted(by_seed))),
            }
            for m in METRICS:
                vals = [by_seed[s].summary[m] for s in sorted(by_seed)]
                vals = [v for v in vals if v is not None and not math.isnan(v)]
                if len(vals) >= 1:
                    s = stats.seed_summary(vals)
                    row.update(
                        {
                            f"{m}": s["mean"],
                            f"{m}_std": s["std"],
                            f"{m}_ci95_low": s["ci95_low"],
                            f"{m}_ci95_high": s["ci95_high"],
                        }
                    )
                for seed in sorted(by_seed):
                    row[f"{m}_seed{seed}"] = by_seed[seed].summary[m]
            rows.append(row)
    return rows


def verdict(per_seed: list[float], lo: float, hi: float) -> str:
    """PROTOCOL 14.6, worded for the report."""
    if len(per_seed) < MIN_SEEDS:
        return "insufficient seeds"
    same_sign = all(d > 0 for d in per_seed) or all(d < 0 for d in per_seed)
    if lo > 0 and same_sign:
        return "A higher"
    if hi < 0 and same_sign:
        return "A lower"
    return "no clear difference"


def gap_tables(runs: list[Run]) -> tuple[list[dict], list[dict]]:
    rows, ep_rows = [], []
    for (cond, cell, control), agents in sorted(_groups(runs).items()):
        for a, b, label, primary in COMPARISONS:
            if a not in agents or b not in agents:
                continue
            seeds = sorted(set(agents[a]) & set(agents[b]))
            row = {
                "condition": cond,
                "num_candidates": cell[0],
                "slate_size": cell[1],
                "control": control,
                "comparison": label,
                "agent_a": a,
                "agent_b": b,
                "primary": primary,
                "n_seeds": len(seeds),
                "seeds": " ".join(map(str, seeds)),
            }
            diffs = []
            for s in seeds:
                ra, rb = agents[a][s], agents[b][s]
                if sorted(ra.rewards) != sorted(rb.rewards):
                    raise RuntimeError(f"{label} seed {s}: runs used different eval env seeds")
                keys = sorted(ra.rewards)
                ep = stats.paired_episode_stats(
                    [ra.rewards[k] for k in keys], [rb.rewards[k] for k in keys]
                )
                ep_rows.append(
                    {
                        **{
                            k: row[k]
                            for k in (
                                "condition",
                                "num_candidates",
                                "slate_size",
                                "control",
                                "comparison",
                                "primary",
                            )
                        },
                        "seed": s,
                        **ep,
                    }
                )
                d = ra.summary["mean_total_reward"] - rb.summary["mean_total_reward"]
                diffs.append(d)
                row[f"diff_seed{s}"] = d
            if diffs:
                sm = stats.seed_summary(diffs)
                row.update(
                    mean_diff=sm["mean"],
                    std_diff=sm["std"],
                    ci95_low=sm["ci95_low"],
                    ci95_high=sm["ci95_high"],
                    relative_to_b=sm["mean"]
                    / np.mean([agents[b][s].summary["mean_total_reward"] for s in seeds]),
                    verdict=verdict(diffs, sm["ci95_low"], sm["ci95_high"]),
                )
            else:
                row["verdict"] = "missing"
            rows.append(row)
    return rows, ep_rows


def curves_table(runs: list[Run]) -> list[dict]:
    rows = []
    for r in runs:
        p = r.dir / "curves.csv"
        if r.status != "ok" or not p.exists():
            continue
        with p.open(encoding="utf-8") as f:
            for c in csv.DictReader(f):
                rows.append(
                    {
                        "condition": r.job.condition,
                        "num_candidates": r.job.cell[0],
                        "slate_size": r.job.cell[1],
                        "agent": r.job.agent,
                        "seed": r.job.seed,
                        **c,
                    }
                )
    return rows


def export_traces(runs: list[Run], out_dir: Path, cell=PRIMARY_CELL) -> list[str]:
    """Copy traces of the given cell (every agent and seed) into a committed folder."""
    done = []
    for r in runs:
        src = r.dir / "traces.jsonl"
        if r.status == "ok" and r.job.cell == cell and src.exists():
            dst = out_dir / f"{r.job.condition}_{r.job.agent}_seed{r.job.seed}.jsonl"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            done.append(dst.name)
    return done


def export_session_lengths(runs: list[Run], path: Path, cell=PRIMARY_CELL) -> int:
    """Exact counts of eval-episode lengths for one cell, per (condition, agent, seed).
    Compact enough to commit; the session-length distribution figure is built from it."""
    counts: dict[tuple, int] = {}
    for r in runs:
        p = r.dir / "episodes.csv"
        if r.status != "ok" or r.job.cell != cell or not p.exists():
            continue
        with p.open(encoding="utf-8") as f:
            for e in csv.DictReader(f):
                k = (r.job.condition, r.job.agent, r.job.seed, int(e["length"]))
                counts[k] = counts.get(k, 0) + 1
    rows = [
        {"condition": c, "agent": a, "seed": s, "length": n, "episodes": v}
        for (c, a, s, n), v in sorted(counts.items())
    ]
    if rows:
        write_csv(path, rows)
    return len(rows)


def case_study_seed(gap_rows: list[dict], condition: str = "matched") -> int | None:
    """PROTOCOL 14.5: the seed whose primary RQ1 gap is the median of the seeds."""
    row = next(
        (
            g
            for g in gap_rows
            if g["primary"]
            and g["condition"] == condition
            and (g["num_candidates"], g["slate_size"]) == PRIMARY_CELL
        ),
        None,
    )
    if not row or row.get("n_seeds", 0) == 0:
        return None
    per = {int(k[len("diff_seed") :]): v for k, v in row.items() if k.startswith("diff_seed")}
    order = sorted(per, key=lambda s: (per[s], s))
    return order[(len(order) - 1) // 2]  # lower median for an even count


def write_csv(path: Path, rows: list[dict]) -> None:
    sweep.write_rows(path, rows)
