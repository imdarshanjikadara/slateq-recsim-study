"""Demo: one simulated user under random / oracle-myopic / learned-myopic / SlateQ (same user).

    python scripts/demo.py [--seed K] [--episode E] [--cell 10 3]

Loads the trained checkpoints (model.pt) of the RQ1 runs, replays evaluation episode E of run seed K
for every policy (common random numbers: same initial user and candidates), prints a summary and
saves results/figures/demo_user.png. Default seed: the pre-registered case-study seed. As a check,
each replayed total reward is compared with the value recorded in that run's episodes.csv: they
must be identical, which shows that checkpoints, seeding and evaluation are reproducible.
Runs in well under a minute on a laptop CPU. If checkpoints are missing it says what to run.
"""

from __future__ import annotations

from slateq_study import runtime

runtime.configure_process(threads=1)

import argparse  # noqa: E402
import csv  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import torch  # noqa: E402

from slateq_study import seeding, sweep  # noqa: E402
from slateq_study.agents import make_agent  # noqa: E402
from slateq_study.config import from_dict  # noqa: E402
from slateq_study.envs import make_env  # noqa: E402
from slateq_study.harness import run_episode  # noqa: E402
from slateq_study.io import REPO_ROOT  # noqa: E402

AGENTS = ["random", "oracle_myopic", "learned_myopic", "slateq"]
SPEC = REPO_ROOT / "configs" / "experiments" / "rq2.yaml"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=None, help="run seed (default: case-study seed)")
    ap.add_argument("--episode", type=int, default=0)
    ap.add_argument("--cell", type=int, nargs=2, default=[10, 3])
    ap.add_argument("--spec", type=Path, default=SPEC, help="sweep spec whose runs to load")
    args = ap.parse_args()

    if args.seed is None:
        summ = REPO_ROOT / "results" / "rq2" / "summary.json"
        cs = json.loads(summ.read_text("utf-8")).get("case_study_seed") if summ.exists() else None
        args.seed = cs if cs is not None else 0
    jobs = {
        j.agent: j
        for j in sweep.manifest(sweep.load_spec(args.spec))
        if j.seed == args.seed and list(j.cell) == args.cell and j.condition == "matched"
    }
    missing = [a for a in AGENTS if a not in jobs or sweep.job_status(jobs[a]) != "ok"]
    if missing:
        print(f"Checkpoints/runs missing for {missing} (seed {args.seed}, cell {args.cell}).")
        print(
            "Run the sweep first:  make sweep   (or: python scripts/sweep.py configs/experiments/rq2.yaml)"
        )
        return 1

    env_seed = seeding.env_seed("eval", args.seed, args.episode)
    results = {}
    for a in AGENTS:
        job = jobs[a]
        cfg = from_dict(job.cfg)
        rd = sweep.run_dir(job)
        space = make_env(cfg.env, env_seed).action_space
        agent = make_agent(a, space, seeding.agent_seed(args.seed), **cfg.agent.params)
        if agent.learns:
            state = torch.load(rd / "model.pt", map_location="cpu", weights_only=True)
            agent.online.load_state_dict(state["online"])
        agent.set_eval_mode(True)
        res = run_episode(agent, cfg.env, env_seed, episode=args.episode, trace=True)
        with (rd / "episodes.csv").open(encoding="utf-8") as fh:
            recorded = next(
                float(r["total_reward"])
                for r in csv.DictReader(fh)
                if int(r["env_seed"]) == env_seed
            )
        results[a] = (res, recorded)

    print(
        f"Same user (run seed {args.seed}, eval episode {args.episode}, env seed {env_seed}), "
        f"N={args.cell[0]}, k={args.cell[1]}:"
    )
    print(f"{'policy':16s} {'steps':>6s} {'clicks':>7s} {'total reward':>13s} {'recorded':>9s}")
    ok = True
    for a, (res, recorded) in results.items():
        r = res.record
        # the random policy's RNG advances across episodes: only episode 0 replays it exactly
        same = abs(r.total_reward - recorded) < 1e-9 or (a == "random" and args.episode > 0)
        ok &= same
        print(
            f"{a:16s} {r.length:6d} {r.clicks:7d} {r.total_reward:13.2f} {recorded:9.2f}"
            f"{'' if same else '  <-- MISMATCH'}"
        )

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {
        "slateq": "#2a78d6",
        "learned_myopic": "#eb6834",
        "oracle_myopic": "#1baf7a",
        "random": "#eda100",
    }
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for a, (res, _) in results.items():
        budget = [s["time_budget_after"] for s in res.trace]
        ax.plot(
            range(len(budget)),
            budget,
            color=colors[a],
            lw=2,
            label=f"{a} ({res.record.length} steps, reward {res.record.total_reward:.1f})",
        )
    ax.set_xlabel("step in session")
    ax.set_ylabel("time budget remaining")
    ax.set_title(f"Demo: one user (seed {args.seed}, episode {args.episode}) under each policy")
    ax.legend(fontsize=8, frameon=False)
    out = REPO_ROOT / "results" / "figures" / "demo_user.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"figure: {out}")
    print("replay matches the recorded evaluation" if ok else "WARNING: replay differs from record")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
