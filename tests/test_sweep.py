from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from slateq_study import sweep
from slateq_study.config import from_dict
from slateq_study.io import REPO_ROOT

SPECS = REPO_ROOT / "configs" / "experiments"


def _frozen_root(tmp_path: Path) -> Path:
    """A results root holding copies of the frozen Phase 3 files."""
    root = tmp_path / "results"
    (root / "phase3").mkdir(parents=True)
    for f in ("budget.json", "tune.json"):
        shutil.copy(REPO_ROOT / "results" / "phase3" / f, root / "phase3" / f)
    return root


def _spec(tmp_path: Path, **over) -> Path:
    spec = {
        "experiment": "t_sweep",
        "pilot": True,
        "grid": {"num_candidates": [5], "slate_size": [2]},
        "seeds": [950, 951],
        "agents": ["random", "_failing_for_tests"] if over.pop("failing", False) else ["random"],
        "eval_episodes": 2,
        **over,
    }
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(spec), "utf-8")
    return p


def test_rq2_manifest_uses_frozen_phase3_values():
    spec = sweep.load_spec(SPECS / "rq2.yaml")
    jobs = sweep.manifest(spec)
    fz = sweep.frozen()
    tune = json.loads((REPO_ROOT / "results/phase3/tune.json").read_text("utf-8"))
    learned = [j for j in jobs if j.learned]
    assert learned and all(j.cfg["train_steps"] == fz["train_steps"] for j in learned)
    for j in learned:
        sel = tune["selected"][j.agent]
        assert j.cfg["agent"]["params"]["learning_rate"] == sel["learning_rate"]
        assert j.cfg["agent"]["params"]["target_update_period"] == sel["target_update_period"]
    assert all(j.cfg["eval_episodes"] == fz["eval_episodes"] for j in jobs)
    # only k < N in the grid; the degenerate control is flagged
    assert all(j.cell[1] < j.cell[0] for j in jobs if not j.control)
    assert {j.cell for j in jobs if j.control} == {(5, 5)}
    # seed-major ordering: a partial sweep holds complete seeds
    seeds = [j.seed for j in jobs]
    assert seeds == sorted(seeds)
    # curves only for the primary cell
    assert {j.cell for j in learned if j.cfg.get("eval_every")} == {(10, 3)}
    assert len({j.key for j in jobs}) == len(jobs)


def test_non_pilot_spec_cannot_override_frozen_values(tmp_path):
    p = tmp_path / "s.yaml"
    grid = {"num_candidates": [5], "slate_size": [2]}
    spec = {"experiment": "x", "grid": grid, "seeds": [0], "agents": ["slateq"], "train_steps": 10}
    p.write_text(yaml.safe_dump(spec))
    with pytest.raises(sweep.SpecError):
        sweep.load_spec(p)


def test_non_pilot_spec_must_use_final_seeds(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(
        yaml.safe_dump(
            {
                "experiment": "x",
                "grid": {"num_candidates": [5], "slate_size": [2]},
                "seeds": [100],
                "agents": ["random"],
            }
        )
    )
    with pytest.raises(sweep.SpecError):
        sweep.load_spec(p)


def test_default_choice_model_keeps_hash_and_other_models_change_it(tmp_path):
    root = _frozen_root(tmp_path)
    a = sweep.manifest(sweep.load_spec(_spec(tmp_path)), root)
    b = sweep.manifest(
        sweep.load_spec(
            _spec(tmp_path, conditions=[{"name": "mnl", "choice_model": "multinomial_logit"}])
        ),
        root,
    )
    assert "choice_model" not in a[0].cfg["env"]
    assert from_dict(a[0].cfg).config_hash != from_dict(b[0].cfg).config_hash


def test_runner_end_to_end_resume_and_failure_isolation(tmp_path):
    root = _frozen_root(tmp_path)
    spec = sweep.load_spec(_spec(tmp_path, failing=True))
    jobs = sweep.manifest(spec, root)
    status = sweep.run_sweep(
        jobs, workers=2, results_root=root, status_file=root / "raw" / "t_sweep" / "_status.csv"
    )
    by_agent = {j.key: j.agent for j in jobs}
    assert all(s == "ok" for k, s in status.items() if by_agent[k] == "random")
    assert all(s == "failed" for k, s in status.items() if by_agent[k] != "random")  # no retry
    rows = sweep.collect(jobs, root)
    assert sorted(r["status"] for r in rows) == ["failed", "failed", "ok", "ok"]
    # resume: completed runs are not redone (run_one exits 3 -> ok, DONE untouched)
    ok_job = next(j for j in jobs if j.agent == "random")
    done = sweep.run_dir(ok_job, root) / "DONE"
    stamp = done.read_text()
    again = sweep.run_sweep([ok_job], workers=1, results_root=root)
    assert again[ok_job.key] == "ok" and done.read_text() == stamp
    # same job, same eval env seeds; different run seeds -> different env seeds
    eps = {
        j.seed: (sweep.run_dir(j, root) / "episodes.csv").read_text()
        for j in jobs
        if j.agent == "random"
    }
    assert eps[950] != eps[951]


def test_wall_estimate_schedules_on_workers():
    assert sweep.wall_estimate([10, 10, 10, 10], 2) == 20
    assert sweep.wall_estimate([30, 10, 10], 2) == 30


def test_rq3_conditions_reach_configs():
    jobs = sweep.manifest(sweep.load_spec(SPECS / "rq3.yaml"))
    conds = {j.condition: from_dict(j.cfg).env for j in jobs}
    assert set(conds) == {"mild_noclick3", "moderate_logit", "severe_cascade"}
    assert conds["mild_noclick3"].no_click_mass == 3.0
    assert conds["moderate_logit"].choice_model == "multinomial_logit"
    assert conds["severe_cascade"].choice_model == "proportional_cascade"
    assert all(j.cell == (10, 3) for j in jobs)


def test_phase6b_variants_change_only_the_named_settings():
    fz = sweep.frozen()
    jobs = sweep.manifest(sweep.load_spec(SPECS / "phase6b.yaml"))
    assert len(jobs) == 5 * 2 * 5  # variants x cells x seeds
    by = {j.key: j for j in jobs}
    lm = by["lm_lr1e-3|N10k3|matched|seed0"]
    assert lm.agent == "learned_myopic" and lm.label == "lm_lr1e-3"
    assert lm.cfg["agent"]["params"] == {**fz["params"]["learned_myopic"], "learning_rate": 0.001}
    g = by["slateq_g0.9|N80k3|matched|seed4"]
    assert g.cfg["agent"]["params"] == {**fz["params"]["slateq"], "gamma": 0.9}
    assert all(j.cfg["train_steps"] == fz["train_steps"] for j in jobs)
    budget = sweep.manifest(sweep.load_spec(SPECS / "phase6b_budget.yaml"))
    assert {j.cfg["train_steps"] for j in budget} == {2 * fz["train_steps"]}
    assert all(j.cfg["agent"]["params"] == fz["params"][j.agent] for j in budget)


def test_variants_cannot_change_other_settings(tmp_path):
    bad = [{"name": "x", "agent": "slateq", "params": {"target_update_period": 4000}}]
    with pytest.raises(sweep.SpecError):
        sweep.load_spec(_spec(tmp_path, variants=bad))
    with pytest.raises(sweep.SpecError):
        sweep.load_spec(_spec(tmp_path, variants=[{"name": "x", "agent": "random"}]))


def test_plain_agent_jobs_are_unchanged_by_the_variant_feature():
    """rq2 jobs keep their keys and labels, so earlier results are found as before."""
    jobs = sweep.manifest(sweep.load_spec(SPECS / "rq2.yaml"))
    assert all(j.variant == "" and j.label == j.agent for j in jobs)
    assert all(j.key.startswith(j.agent + "|") for j in jobs)
