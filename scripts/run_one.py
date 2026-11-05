"""Run ONE (config, seed) into ONE run directory. Designed to be launched as a subprocess.

Exit codes: 0 = completed (DONE written); 1 = run failed (error.json written);
            2 = invalid config / arguments; 3 = completed run already exists (no --force).

    python scripts/run_one.py --config configs/smoke.yaml --seed 0
        [--results-root results] [--force]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from slateq_study import runtime

runtime.configure_process(threads=1)  # before anything else touches torch / recsim

from slateq_study import io, metrics, seeding  # noqa: E402
from slateq_study.agents import make_agent  # noqa: E402
from slateq_study.config import ConfigError, load_config  # noqa: E402
from slateq_study.envs import make_env  # noqa: E402
from slateq_study.harness import evaluate  # noqa: E402
from slateq_study.log import setup_logging  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--results-root", type=Path, default=io.REPO_ROOT / "results")
    p.add_argument("--force", action="store_true", help="overwrite a completed run")
    args = p.parse_args(argv)

    try:
        cfg = load_config(args.config)
        seeding.env_seed("eval", args.seed, 0)  # validates the seed range
    except (ConfigError, ValueError, OSError) as exc:
        setup_logging().error("invalid config or seed: %s", exc)
        return 2

    rd = io.RunDir(io.run_dir(args.results_root, cfg, args.seed))
    try:
        rd.prepare(force=args.force)
    except io.RunExistsError as exc:
        setup_logging().error("%s", exc)
        return 3

    log = setup_logging(rd.path / "run.log")
    meta = {
        "config_hash": cfg.config_hash,
        "seed": args.seed,
        "degenerate": cfg.env.degenerate,
        "start_time": io.now(),
        **io.provenance(),
    }
    if cfg.env.degenerate:
        log.warning("degenerate cell: slate_size == num_candidates (no selection problem)")
    t0 = time.perf_counter()
    try:
        rd.write_config(cfg, args.seed)
        seeding.seed_torch(seeding.agent_seed(args.seed))
        probe_env = make_env(cfg.env, seeding.env_seed("eval", args.seed, 0))
        agent = make_agent(
            cfg.agent.name,
            probe_env.action_space,
            seeding.agent_seed(args.seed),
            **cfg.agent.params,
        )
        meta["privileged_agent"] = agent.privileged
        if cfg.train_steps:
            raise NotImplementedError("training arrives in Phase 3")
        records, traces = evaluate(
            agent, cfg.env, args.seed, cfg.eval_episodes, trace_episodes=cfg.trace_episodes
        )
        rd.write_episodes(records)
        rd.write_traces(traces)
        meta.update(
            summary=metrics.summarize(records),
            end_time=io.now(),
            wall_clock_sec=time.perf_counter() - t0,
            status="ok",
        )
        rd.write_meta(meta)
        rd.mark_done()  # LAST
        log.info("run complete: %s", rd.path)
        return 0
    except Exception as exc:  # noqa: BLE001  one failed run must never kill a sweep
        log.exception("run failed")
        meta.update(end_time=io.now(), wall_clock_sec=time.perf_counter() - t0, status="failed")
        rd.write_meta(meta)
        rd.write_error(exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
