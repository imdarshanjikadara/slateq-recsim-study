"""Run or inspect a sweep defined by an experiment spec (configs/experiments/*.yaml).

    python scripts/sweep.py SPEC --dry-run           # manifest, job count, wall-clock estimate
    python scripts/sweep.py SPEC [--workers 4] [--max-hours H] [--allow-dirty] [--retry-failed]
    python scripts/sweep.py SPEC --collect           # write results/<experiment>/runs.csv only

Progress: results/logs/<experiment>_progress.txt. Per-attempt status log:
results/raw/<experiment>/_status.csv. Ctrl-C kills every child run; rerun the command to resume.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

from slateq_study import sweep
from slateq_study.sweep import RESULTS


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--max-hours", type=float, default=None, help="stop launching after H hours")
    ap.add_argument("--timeout-sec", type=float, default=None, help="per-job (default: 3x est.)")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--retry-failed", action="store_true", help="rerun jobs that wrote error.json")
    ap.add_argument("--results-root", type=Path, default=RESULTS)
    args = ap.parse_args()

    try:
        spec = sweep.load_spec(args.spec)
        jobs = sweep.manifest(spec, args.results_root)
    except (sweep.SpecError, ValueError, FileNotFoundError) as exc:
        print(f"bad spec: {exc}", file=sys.stderr)
        return 2
    exp = spec["experiment"]
    out_dir = args.results_root / exp
    timing = sweep.load_timing(args.results_root)
    est = {j.key: s for j in jobs if (s := sweep.estimate_job_sec(j, timing)) is not None}

    if args.collect:
        rows = sweep.collect(jobs, args.results_root)
        sweep.write_rows(out_dir / "runs.csv", rows)
        print(f"{out_dir / 'runs.csv'}: {dict(Counter(r['status'] for r in rows))}")
        return 0

    status = {j.key: sweep.job_status(j, args.results_root) for j in jobs}
    todo = [
        j
        for j in jobs
        if status[j.key] == "missing" or (status[j.key] == "failed" and args.retry_failed)
    ]

    if args.dry_run:
        print(f"experiment {exp}{' (PILOT)' if spec.get('pilot') else ''}: {len(jobs)} jobs")
        print(f"  status now: {dict(Counter(status.values()))}; to run: {len(todo)}")
        by = Counter((j.agent, j.cell, j.condition, j.control) for j in jobs)
        for (agent, cell, cm, control), n in sorted(by.items()):
            e = est.get(
                next(j.key for j in jobs if (j.agent, j.cell, j.condition) == (agent, cell, cm))
            )
            print(
                f"  {agent:15s} N={cell[0]:<3d} k={cell[1]}  {cm:10s}"
                f"{' control' if control else '        '}  x{n} seeds  "
                f"est {e / 60:.1f} min/job"
                if e
                else "  est n/a"
            )
        secs = [est[j.key] for j in todo if j.key in est]
        if secs:
            cpu_h = sum(secs) / 3600
            wall_h = sweep.wall_estimate(secs, args.workers) / 3600
            print(
                f"  estimate: {cpu_h:.1f} CPU-hours; ~{wall_h:.1f} h wall on {args.workers} "
                f"workers (from {'results/protocol/timing.json'}; contention not modelled)"
            )
        if len(secs) < len(todo):
            print(f"  {len(todo) - len(secs)} jobs have no timing estimate")
        return 0

    sweep.check_code_state(args.results_root / "raw" / exp, args.allow_dirty)
    for j in jobs:
        if status[j.key] == "failed" and not args.retry_failed:
            print(f"skipping failed run (use --retry-failed): {j.key}")
    print(f"{len(todo)} jobs to run on {args.workers} workers", flush=True)
    try:
        result = sweep.run_sweep(
            todo,
            args.workers,
            args.results_root,
            progress_file=args.results_root / "logs" / f"{exp}_progress.txt",
            status_file=args.results_root / "raw" / exp / "_status.csv",
            timeout_sec=args.timeout_sec,
            est=est,
            max_hours=args.max_hours,
        )
    except KeyboardInterrupt:
        return 130
    rows = sweep.collect(jobs, args.results_root)
    sweep.write_rows(out_dir / "runs.csv", rows)
    print(
        f"done: {dict(Counter(result.values()))}; runs.csv: "
        f"{dict(Counter(r['status'] for r in rows))}"
    )
    return 0 if all(s == "ok" for s in result.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
