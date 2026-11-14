"""Phase 6b analysis (PROTOCOL 16): experiments E1-E5 -> results/phase6b/.

    python scripts/phase6b_analyze.py

Writes:
  runs.csv            one row per Phase 6b job (status explicit: ok / failed / missing)
  agents.csv          per agent or variant: across-seed mean, std and CI of every metric
  gaps.csv            E1-E4 comparisons: per-seed paired differences, mean, CI and the
                      PROTOCOL 14.6 verdict
  gaps_episodes.csv   the same comparisons, within each seed, episode by episode
  clicks_watch.csv    E5: click rate, clicks, watch time per click and per session, per agent
  clicks_watch_gaps.csv  E5: oracle-myopic - SlateQ and learned-myopic - SlateQ for each metric
  summary.json        run counts and provenance

Baseline runs (random, oracle-myopic, SlateQ, learned-myopic) are the rq2 runs of the same cell
and seeds (PROTOCOL 16.1). Every comparison below was fixed in PROTOCOL 16 before any run.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter

from slateq_study import analysis, io, stats, sweep
from slateq_study.sweep import RESULTS

SPECS = io.REPO_ROOT / "configs" / "experiments"
OUT = RESULTS / "phase6b"
CELLS = {(10, 3), (80, 3)}  # the two cells of E1 and E2

# (A, B, label, primary?) -- read as "A minus B". Names are agent or variant labels.
E1 = [
    ("slateq", "lm_lr1e-3", "E1: SlateQ - learned-myopic, both lr 1e-3", True),
    ("slateq_lr2.5e-4", "learned_myopic", "E1: SlateQ - learned-myopic, both lr 2.5e-4", True),
    ("lm_lr1e-3", "oracle_myopic", "E1: learned-myopic (lr 1e-3) - oracle-myopic", False),
]
GAMMAS = [
    ("slateq_g0.5", "0.5"),
    ("slateq_g0.9", "0.9"),
    ("slateq_g0.95", "0.95"),
    ("slateq", "0.99"),
]
E2 = [(a, "lm_lr1e-3", f"E2: gamma {g} - gamma 0 (lr 1e-3)", False) for a, g in GAMMAS]
E2 += [(a, "oracle_myopic", f"E2: gamma {g} - oracle-myopic", False) for a, g in GAMMAS]
E3 = [
    ("slateq_2x", "lm_2x", "E3: SlateQ - learned-myopic, both 600K steps", True),
    ("lm_2x", "oracle_myopic", "E3: learned-myopic (600K) - oracle-myopic", False),
    ("slateq_2x", "oracle_myopic", "E3: SlateQ (600K) - oracle-myopic", False),
    ("lm_2x", "learned_myopic", "E3: learned-myopic 600K - 300K", False),
    ("slateq_2x", "slateq", "E3: SlateQ 600K - 300K", False),
]
E4 = [(a, b, "E4: " + label, primary) for a, b, label, primary in analysis.COMPARISONS]

# E5: which agent is compared with SlateQ, on which metric
E5_PAIRS = [
    ("oracle_myopic", "oracle-myopic - SlateQ"),
    ("learned_myopic", "learned-myopic - SlateQ"),
]
E5_METRICS = ("click_rate", "clicks_per_session", "watch_per_click", "watch_per_session")


def load_spec_runs(name: str) -> list[analysis.Run]:
    spec = sweep.load_spec(SPECS / f"{name}.yaml")
    return analysis.load(sweep.manifest(spec, RESULTS), RESULTS)


# ---------------------------------------------------------------------------------- E5 helpers
def click_metrics(run: analysis.Run) -> dict:
    """Pooled over the run's evaluation episodes (PROTOCOL 16.7)."""
    clicks = steps = reward = n = 0
    with (run.dir / "episodes.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            clicks += int(row["clicks"])
            steps += int(row["length"])
            reward += float(row["total_reward"])
            n += 1
    return {
        "click_rate": clicks / steps,
        "clicks_per_session": clicks / n,
        "watch_per_click": reward / clicks if clicks else float("nan"),
        "watch_per_session": reward / n,
    }


def e5_tables(runs: list[analysis.Run]) -> tuple[list[dict], list[dict]]:
    # (condition, cell, control) -> agent -> seed -> metrics
    groups: dict[tuple, dict[str, dict[int, dict]]] = {}
    for r in runs:
        if r.status != "ok" or r.job.variant:
            continue
        key = (r.job.condition, r.job.cell, r.job.control)
        groups.setdefault(key, {}).setdefault(r.job.agent, {})[r.job.seed] = click_metrics(r)

    agent_rows, gap_rows = [], []
    for (cond, cell, control), agents in sorted(groups.items()):
        base = {
            "condition": cond,
            "num_candidates": cell[0],
            "slate_size": cell[1],
            "control": control,
        }
        for agent, by_seed in sorted(agents.items()):
            row = {**base, "agent": agent, "n_seeds": len(by_seed)}
            for m in E5_METRICS:
                s = stats.seed_summary([by_seed[k][m] for k in sorted(by_seed)])
                row[m], row[f"{m}_ci95_low"], row[f"{m}_ci95_high"] = (
                    s["mean"],
                    s["ci95_low"],
                    s["ci95_high"],
                )
            agent_rows.append(row)
        if "slateq" not in agents:
            continue
        for other, label in E5_PAIRS:
            if other not in agents:
                continue
            seeds = sorted(set(agents[other]) & set(agents["slateq"]))
            row = {**base, "comparison": label, "n_seeds": len(seeds)}
            for m in E5_METRICS:
                diffs = [agents[other][k][m] - agents["slateq"][k][m] for k in seeds]
                s = stats.seed_summary(diffs)
                row[f"{m}_diff"] = s["mean"]
                row[f"{m}_ci95_low"], row[f"{m}_ci95_high"] = s["ci95_low"], s["ci95_high"]
                row[f"{m}_verdict"] = analysis.verdict(diffs, s["ci95_low"], s["ci95_high"])
                for k, d in zip(seeds, diffs, strict=True):
                    row[f"{m}_seed{k}"] = d
            row["pattern"] = pattern(row["click_rate_verdict"], row["watch_per_session_verdict"])
            gap_rows.append(row)
    return agent_rows, gap_rows


def pattern(click_verdict: str, watch_verdict: str) -> str:
    """Plain-language class of a cell for E5 (PROTOCOL 16.7). "A" is the myopic agent."""
    words = {
        "A higher": "more",
        "A lower": "fewer",
        "no clear difference": "no clear difference in",
    }
    watch = {"A higher": "more", "A lower": "less", "no clear difference": "no clear difference in"}
    clicks = words.get(click_verdict, click_verdict)
    watched = watch.get(watch_verdict, watch_verdict)
    return f"{clicks} clicks, {watched} watch time"


# ------------------------------------------------------------------------------------------ main
def main() -> int:
    rq2 = load_spec_runs("rq2")
    rq3 = load_spec_runs("rq3")
    p6b = load_spec_runs("phase6b")
    budget = load_spec_runs("phase6b_budget")
    cascade = load_spec_runs("phase6b_cascade")
    new_runs = p6b + budget + cascade

    baselines = [r for r in rq2 if r.job.cell in CELLS and r.job.condition == "matched"]
    gaps, ep = analysis.gap_tables(baselines + p6b + budget, E1 + E2 + E3)
    gaps4, ep4 = analysis.gap_tables(cascade, E4)

    OUT.mkdir(parents=True, exist_ok=True)
    analysis.write_csv(OUT / "runs.csv", sweep.collect([r.job for r in new_runs], RESULTS))
    analysis.write_csv(OUT / "agents.csv", analysis.agent_table(baselines + new_runs))
    analysis.write_csv(OUT / "gaps.csv", gaps + gaps4)
    analysis.write_csv(OUT / "gaps_episodes.csv", ep + ep4)
    e5_agents, e5_gaps = e5_tables(rq2 + rq3 + cascade)
    analysis.write_csv(OUT / "clicks_watch.csv", e5_agents)
    analysis.write_csv(OUT / "clicks_watch_gaps.csv", e5_gaps)

    status = Counter(r.status for r in new_runs)
    summary = {"runs": dict(status), "n_gap_rows": len(gaps + gaps4), "provenance": io.provenance()}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str), "utf-8")
    print(
        f"phase6b: runs {dict(status)}; {len(gaps + gaps4)} gap rows; "
        f"{len(e5_gaps)} E5 rows -> {OUT}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
