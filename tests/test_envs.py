"""Our env factory must reproduce RecSim's own create_environment exactly (default choice model),
and expose only what PROTOCOL.md says."""

from __future__ import annotations

import numpy as np
import pytest

from slateq_study import recsim_compat, seeding
from slateq_study.config import CHOICE_MODELS, ConfigError, EnvConfig
from slateq_study.envs import make_env


def _rollout(env, global_seed: int, n_steps: int = 40):
    """Fixed slate policy (first k items); record everything observable."""
    seeding.seed_global(global_seed)
    obs = env.reset()
    k = len(env.action_space.nvec)
    out = [(obs["user"].copy(), [d.copy() for d in obs["doc"].values()])]
    for _ in range(n_steps):
        obs, r, done, _ = env.step(list(range(k)))
        out.append(
            (
                obs["user"].copy(),
                [d.copy() for d in obs["doc"].values()],
                r,
                done,
                [dict(x) for x in obs["response"]],
            )
        )
        if done:
            break
    return out


def _equal(a, b) -> bool:
    if isinstance(a, np.ndarray):
        return np.array_equal(a, b)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    return a == b


@pytest.mark.parametrize("n,k,seed", [(5, 2, 0), (10, 3, 7), (20, 5, 123)])
def test_matches_recsim_create_environment(n, k, seed):
    recsim_compat.install()
    from recsim.environments import interest_evolution as ie

    ours = make_env(EnvConfig(num_candidates=n, slate_size=k), seed)
    theirs = ie.create_environment(
        {"num_candidates": n, "slate_size": k, "resample_documents": True, "seed": seed}
    )
    assert _equal(_rollout(ours, seed), _rollout(theirs, seed))


def test_default_choice_model_is_recsims():
    env = make_env(EnvConfig(), 0)
    assert type(env._environment.user_model.choice_model).__name__ == (
        "MultinomialProportionalChoiceModel"
    )


@pytest.mark.parametrize("name", sorted(CHOICE_MODELS))
def test_every_choice_model_constructs(name):
    env = make_env(EnvConfig(choice_model=name), 0)
    assert type(env._environment.user_model.choice_model).__name__ == CHOICE_MODELS[name]


def test_unknown_choice_model_rejected():
    with pytest.raises(ConfigError):
        make_env(EnvConfig(choice_model="nope"), 0)
