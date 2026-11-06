"""Phase 3: SlateQ sanity ladder, training-budget rule, tuning, final learning curves.

Every rule applied here is fixed in docs/PROTOCOL.md §12 BEFORE the runs. Each stage runs its jobs
(resumable) and then writes its analysis to results/phase3/<stage>.json.

    python scripts/phase3.py ladder   # checks 1-4 at (5,2), seeds 100-101   (PROTOCOL 12.7)
    python scripts/phase3.py budget   # T2 budget rule at (10,3), seeds 100-102 (12.3)
    python scripts/phase3.py tune     # T3 grid, both agents, seeds 100-101   (12.4, 12.5)
    python scripts/phase3.py final    # check 5: frozen configs, seeds 200-202 + figure
    add --analyze-only to skip running jobs.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys

import numpy as np

from slateq_study import stats
from slateq_study.jobs import RESULTS, load_run, run_jobs

OUT = RESULTS / "phase3"
TUNE_EPISODES = 500  # PROTOCOL 12.2
CURVE_EPISODES = 200
LADDER_CELL, MAIN_CELL = (5, 2), (10, 3)
LADDER_SEEDS, BUDGET_SEEDS, TUNE_SEEDS, FINAL_SEEDS = (
    [100, 101],
    [100, 101, 102],
    [100, 101],
    [
        200,
        201,
        202,
    ],
)
GRID = list(itertools.product([1e-4, 2.5e-4, 1e-3], [1000, 4000, 8000]))  # (lr, target period)


def learned_cfg(exp, agent, cell, steps, params=None, eval_every=50_000):
    return {
        "experiment": exp,
        "env": {"num_candidates": cell[0], "slate_size": cell[1]},
        "agent": {"name": agent, "params": dict(params or {})},
        "train_steps": steps,
        "eval_every": eval_every,
        "curve_episodes": CURVE_EPISODES,
        "eval_episodes": TUNE_EPISODES,
        "eval_stream": "tune",
    }


def ref_cfg(exp, agent, cell):
    return {
        "experiment": exp,
        "env": {"num_candidates": cell[0], "slate_size": cell[1]},
        "agent": {"name": agent},
        "eval_episodes": TUNE_EPISODES,
        "eval_stream": "tune",
    }


def paired(a: dict, b: dict) -> dict:
    keys = sorted(a)
    if keys != sorted(b):
        raise RuntimeError("runs were not evaluated on the same env seeds")
    return stats.paired_episode_stats([a[k] for k in keys], [b[k] for k in keys])


def must(run, what):
    if run is None:
        raise SystemExit(f"missing or failed run: {what} (see results/raw/... error.json)")
    return run


def save(name: str, obj: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=2, default=str), "utf-8")
    print(json.dumps(obj, indent=2, default=str))


# ------------------------------------------------------------------------------------- ladder
def ladder_jobs():
    jobs = []
    for s in LADDER_SEEDS:
        for a in ("slateq", "learned_myopic"):
            jobs.append((learned_cfg("p3_ladder", a, LADDER_CELL, 300_000), s))
        for a in ("random", "oracle_myopic"):
            jobs.append((ref_cfg("p3_ladder", a, LADDER_CELL), s))
    return jobs


def ladder_analyze():
    out = {"cell": LADDER_CELL, "seeds": LADDER_SEEDS, "per_seed": [], "checks": {}}
    plumbing, beats, ratios, q_lm, q_sq = [], [], [], [], []
    for s in LADDER_SEEDS:
        r = {
            a: must(load_run(ref_cfg("p3_ladder", a, LADDER_CELL), s), (a, s))
            for a in ("random", "oracle_myopic")
        }
        for a in ("slateq", "learned_myopic"):
            r[a] = must(load_run(learned_cfg("p3_ladder", a, LADDER_CELL, 300_000), s), (a, s))
        row = {"seed": s}
        for a in ("slateq", "learned_myopic"):
            m, d = r[a]["meta"], r[a]["diagnostics"]
            last = d[-1]
            finite = all(math.isfinite(x[k]) for x in d for k in x if isinstance(x[k], float))
            ok = (
                finite
                and m["training"]["replay_size"] == m["training"]["train_steps"]
                and abs(last["epsilon"] - 0.01) < 1e-9
                and m["training"]["target_syncs"] >= 1
            )
            plumbing.append(ok)
            p = paired(r[a]["rewards"], r["random"]["rewards"])
            beats.append(p["mean_diff"] > 2 * p["se_diff"])
            row[a] = {
                "vs_random": p,
                "plumbing_ok": ok,
                "final_diagnostics": last,
                "tune_reward": m["summary"]["mean_total_reward"],
            }
        po = paired(r["oracle_myopic"]["rewards"], r["random"]["rewards"])
        pl = paired(r["learned_myopic"]["rewards"], r["random"]["rewards"])
        ratios.append(pl["mean_diff"] / po["mean_diff"])
        row["oracle_vs_random"] = po
        row["learned_myopic_recovery_of_oracle_gain"] = ratios[-1]
        q_lm.append(row["learned_myopic"]["final_diagnostics"]["mean_q_clicked"])
        q_sq.append(row["slateq"]["final_diagnostics"]["mean_q_clicked"])
        out["per_seed"].append(row)
    rec = float(np.mean(ratios))
    out["checks"] = {
        "1_plumbing": all(plumbing),
        "2_beats_random": all(beats),
        "3_calibration_recovery_mean": rec,
        "3_calibration": rec >= 0.9,
        "4_q_scale_learned_myopic": q_lm,
        "4_q_scale_slateq": q_sq,
        "4_q_scale": all(2 <= q <= 6 for q in q_lm)
        and all(qs > ql and qs < 400 for qs, ql in zip(q_sq, q_lm, strict=True)),
    }
    save("ladder", out)


# ------------------------------------------------------------------------------------- budget
def budget_jobs():
    return [(learned_cfg("p3_budget", "slateq", MAIN_CELL, 500_000), s) for s in BUDGET_SEEDS]


def budget_analyze():
    d, per = [], []
    for s in BUDGET_SEEDS:
        run = must(load_run(learned_cfg("p3_budget", "slateq", MAIN_CELL, 500_000), s), s)

        # curve points are taken at the first episode boundary at/after each 50K mark
        def at(target, curves=run["curves"], s=s):
            pts = [r for r in curves if r["train_steps"] >= target]
            if not pts or pts[0]["train_steps"] - target > 1000:
                raise SystemExit(f"no curve point near {target} for seed {s}")
            return pts[0]

        p300, p500 = at(300_000), at(500_000)
        d.append(p500["mean_total_reward"] - p300["mean_total_reward"])
        per.append(
            {
                "seed": s,
                "steps_300k_point": p300["train_steps"],
                "steps_500k_point": p500["train_steps"],
                "reward_300k": p300["mean_total_reward"],
                "reward_500k": p500["mean_total_reward"],
                "diff": d[-1],
                "curve": run["curves"],
            }
        )
    mean, sd = float(np.mean(d)), float(np.std(d, ddof=1))
    threshold = 2 * sd / math.sqrt(len(d))
    budget = 500_000 if mean > threshold else 300_000
    save(
        "budget",
        {
            "rule": "500K if mean(d) > 2*SD(d)/sqrt(3) else 300K (PROTOCOL 12.3)",
            "mean_diff": mean,
            "sd_diff": sd,
            "threshold": threshold,
            "budget": budget,
            "per_seed": per,
        },
    )


def frozen_budget() -> int:
    p = OUT / "budget.json"
    if not p.exists():
        raise SystemExit("run the budget stage first")
    return json.loads(p.read_text("utf-8"))["budget"]


# ------------------------------------------------------------------------------------- tune
def tune_jobs():
    b = frozen_budget()
    jobs = []
    for agent in ("slateq", "learned_myopic"):
        for lr, period in GRID:
            params = {"learning_rate": lr, "target_update_period": period}
            for s in TUNE_SEEDS:
                jobs.append((learned_cfg("p3_tune", agent, MAIN_CELL, b, params, eval_every=0), s))
    for s in TUNE_SEEDS:
        for a in ("random", "oracle_myopic"):
            jobs.append((ref_cfg("p3_tune", a, MAIN_CELL), s))
    return jobs


def tune_analyze():
    b = frozen_budget()
    table, chosen = [], {}
    for agent in ("slateq", "learned_myopic"):
        best = None
        for lr, period in GRID:  # grid order = tie-break order
            params = {"learning_rate": lr, "target_update_period": period}
            runs = [
                must(
                    load_run(learned_cfg("p3_tune", agent, MAIN_CELL, b, params, 0), s),
                    (agent, params, s),
                )
                for s in TUNE_SEEDS
            ]
            per_seed = [r["meta"]["summary"]["mean_total_reward"] for r in runs]
            mean = float(np.mean(per_seed))
            table.append({"agent": agent, **params, "per_seed": per_seed, "mean": mean})
            if best is None or mean > best["mean"] + 0.01:
                best = {**params, "mean": mean}
        chosen[agent] = best
    # 12.5: paired SD of the two selected configs on the same tune episodes
    n_needed, sds = [], []
    for s in TUNE_SEEDS:
        rs = {
            a: load_run(
                learned_cfg(
                    "p3_tune",
                    a,
                    MAIN_CELL,
                    b,
                    {
                        "learning_rate": chosen[a]["learning_rate"],
                        "target_update_period": chosen[a]["target_update_period"],
                    },
                    0,
                ),
                s,
            )["rewards"]
            for a in chosen
        }
        p = paired(rs["slateq"], rs["learned_myopic"])
        sds.append(p["sd_diff"])
        n_needed.append(stats.episodes_for_target_se(p["sd_diff"], 0.5))
    n_max = max(n_needed)
    new_n = max(2400, int(math.ceil(n_max / 50) * 50))
    refs = {}
    for a in ("random", "oracle_myopic"):
        refs[a] = [
            must(load_run(ref_cfg("p3_tune", a, MAIN_CELL), s), (a, s))["meta"]["summary"][
                "mean_total_reward"
            ]
            for s in TUNE_SEEDS
        ]
    save(
        "tune",
        {
            "budget": b,
            "grid": table,
            "selected": chosen,
            "references": refs,
            "episode_recheck": {
                "sd_diff_per_seed": sds,
                "n_needed_per_seed": n_needed,
                "eval_episodes": new_n,
                "rule": "max(2400, ceil(max n / 50) * 50) (PROTOCOL 12.5)",
            },
        },
    )


def frozen_params() -> dict:
    p = OUT / "tune.json"
    if not p.exists():
        raise SystemExit("run the tune stage first")
    sel = json.loads(p.read_text("utf-8"))["selected"]
    return {
        a: {"learning_rate": v["learning_rate"], "target_update_period": v["target_update_period"]}
        for a, v in sel.items()
    }


# ------------------------------------------------------------------------------------- final
def final_jobs():
    b, fp = frozen_budget(), frozen_params()
    jobs = [(learned_cfg("p3_final", a, MAIN_CELL, b, fp[a]), s) for a in fp for s in FINAL_SEEDS]
    jobs += [
        (ref_cfg("p3_final", a, MAIN_CELL), s)
        for a in ("random", "oracle_myopic")
        for s in FINAL_SEEDS
    ]
    return jobs


def final_analyze():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    b, fp = frozen_budget(), frozen_params()
    curves, finals = {}, {}
    for a in fp:
        runs = [
            must(load_run(learned_cfg("p3_final", a, MAIN_CELL, b, fp[a]), s), (a, s))
            for s in FINAL_SEEDS
        ]
        steps = [c["train_steps"] for c in runs[0]["curves"]]
        mat = np.array([[c["mean_total_reward"] for c in r["curves"]] for r in runs])
        if not np.isfinite(mat).all():
            raise SystemExit(f"non-finite curve values for {a}")
        curves[a] = {
            "steps": steps,
            "per_seed": mat.tolist(),
            "mean": mat.mean(0).tolist(),
            "std": mat.std(0, ddof=1).tolist(),
        }
        finals[a] = [r["meta"]["summary"]["mean_total_reward"] for r in runs]
    refs = {}
    for a in ("random", "oracle_myopic"):
        refs[a] = [
            must(load_run(ref_cfg("p3_final", a, MAIN_CELL), s), (a, s))["meta"]["summary"][
                "mean_total_reward"
            ]
            for s in FINAL_SEEDS
        ]
    paired_sq_lm = []
    for s in FINAL_SEEDS:
        ra = load_run(learned_cfg("p3_final", "slateq", MAIN_CELL, b, fp["slateq"]), s)
        rb = load_run(
            learned_cfg("p3_final", "learned_myopic", MAIN_CELL, b, fp["learned_myopic"]), s
        )
        paired_sq_lm.append({"seed": s, **paired(ra["rewards"], rb["rewards"])})
    save(
        "final",
        {
            "budget": b,
            "params": fp,
            "seeds": FINAL_SEEDS,
            "curves": curves,
            "final_tune_reward": finals,
            "references_tune_reward": refs,
            "paired_slateq_minus_learned_myopic_tune": paired_sq_lm,
            "note": "tune stream (Phase 3); NOT the RQ1 result, which uses the eval stream",
        },
    )

    fig_dir = RESULTS / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    colours = {"slateq": "#0072B2", "learned_myopic": "#D55E00"}
    labels = {"slateq": "SlateQ (γ=0.99)", "learned_myopic": "Learned myopic (γ=0)"}
    for a, c in curves.items():
        x, m, sd = np.array(c["steps"]) / 1000, np.array(c["mean"]), np.array(c["std"])
        ax.plot(x, m, color=colours[a], label=labels[a])
        ax.fill_between(x, m - sd, m + sd, color=colours[a], alpha=0.2)
    for a, style in (("oracle_myopic", "--"), ("random", ":")):
        ax.axhline(
            np.mean(refs[a]),
            color="0.3",
            ls=style,
            label=f"{'Oracle myopic' if a == 'oracle_myopic' else 'Random'} (mean)",
        )
    ax.set_xlabel("training steps (thousands)")
    ax.set_ylabel(f"mean total reward per episode\n({CURVE_EPISODES} tune-stream episodes)")
    ax.set_title(
        f"Phase 3 learning curves, N={MAIN_CELL[0]}, k={MAIN_CELL[1]}, "
        f"seeds {FINAL_SEEDS[0]}-{FINAL_SEEDS[-1]}"
    )
    ax.legend(fontsize=8, loc="lower right")
    ax.text(
        0.01, 0.01, "band = ±1 SD over 3 seeds", transform=ax.transAxes, fontsize=7, color="0.4"
    )
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(fig_dir / f"phase3_learning_curves.{ext}", dpi=150)
    print(f"figure: {fig_dir / 'phase3_learning_curves.png'}")


STAGES = {
    "ladder": (ladder_jobs, ladder_analyze),
    "budget": (budget_jobs, budget_analyze),
    "tune": (tune_jobs, tune_analyze),
    "final": (final_jobs, final_analyze),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=sorted(STAGES))
    ap.add_argument("--analyze-only", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    jobs_fn, analyze_fn = STAGES[args.stage]
    if not args.analyze_only:
        codes = run_jobs(
            jobs_fn(),
            workers=args.workers,
            progress_file=RESULTS / "logs" / f"phase3_{args.stage}_progress.txt",
        )
        failed = sum(c not in (0, 3) for c in codes)
        print(f"{len(codes)} jobs, {failed} failed")
        if failed:
            return 1
    analyze_fn()
    return 0


if __name__ == "__main__":
    sys.exit(main())
