"""Phase 6: turn completed sweep runs into committed result tables (PROTOCOL §14, §15).

    python scripts/analyze.py                       # rq2 + rq3 -> results/rq2/, results/rq3/
    python scripts/analyze.py --spec SPEC [--rq3-spec SPEC3] --out DIR   # e.g. a pilot

Partial sweeps are fine: missing runs appear as missing in runs.csv, and every aggregate states
its number of seeds. RQ3's matched rung is the RQ2 primary cell (10, 3), reused (PROTOCOL 15.2).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from slateq_study import analysis, io, sweep
from slateq_study.sweep import RESULTS

SPECS = io.REPO_ROOT / "configs" / "experiments"


def analyse(name: str, runs: list[analysis.Run], out: Path, pilot: bool) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    jobs = [r.job for r in runs]
    analysis.write_csv(out / "runs.csv", sweep.collect(jobs, RESULTS_ROOT))
    agents = analysis.agent_table(runs)
    gaps, ep = analysis.gap_tables(runs)
    analysis.write_csv(out / "agents.csv", agents)
    analysis.write_csv(out / "gaps.csv", gaps)
    analysis.write_csv(out / "gaps_episodes.csv", ep)
    curves = analysis.curves_table(runs)
    if curves:
        analysis.write_csv(out / "curves.csv", curves)
    traces = analysis.export_traces(runs, out / "traces")
    analysis.export_session_lengths(runs, out / "session_lengths.csv")
    status = Counter(r.status for r in runs)
    summary = {
        "experiment": name,
        "pilot": pilot,
        "runs": dict(status),
        "case_study_seed": analysis.case_study_seed(gaps),
        "primary": [g for g in gaps if g["primary"]],
        "traces_exported": len(traces),
        "provenance": io.provenance(),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str), "utf-8")
    print(f"{name}: runs {dict(status)}; {len(gaps)} gap rows -> {out}")
    return summary


def main() -> int:
    global RESULTS_ROOT
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", type=Path, default=SPECS / "rq2.yaml")
    ap.add_argument("--rq3-spec", type=Path, default=SPECS / "rq3.yaml")
    ap.add_argument("--no-rq3", action="store_true", help="skip the RQ3 analysis")
    ap.add_argument("--out", type=Path, default=None, help="default: results/<experiment>")
    ap.add_argument("--results-root", type=Path, default=RESULTS)
    args = ap.parse_args()
    RESULTS_ROOT = args.results_root

    spec = sweep.load_spec(args.spec)
    main_runs = analysis.load(sweep.manifest(spec, RESULTS_ROOT), RESULTS_ROOT)
    out = args.out or RESULTS_ROOT / spec["experiment"]
    analyse(spec["experiment"], main_runs, out, bool(spec.get("pilot")))

    if not args.no_rq3 and args.rq3_spec.is_file():
        spec3 = sweep.load_spec(args.rq3_spec)
        rq3_runs = analysis.load(sweep.manifest(spec3, RESULTS_ROOT), RESULTS_ROOT)
        matched = [
            r
            for r in main_runs
            if r.job.cell == analysis.PRIMARY_CELL and r.job.condition == "matched"
        ]
        out3 = (args.out / "rq3") if args.out else RESULTS_ROOT / spec3["experiment"]
        analyse(spec3["experiment"], matched + rq3_runs, out3, bool(spec3.get("pilot")))
    return 0


RESULTS_ROOT = RESULTS

if __name__ == "__main__":
    sys.exit(main())
