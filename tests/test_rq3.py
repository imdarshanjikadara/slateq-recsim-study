"""RQ3 plumbing: the environment's TRUE choice model is separate from what the agents assume."""

from __future__ import annotations

import numpy as np
import pytest

from slateq_study import seeding
from slateq_study.agents import make_agent
from slateq_study.config import EnvConfig, from_dict
from slateq_study.envs import make_env, true_user_state, user_model

LADDER = [
    ("multinomial_proportional", 1.0),
    ("multinomial_proportional", 3.0),
    ("multinomial_logit", 1.0),
    ("proportional_cascade", 1.0),
]


def _reset(cfg: EnvConfig, seed: int = 12345):
    env = make_env(cfg, seed)
    seeding.seed_global(seed)
    return env, env.reset()


@pytest.mark.parametrize("cm,ncm", LADDER)
def test_true_choice_model_and_no_click_mass_reach_the_env(cm, ncm):
    env, _ = _reset(EnvConfig(choice_model=cm, no_click_mass=ncm))
    um = user_model(env)
    assert (
        type(um.choice_model).__name__
        == {
            "multinomial_proportional": "MultinomialProportionalChoiceModel",
            "multinomial_logit": "MultinomialLogitChoiceModel",
            "proportional_cascade": "ProportionalCascadeChoiceModel",
        }[cm]
    )
    assert true_user_state(env).choice_features["no_click_mass"] == ncm
    if cm != "proportional_cascade":
        assert um.choice_model._no_click_mass == ncm


def test_slateq_scoring_does_not_depend_on_the_env_choice_model():
    """Changing ONLY the env's true model leaves the agent's scoring and slate unchanged."""
    slates = []
    for cm, ncm in LADDER:
        env, obs = _reset(EnvConfig(choice_model=cm, no_click_mass=ncm))
        agent = make_agent("slateq", env.action_space, 7, min_replay_history=10**9)
        agent.eval_mode = True
        slates.append(np.asarray(agent.begin_episode(obs)))
    for s in slates[1:]:
        np.testing.assert_array_equal(s, slates[0])


@pytest.mark.parametrize("cm,ncm", LADDER)
def test_oracle_ranks_by_true_affinity_in_every_condition(cm, ncm):
    env, obs = _reset(
        EnvConfig(num_candidates=10, slate_size=3, choice_model=cm, no_click_mass=ncm)
    )
    oracle = make_agent("oracle_myopic", env.action_space, 0)
    oracle.attach_true_state(env)
    slate = np.asarray(oracle.begin_episode(obs))
    state = true_user_state(env)
    docs = list(obs["doc"].values())
    affinity = np.array([state.score_document(d) for d in docs])
    # same-cluster documents tie (one-hot features), so compare affinities, in slate order
    np.testing.assert_array_equal(affinity[slate], np.sort(affinity)[::-1][:3])


def test_default_no_click_mass_keeps_existing_hashes():
    base = {"experiment": "smoke", "env": {"num_candidates": 10, "slate_size": 3,
            "resample_documents": True, "max_steps": 1000}, "agent": {"name": "random"},
            "train_steps": 0, "eval_episodes": 3}  # fmt: skip
    assert from_dict(base).config_hash == "b89f083ec0ee"
    explicit = {**base, "env": {**base["env"], "no_click_mass": 1.0}}
    assert from_dict(explicit).config_hash == "b89f083ec0ee"
    other = {**base, "env": {**base["env"], "no_click_mass": 3.0}}
    assert from_dict(other).config_hash != "b89f083ec0ee"


@pytest.mark.parametrize("cm", ["proportional_cascade", "exponential_cascade", "multinomial_logit"])
def test_every_rq3_choice_model_runs_full_episodes(cm):
    """RecSim's proportional cascade fails under numpy 2; our compat subclass must run."""
    from slateq_study.harness import run_episode

    agent = make_agent("random", make_env(EnvConfig(choice_model=cm), 1).action_space, 3)
    rec = run_episode(agent, EnvConfig(choice_model=cm), env_seed=4242).record
    assert rec.length > 0 and np.isfinite(rec.total_reward)


def test_cascade_compat_matches_recsim_math():
    from recsim import choice_model as rcm

    from slateq_study.choice_compat import proportional_cascade_cls

    feats = {"min_normalizer": -1.0, "attention_prob": 0.65, "score_scaling": 0.05}
    ours, ref = proportional_cascade_cls()(feats), rcm.ProportionalCascadeChoiceModel(feats)
    raw = np.array([0.3, -0.2, 0.9])
    ours._score_documents_helper = staticmethod(lambda u, d: raw.copy())
    ours.score_documents(None, None)
    ref._positional_normalization(raw - (-1.0))  # RecSim's own maths on the same scores
    np.testing.assert_allclose(ours.scores, ref.scores)
    np.testing.assert_allclose(ours._score_no_click, ref._score_no_click)
    assert issubclass(type(ours), rcm.CascadeChoiceModel)
