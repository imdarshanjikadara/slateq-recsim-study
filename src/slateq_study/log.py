"""Structured logging to a run's log file and the console."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_FMT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(log_file: Path | None = None, level: int = logging.INFO) -> logging.Logger:
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)
        h.close()
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(logging.Formatter(_FMT))
    root.addHandler(console)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(_FMT))
        root.addHandler(fh)
    logging.getLogger("absl").setLevel(logging.WARNING)  # RecSim logs every slate at DEBUG
    return logging.getLogger("slateq_study")
