"""run_one.py end to end, in subprocesses, against a temporary results root."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from slateq_study import io
from slateq_study.config import from_dict

REPO = Path(__file__).resolve().parents[1]
RUN_ONE = REPO / "scripts" / "run_one.py"


def _write_cfg(tmp_path: Path, agent: str = "random", **extra) -> Path:
    data = {
        "experiment": "t",
        "env": {"num_candidates": 5, "slate_size": 2},
        "agent": {"name": agent},
        "eval_episodes": 2,
        **extra,
    }
    p = tmp_path / f"{agent}.yaml"
    p.write_text(yaml.safe_dump(data), "utf-8")
    return p


def _run(cfg_path: Path, root: Path, *extra: str) -> int:
    cmd = [
        sys.executable,
        str(RUN_ONE),
        "--config",
        str(cfg_path),
        "--seed",
        "0",
        "--results-root",
        str(root),
        *extra,
    ]
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True).returncode


def _rundir(cfg_path: Path, root: Path) -> Path:
    return io.run_dir(root, from_dict(yaml.safe_load(cfg_path.read_text("utf-8"))), 0)


def test_complete_run_and_no_silent_overwrite(tmp_path):
    cfg = _write_cfg(tmp_path)
    root = tmp_path / "results"
    assert _run(cfg, root) == 0
    rd = _rundir(cfg, root)
    for f in ("config.yaml", "meta.json", "episodes.csv", "run.log", "DONE"):
        assert (rd / f).exists(), f
    meta = json.loads((rd / "meta.json").read_text("utf-8"))
    assert meta["status"] == "ok" and meta["summary"]["episodes"] == 2
    assert meta["git_sha"] and meta["uv_lock_sha256"]
    first_done = (rd / "DONE").read_text("utf-8")
    assert _run(cfg, root) == 3  # refuses without --force
    assert (rd / "DONE").read_text("utf-8") == first_done
    assert _run(cfg, root, "--force") == 0


def test_failure_writes_error_json_and_no_done(tmp_path):
    cfg = _write_cfg(tmp_path, agent="_failing_for_tests")
    root = tmp_path / "results"
    assert _run(cfg, root) == 1
    rd = _rundir(cfg, root)
    assert (rd / "error.json").exists() and not (rd / "DONE").exists()
    assert json.loads((rd / "meta.json").read_text("utf-8"))["status"] == "failed"


def test_partial_run_is_not_treated_as_complete(tmp_path):
    cfg = _write_cfg(tmp_path)
    root = tmp_path / "results"
    rd = _rundir(cfg, root)
    rd.mkdir(parents=True)
    (rd / "episodes.csv").write_text("half-written", "utf-8")  # crashed run, no DONE
    assert _run(cfg, root) == 0  # re-run proceeds without --force
    assert (rd / "DONE").exists()


def test_invalid_config_exit_code(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        yaml.safe_dump({"experiment": "t", "env": {"num_candidates": 3, "slate_size": 4}}), "utf-8"
    )
    assert _run(bad, tmp_path / "results") == 2


def test_degenerate_flag_in_meta(tmp_path):
    cfg = tmp_path / "degen.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {"experiment": "t", "env": {"num_candidates": 3, "slate_size": 3}, "eval_episodes": 1}
        ),
        "utf-8",
    )
    root = tmp_path / "results"
    assert _run(cfg, root) == 0
    assert json.loads((_rundir(cfg, root) / "meta.json").read_text("utf-8"))["degenerate"] is True
