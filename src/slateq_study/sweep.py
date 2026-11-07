"""Sweep runner (Phase 4): experiment spec -> job manifest -> resumable parallel subprocess runs.

A spec (configs/experiments/*.yaml) names cells, seeds, agents and the env's true choice-model
`conditions` (RQ3; default: matched). Training budget, learned-agent hyperparameters and
eval_episodes are NOT in the spec: they are read from the frozen Phase 3 outputs
(results/phase3/budget.json, tune.json; PROTOCOL 12.6), so no frozen number is typed twice. A spec
may override train_steps / eval_episodes only when it is marked `pilot: true` (plumbing checks such
as the mini-sweep); pilot results are never used for analysis.

Each job is one `scripts/run_one.py` subprocess (one thread). The runner is resumable (completed
runs exit 3 and count as done), failure-isolated, enforces a per-job timeout, retries a job at most
once and only for infrastructure crashes (never for a run that failed cleanly, e.g. NaN loss),
stops launching new jobs past a wall-clock budget, writes a live progress file, and kills all
children on Ctrl-C. (A hard kill of the runner process itself does not reach the children on
Windows; resume is still safe because run_one clears partial run directories.)
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from slateq_study import io
from slateq_study.config import CHOICE_MODELS, from_dict

RESULTS = io.REPO_ROOT / "results"
RUN_ONE = io.REPO_ROOT / "scripts" / "run_one.py"
LEARNED = ("slateq", "learned_myopic")
SPEC_KEYS = {
    "experiment",
    "description",
    "grid",
    "controls",
    "seeds",
    "agents",
    "conditions",
    "trace_episodes",
    "curves",
    "pilot",
    "train_steps",
    "eval_episodes",
    "frozen_from",
}
OK_EXIT = (0, 3)  # completed now / already completed
CLEAN_FAIL_EXIT = (1, 2)  # run failed and wrote error.json / bad config: never retried


class SpecError(ValueError):
    pass


@dataclass(frozen=True)
class Job:
    cfg: dict
    seed: int
    agent: str
    cell: tuple[int, int]
    condition: str  # name of the env's true choice-model condition (RQ3); "matched" otherwise
    control: bool = False  # degenerate k == N control cell (excluded from the main analysis)
    key: str = field(default="", compare=False)

    @property
    def learned(self) -> bool:
        return self.agent in LEARNED


# ------------------------------------------------------------------------------------- spec
def load_spec(path: Path) -> dict:
    spec = yaml.safe_load(Path(path).read_text("utf-8"))
    if not isinstance(spec, dict):
        raise SpecError(f"{path}: not a mapping")
    unknown = set(spec) - SPEC_KEYS
    if unknown:
        raise SpecError(f"{path}: unknown keys {sorted(unknown)}")
    for req in ("experiment", "grid", "seeds", "agents"):
        if req not in spec:
            raise SpecError(f"{path}: missing {req!r}")
    from slateq_study.agents import AGENTS

    bad = [a for a in spec["agents"] if a not in AGENTS]
    if bad:
        raise SpecError(f"unknown agents {bad}")
    names = [c.get("name") for c in conditions(spec)]
    if len(set(names)) != len(names) or not all(names):
        raise SpecError("conditions need unique names")
    for c in conditions(spec):
        if set(c) - {"name", "choice_model", "no_click_mass"}:
            raise SpecError(f"unknown condition keys in {c}")
        if c["choice_model"] not in CHOICE_MODELS:
            raise SpecError(f"unknown choice model {c['choice_model']!r}")
    if not spec.get("pilot") and ("train_steps" in spec or "eval_episodes" in spec):
        raise SpecError(
            "train_steps / eval_episodes come from the frozen Phase 3 files; "
            "overrides are allowed only in a spec marked pilot: true"
        )
    if not spec.get("pilot") and set(spec["seeds"]) - {0, 1, 2, 3, 4}:
        raise SpecError("non-pilot sweeps use the reserved final run seeds 0-4 (PROTOCOL 3)")
    return spec


def frozen(results_root: Path = RESULTS, frozen_from: str = "phase3") -> dict:
    """Budget, selected hyperparameters and eval_episodes fixed by Phase 3 (PROTOCOL 12.6)."""
    d = Path(results_root) / frozen_from
    budget = json.loads((d / "budget.json").read_text("utf-8"))
    tune = json.loads((d / "tune.json").read_text("utf-8"))
    params = {
        a: {k: v[k] for k in ("learning_rate", "target_update_period")}
        for a, v in tune["selected"].items()
    }
    return {
        "train_steps": int(budget["budget"]),
        "params": params,
        "eval_episodes": int(tune["episode_recheck"]["eval_episodes"]),
    }


MATCHED = {"name": "matched", "choice_model": "multinomial_proportional", "no_click_mass": 1.0}


def conditions(spec: dict) -> list[dict]:
    """The env's TRUE choice-model conditions (RQ3); default: the matched RecSim setting."""
    out = []
    for c in spec.get("conditions") or [MATCHED]:
        c = {**MATCHED, **c}
        c["no_click_mass"] = float(c["no_click_mass"])
        out.append(c)
    return out


def cells(spec: dict) -> list[tuple[tuple[int, int], bool]]:
    """(cell, is_control) for the grid (k < N only) plus explicit controls."""
    g = spec["grid"]
    out = [((n, k), False) for n in g["num_candidates"] for k in g["slate_size"] if k < n]
    out += [((int(n), int(k)), True) for n, k in spec.get("controls", [])]
    return out


def manifest(spec: dict, results_root: Path = RESULTS) -> list[Job]:
    """Jobs ordered seed-major (a partial sweep holds complete seeds), long jobs first in a seed."""
    fz = frozen(results_root, spec.get("frozen_from", "phase3"))
    steps = int(spec.get("train_steps", fz["train_steps"]))
    n_eval = int(spec.get("eval_episodes", fz["eval_episodes"]))
    curves = spec.get("curves") or {}
    curve_cells = {tuple(c) for c in curves.get("cells", [])}
    jobs = []
    for seed in spec["seeds"]:
        for cond in conditions(spec):
            per_seed = []
            for (n, k), control in cells(spec):
                for agent in spec["agents"]:
                    env = {"num_candidates": n, "slate_size": k}
                    for key in ("choice_model", "no_click_mass"):  # defaults left implicit
                        if cond[key] != MATCHED[key]:
                            env[key] = cond[key]
                    cfg = {
                        "experiment": spec["experiment"],
                        "env": env,
                        "agent": {"name": agent},
                        "eval_episodes": n_eval,
                        "trace_episodes": int(spec.get("trace_episodes", 0)),
                    }
                    if agent in LEARNED:
                        cfg["agent"]["params"] = dict(fz["params"][agent])
                        cfg["train_steps"] = steps
                        if (n, k) in curve_cells:
                            cfg["eval_every"] = int(curves["eval_every"])
                            cfg["curve_episodes"] = int(curves["curve_episodes"])
                    from_dict(cfg)  # validate now, not in a subprocess hours later
                    name = cond["name"]
                    per_seed.append(
                        Job(
                            cfg,
                            int(seed),
                            agent,
                            (n, k),
                            name,
                            control,
                            key=f"{agent}|N{n}k{k}|{name}|seed{seed}",
                        )
                    )
            per_seed.sort(key=lambda j: (not j.learned, -j.cell[0], -j.cell[1]))
            jobs += per_seed
    keys = [j.key for j in jobs]
    if len(set(keys)) != len(keys):
        raise SpecError("duplicate jobs in manifest")
    return jobs


# --------------------------------------------------------------------------------- estimates
def estimate_job_sec(job: Job, timing: dict | None) -> float | None:
    if not timing:
        return None
    row = next(
        (
            r
            for r in timing["cells"]
            if (r.get("num_candidates"), r.get("slate_size")) == job.cell and "error" not in r
        ),
        None,
    )
    if row is None:
        return None
    sec = 0.0
    if job.learned:
        sec += job.cfg["train_steps"] * row["train_sec_per_step"]
        sec += job.cfg["eval_episodes"] * row["eval_sec_per_episode_slateq"]
        if job.cfg.get("eval_every"):
            points = job.cfg["train_steps"] // job.cfg["eval_every"] + 1
            sec += points * job.cfg["curve_episodes"] * row["eval_sec_per_episode_slateq"]
    else:
        sec += job.cfg["eval_episodes"] * row["eval_sec_per_episode_random"]
    return sec


def load_timing(results_root: Path = RESULTS) -> dict | None:
    p = Path(results_root) / "protocol" / "timing.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def wall_estimate(secs: list[float], workers: int) -> float:
    """Greedy longest-first list scheduling on `workers` slots (what the pool roughly does)."""
    slots = [0.0] * max(1, workers)
    for s in sorted(secs, reverse=True):
        i = slots.index(min(slots))
        slots[i] += s
    return max(slots)


# ------------------------------------------------------------------------------------- runner
def run_dir(job: Job, results_root: Path = RESULTS) -> Path:
    return io.run_dir(results_root, from_dict(job.cfg), job.seed)


def job_status(job: Job, results_root: Path = RESULTS) -> str:
    rd = run_dir(job, results_root)
    if (rd / "DONE").exists():
        return "ok"
    if (rd / "error.json").exists():
        return "failed"
    return "missing"


def _config_file(job: Job, results_root: Path) -> Path:
    c = from_dict(job.cfg)
    p = Path(results_root) / "raw" / c.experiment / "_configs" / f"{c.config_hash}.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(job.cfg, sort_keys=True), "utf-8")
    return p


def check_code_state(exp_dir: Path, allow_dirty: bool) -> dict:
    """Refuse to (re)launch on a dirty tree or a different commit than the sweep started with."""
    prov = io.provenance()
    state_file = exp_dir / "_sweep.json"
    if prov["git_dirty"] and not allow_dirty:
        raise SystemExit("working tree has uncommitted changes; commit first or pass --allow-dirty")
    if state_file.exists():
        prev = json.loads(state_file.read_text("utf-8"))
        if prev.get("git_sha") != prov["git_sha"] and not allow_dirty:
            raise SystemExit(
                f"sweep started at commit {prev.get('git_sha')}, code is now at {prov['git_sha']}; "
                "refusing to mix code versions (pass --allow-dirty to override)"
            )
    else:
        exp_dir.mkdir(parents=True, exist_ok=True)
        state_file.write_text(
            json.dumps(
                {"git_sha": prov["git_sha"], "git_dirty": prov["git_dirty"], "started": io.now()},
                indent=2,
            ),
            "utf-8",
        )
    return prov


def run_sweep(
    jobs: list[Job],
    workers: int,
    results_root: Path = RESULTS,
    progress_file: Path | None = None,
    status_file: Path | None = None,
    timeout_sec: float | None = None,
    est: dict[str, float] | None = None,
    max_hours: float | None = None,
) -> dict[str, str]:
    """Run jobs; returns key -> status (ok / failed / timeout / crashed / not_started)."""
    lock = threading.Lock()
    live: set[subprocess.Popen] = set()
    stop = threading.Event()
    t0 = time.time()
    status: dict[str, str] = {}
    done_sec: list[float] = []
    est = est or {}

    def record(job, st, sec, code, attempt):
        with lock:
            status[job.key] = st
            done_sec.append(sec)
            n = len(status)
            remaining = [est.get(j.key) for j in jobs if j.key not in status]
            rem_known = sum(x for x in remaining if x)
            eta = rem_known / max(1, workers)
            n_ok = sum(s == "ok" for s in status.values())
            msg = (
                f"{n}/{len(jobs)} finished ({n_ok} ok), {(time.time() - t0) / 3600:.2f} h "
                f"elapsed, ETA ~{eta / 3600:.1f} h; last: {job.key} -> {st} ({sec:.0f}s, "
                f"exit {code}, attempt {attempt})"
            )
            print(msg, flush=True)
            if progress_file:
                progress_file.parent.mkdir(parents=True, exist_ok=True)
                progress_file.write_text(msg + "\n", "utf-8")
            if status_file:
                new = not status_file.exists()
                with status_file.open("a", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    if new:
                        w.writerow(["time", "key", "status", "exit", "attempt", "sec"])
                    w.writerow([io.now(), job.key, st, code, attempt, round(sec, 1)])

    def one(job: Job) -> None:
        if stop.is_set() or (max_hours and time.time() - t0 > max_hours * 3600):
            with lock:
                status[job.key] = "not_started"
            return
        cfg_path = _config_file(job, results_root)
        limit = timeout_sec or max(1800.0, 3 * est.get(job.key, 3600.0))
        for attempt in (1, 2):
            cmd = [
                sys.executable,
                str(RUN_ONE),
                "--config",
                str(cfg_path),
                "--seed",
                str(job.seed),
                "--results-root",
                str(results_root),
            ]
            ts = time.time()
            proc = subprocess.Popen(
                cmd, cwd=io.REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            with lock:
                live.add(proc)
            try:
                code = proc.wait(timeout=limit)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                record(job, "timeout", time.time() - ts, None, attempt)
                return
            finally:
                with lock:
                    live.discard(proc)
            if stop.is_set():
                with lock:
                    status[job.key] = "interrupted"
                return
            if code in OK_EXIT:
                record(job, "ok", time.time() - ts, code, attempt)
                return
            if code in CLEAN_FAIL_EXIT:
                record(job, "failed", time.time() - ts, code, attempt)
                return
            if attempt == 2:  # infrastructure crash twice
                record(job, "crashed", time.time() - ts, code, attempt)
                return
            # run_one clears a partial run directory itself (RunDir.prepare)
            print(f"infrastructure crash (exit {code}) for {job.key}; retrying once", flush=True)

    pool = ThreadPoolExecutor(max_workers=max(1, workers))
    try:
        futures = [pool.submit(one, j) for j in jobs]
        while any(not f.done() for f in futures):
            time.sleep(0.5)
        for f in futures:
            f.result()
    except KeyboardInterrupt:
        stop.set()
        with lock:
            for p in list(live):
                p.kill()
        pool.shutdown(wait=True, cancel_futures=True)
        print("interrupted: all child runs killed; rerun the same command to resume", flush=True)
        raise
    pool.shutdown(wait=True)
    return status


# ------------------------------------------------------------------------------------ collect
def collect(jobs: list[Job], results_root: Path = RESULTS) -> list[dict]:
    """One row per job (runs.csv): status, timings, metrics. Missing/failed rows stay explicit."""
    rows = []
    for j in jobs:
        rd = run_dir(j, results_root)
        st = job_status(j, results_root)
        row = {
            "agent": j.agent,
            "num_candidates": j.cell[0],
            "slate_size": j.cell[1],
            "condition": j.condition,
            "choice_model": from_dict(j.cfg).env.choice_model,
            "no_click_mass": from_dict(j.cfg).env.no_click_mass,
            "seed": j.seed,
            "control": j.control,
            "config_hash": from_dict(j.cfg).config_hash,
            "status": st,
        }
        if st == "ok":
            meta = json.loads((rd / "meta.json").read_text("utf-8"))
            row.update(
                git_sha=meta.get("git_sha"),
                wall_clock_sec=round(meta.get("wall_clock_sec", math.nan), 1),
                train_wall_clock_sec=round(meta.get("train_wall_clock_sec", 0.0), 1),
                **{k: v for k, v in meta["summary"].items()},
            )
        elif st == "failed":
            err = json.loads((rd / "error.json").read_text("utf-8"))
            row["error"] = str(err.get("type", "")) + ": " + str(err.get("message", ""))[:200]
        rows.append(row)
    return rows


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols: list[str] = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
