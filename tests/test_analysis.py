"""Known-answer tests for the Phase 6 analysis rules (PROTOCOL 14.3-14.6) on synthetic runs."""

from __future__ import annotations

from pathlib import Path

import pytest

from slateq_study import analysis
from slateq_study.sweep import Job


def run(agent, seed, mean, cell=(10, 3), cond="matched", n=4, status="ok"):
    rewards = {1000 + i: mean + (0.5 if i % 2 else -0.5) for i in range(n)}
    job = Job({}, seed, agent, cell, cond)
    summary = {m: 0.0 for m in analysis.METRICS} | {"mean_total_reward": mean}
    if status != "ok":
        return analysis.Run(job, status, None, None, Path("."))
    return analysis.Run(job, "ok", summary, rewards, Path("."))


def test_verdict_rule():
    assert analysis.verdict([1, 2, 3], 0.5, 2.5) == "A higher"
    assert analysis.verdict([-1, -2, -3], -2.5, -0.5) == "A lower"
    assert analysis.verdict([1, -0.1, 3], 0.1, 2.5) == "no clear difference"  # signs disagree
    assert analysis.verdict([1, 2, 3], -0.1, 2.5) == "no clear difference"  # CI includes 0
    assert analysis.verdict([1, 2], 0.5, 1.5) == "insufficient seeds"


def test_gap_table_paired_differences_and_primary():
    runs = [run("slateq", s, 170 + s) for s in range(5)]
    runs += [run("learned_myopic", s, 168 + s) for s in range(5)]
    gaps, ep = analysis.gap_tables(runs)
    (g,) = [r for r in gaps if r["comparison"] == "SlateQ - learned-myopic"]
    assert g["primary"] and g["n_seeds"] == 5
    assert g["mean_diff"] == pytest.approx(2.0)
    assert all(g[f"diff_seed{s}"] == pytest.approx(2.0) for s in range(5))
    assert g["verdict"] == "A higher"
    assert len(ep) == 5 and all(e["mean_diff"] == pytest.approx(2.0) for e in ep)


def test_missing_and_failed_runs_are_not_imputed():
    runs = [run("slateq", s, 170) for s in range(5)]
    runs += [run("learned_myopic", s, 168) for s in range(3)]
    runs += [
        run("learned_myopic", 3, 0, status="failed"),
        run("learned_myopic", 4, 0, status="missing"),
    ]
    gaps, _ = analysis.gap_tables(runs)
    (g,) = [r for r in gaps if r["comparison"] == "SlateQ - learned-myopic"]
    assert g["n_seeds"] == 3 and g["seeds"] == "0 1 2"


def test_different_eval_seeds_are_refused():
    a, b = run("slateq", 0, 170), run("learned_myopic", 0, 168)
    b.rewards = {k + 1: v for k, v in b.rewards.items()}
    with pytest.raises(RuntimeError):
        analysis.gap_tables([a, b])


def test_case_study_seed_is_the_median_gap_seed():
    diffs = {0: 3.0, 1: -1.0, 2: 0.5, 3: 2.0, 4: 1.0}  # median 1.0 -> seed 4
    runs = [run("slateq", s, 170 + d) for s, d in diffs.items()]
    runs += [run("learned_myopic", s, 170) for s in diffs]
    gaps, _ = analysis.gap_tables(runs)
    assert analysis.case_study_seed(gaps) == 4
