"""Phase 6b analysis helpers (PROTOCOL 16.7): E5 click and watch-time metrics."""

from __future__ import annotations

import importlib.util
import math

from slateq_study.analysis import Run
from slateq_study.io import REPO_ROOT
from slateq_study.sweep import Job

_spec = importlib.util.spec_from_file_location(
    "phase6b_analyze", REPO_ROOT / "scripts" / "phase6b_analyze.py"
)
p6b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p6b)


def _run(tmp_path, rows):
    (tmp_path / "episodes.csv").write_text(
        "episode,env_seed,total_reward,length,clicks\n"
        + "".join(f"{i},{i},{r},{n},{c}\n" for i, (r, n, c) in enumerate(rows)),
        "utf-8",
    )
    return Run(Job({}, 0, "slateq", (10, 3), "matched"), "ok", {}, {}, tmp_path)


def test_click_metrics_are_pooled_over_episodes(tmp_path):
    # two sessions: 10 steps, 4 clicks, 16 watched; 30 steps, 6 clicks, 20 watched
    m = p6b.click_metrics(_run(tmp_path, [(16.0, 10, 4), (20.0, 30, 6)]))
    assert math.isclose(m["click_rate"], 10 / 40)  # pooled, not the mean of 0.4 and 0.2
    assert math.isclose(m["clicks_per_session"], 5.0)
    assert math.isclose(m["watch_per_click"], 36 / 10)
    assert math.isclose(m["watch_per_session"], 18.0)


def test_pattern_wording():
    assert p6b.pattern("A higher", "A lower") == "more clicks, less watch time"
    assert p6b.pattern("no clear difference", "A higher") == (
        "no clear difference in clicks, more watch time"
    )
