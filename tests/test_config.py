from __future__ import annotations

import pytest

from slateq_study.config import ConfigError, from_dict, load_config

BASE = {
    "experiment": "t",
    "env": {"num_candidates": 10, "slate_size": 3},
    "agent": {"name": "random"},
}


def cfg(**env):
    return {**BASE, "env": {**BASE["env"], **env}}


@pytest.mark.parametrize(
    "env",
    [
        {"slate_size": 11},  # k > N
        {"slate_size": 0},  # k < 1
        {"num_candidates": 1, "slate_size": 1},  # N < 2
        {"max_steps": 0},
        {"num_candidates": 2.5},
    ],
)
def test_invalid_env_rejected(env):
    with pytest.raises(ConfigError):
        from_dict(cfg(**env))


def test_degenerate_cell_allowed_but_flagged():
    c = from_dict(cfg(num_candidates=3, slate_size=3))
    assert c.env.degenerate
    assert not from_dict(BASE).env.degenerate


@pytest.mark.parametrize(
    "bad",
    [
        {**BASE, "typo_key": 1},
        {**BASE, "env": {"num_candidate": 10}},
        {**BASE, "agent": {"name": "no_such_agent"}},
        {**BASE, "experiment": "bad name/with slash"},
        {**BASE, "eval_episodes": 0},
        {**BASE, "train_steps": -1},
    ],
)
def test_bad_configs_rejected(bad):
    with pytest.raises(ConfigError):
        from_dict(bad)


def test_hash_is_canonical_and_sensitive():
    a = from_dict(BASE)
    b = from_dict(
        {
            "agent": {"name": "random"},
            "env": {"slate_size": 3, "num_candidates": 10},
            "experiment": "t",
        }
    )
    assert a.config_hash == b.config_hash  # key order does not matter
    assert from_dict(cfg(slate_size=2)).config_hash != a.config_hash


def test_smoke_config_loads():
    from slateq_study.io import REPO_ROOT

    c = load_config(REPO_ROOT / "configs" / "smoke.yaml")
    assert c.eval_episodes == 3 and c.agent.name == "random"
