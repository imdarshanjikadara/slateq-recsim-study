"""Build the static presentation site's data from the committed result tables.

    python scripts/build_web.py [--rq2 results/rq2] [--rq3 results/rq3] [--out web/data]

Writes web/data/site.json (tables for the RQ1/RQ2/RQ3 views) and web/data/traces_seed<k>.json
(per-step traces of the primary cell for the "replay one user" view). The page (web/index.html)
only renders these files: every number shown on the site comes from results/ via this script.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

from slateq_study.io import REPO_ROOT


def clean(obj):
    """JSON-safe: NaN -> None, numpy scalars -> python."""
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean(v) for v in obj]
    if hasattr(obj, "item"):
        obj = obj.item()
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def table(path: Path) -> list[dict]:
    return pd.read_csv(path).to_dict("records") if path.exists() else []


def traces(d: Path, out: Path) -> list[int]:
    seeds: dict[int, dict] = {}
    for f in sorted((d / "traces").glob("matched_*_seed*.jsonl")):
        agent = f.stem[len("matched_") :].rsplit("_seed", 1)[0]
        seed = int(f.stem.rsplit("seed", 1)[1])
        df = pd.read_json(f, lines=True)
        eps = []
        for e, g in df.groupby("episode"):
            g = g.sort_values("t")
            eps.append(
                {
                    "episode": int(e),
                    "budget": [round(x, 2) for x in g.time_budget_after],
                    "reward": [round(x, 3) for x in g.reward],
                    "clicked": [int(x) for x in g.clicked_pos],
                    "clusters": [list(map(int, c)) for c in g.slate_clusters],
                    "quality": [[round(q, 2) for q in qs] for qs in g.slate_qualities],
                    "interests": [[round(u, 3) for u in us] for us in g.user_interests],
                }
            )
        seeds.setdefault(seed, {})[agent] = eps
    for seed, agents in seeds.items():
        (out / f"traces_seed{seed}.json").write_text(json.dumps(clean(agents)), "utf-8")
    return sorted(seeds)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rq2", type=Path, default=REPO_ROOT / "results" / "rq2")
    ap.add_argument("--rq3", type=Path, default=REPO_ROOT / "results" / "rq3")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "web" / "data")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    s2 = json.loads((args.rq2 / "summary.json").read_text("utf-8"))
    s3p = args.rq3 / "summary.json"
    s3 = json.loads(s3p.read_text("utf-8")) if s3p.exists() else {}
    phase3 = REPO_ROOT / "results" / "phase3"
    frozen = {
        "budget": json.loads((phase3 / "budget.json").read_text("utf-8"))["budget"],
        "selected": json.loads((phase3 / "tune.json").read_text("utf-8"))["selected"],
        "eval_episodes": json.loads((phase3 / "tune.json").read_text("utf-8"))["episode_recheck"][
            "eval_episodes"
        ],
    }
    seeds = traces(args.rq2, args.out)
    site = {
        "pilot": bool(s2.get("pilot")) or bool(s3.get("pilot")),
        "git_sha": (s2.get("provenance") or {}).get("git_sha"),
        "runs": {"rq2": s2.get("runs"), "rq3": s3.get("runs")},
        "case_study_seed": s2.get("case_study_seed"),
        "trace_seeds": seeds,
        "frozen": frozen,
        "rq2": {
            "agents": table(args.rq2 / "agents.csv"),
            "gaps": table(args.rq2 / "gaps.csv"),
            "curves": table(args.rq2 / "curves.csv"),
            "session_lengths": table(args.rq2 / "session_lengths.csv"),
        },
        "rq3": {"agents": table(args.rq3 / "agents.csv"), "gaps": table(args.rq3 / "gaps.csv")},
    }
    # Phase 6b follow-up tables (PROTOCOL 16). Data only: the current page does not show them yet;
    # they are here for the planned side-by-side feed demo.
    p6b = REPO_ROOT / "results" / "phase6b"
    if (p6b / "gaps.csv").exists():
        site["phase6b"] = {
            "agents": table(p6b / "agents.csv"),
            "gaps": table(p6b / "gaps.csv"),
            "clicks_watch": table(p6b / "clicks_watch.csv"),
            "clicks_watch_gaps": table(p6b / "clicks_watch_gaps.csv"),
        }
    (args.out / "site.json").write_text(json.dumps(clean(site)), "utf-8")
    size = sum(p.stat().st_size for p in args.out.glob("*.json")) / 1e6
    print(f"web data -> {args.out} ({size:.1f} MB; trace seeds {seeds}; pilot={site['pilot']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
