"""Run-directory convention and result files.

results/raw/<experiment>/<config_hash>/seed<k>/
    config.yaml   resolved config
    meta.json     provenance: git SHA (+dirty), uv.lock hash, versions, host, times, summary
    episodes.csv  one row per evaluation episode
    traces.jsonl  per-step traces of the first `trace_episodes` eval episodes (optional)
    run.log       log of this run
    error.json    only if the run failed
    DONE          written LAST; its presence is the only signal that a run is complete
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import shutil
import socket
import subprocess
import sys
import traceback
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

import yaml

from slateq_study.config import RunConfig
from slateq_study.metrics import EpisodeRecord

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKED_PACKAGES = ("numpy", "torch", "gymnasium", "gin-config", "absl-py", "pandas", "scipy")


class RunExistsError(RuntimeError):
    """A completed run already exists and --force was not given."""


def run_dir(results_root: Path, cfg: RunConfig, seed: int) -> Path:
    return Path(results_root) / "raw" / cfg.experiment / cfg.config_hash / f"seed{seed}"


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10, check=True
        )
        return out.stdout.strip()
    except OSError, subprocess.SubprocessError:
        return None


def provenance() -> dict:
    lock = REPO_ROOT / "uv.lock"
    versions = {}
    for pkg in TRACKED_PACKAGES:
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            versions[pkg] = None
    status = _git("status", "--porcelain")
    return {
        "git_sha": _git("rev-parse", "HEAD"),
        "git_dirty": bool(status) if status is not None else None,
        "recsim_sha": _git("-C", "third_party/recsim", "rev-parse", "HEAD"),
        "uv_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.exists() else None,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "packages": versions,
    }


class RunDir:
    def __init__(self, path: Path):
        self.path = Path(path)

    @property
    def done(self) -> bool:
        return (self.path / "DONE").exists()

    def prepare(self, force: bool = False) -> None:
        """Refuse to touch a completed run unless force. A partial run (no DONE) is cleared."""
        if self.done and not force:
            raise RunExistsError(f"completed run exists: {self.path} (use --force to overwrite)")
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True)

    def write_config(self, cfg: RunConfig, seed: int) -> None:
        with (self.path / "config.yaml").open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                {**cfg.to_dict(), "seed": seed, "config_hash": cfg.config_hash}, f, sort_keys=True
            )

    def write_meta(self, meta: dict) -> None:
        (self.path / "meta.json").write_text(json.dumps(meta, indent=2, default=str), "utf-8")

    def write_episodes(self, records: list[EpisodeRecord]) -> None:
        rows = [r.to_row() for r in records]
        with (self.path / "episodes.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    def write_traces(self, traces: list[dict]) -> None:
        """Per-step traces (JSON lines) for the first `trace_episodes` eval episodes."""
        if not traces:
            return
        with (self.path / "traces.jsonl").open("w", encoding="utf-8") as f:
            for row in traces:
                f.write(json.dumps(row, separators=(",", ":")) + "\n")

    def write_error(self, exc: BaseException) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        err = {
            "time": now(),
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exception(exc),
        }
        (self.path / "error.json").write_text(json.dumps(err, indent=2), "utf-8")

    def mark_done(self) -> None:
        (self.path / "DONE").write_text(now() + "\n", "utf-8")
