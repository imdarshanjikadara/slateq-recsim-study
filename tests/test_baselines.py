"""Oracle agent, common random numbers, per-step candidate checks, traces, and the Phase 2 sanity
requirement that oracle-myopic beats random (PROTOCOL §10)."""

from __future__ import annotations

import numpy as np
import pytest

from slateq_study import seeding, stats
from slateq_study.agents import make_agent
from slateq_study.agents.base import Agent
from slateq_study.config import EnvConfig
from slateq_study.envs import make_env
from slateq_study.harness import SlateError, evaluate, run_episode

ENV = EnvConfig(num_candidates=10, slate_size=3)
SPACE = make_env(ENV, 0).action_space


class FirstObsRecorder(Agent):
    """Wraps another agent; remembers the first observation of each episode."""

    def __init__(self, inner):
        self.inner, self.first_obs = inner, []
        self.privileged = inner.privileged
        self.num_candidates, self.slate_size = inner.num_candidates, inner.slate_size

    def attach_true_state(self, env):
        self.inner.attach_true_state(env)

    def begin_episode(self, observation):
        self.first_obs.append(
            (observation["user"].copy(), np.stack(list(observation["doc"].values())))
        )
        return self.inner.begin_episode(observation)

    def step(self, reward, observation):
        return self.inner.step(reward, observation)

    def end_episode(self, reward, observation):
        self.inner.end_episode(reward, observation)


def test_common_random_numbers_same_user_and_candidates_at_step0():
    a = FirstObsRecorder(make_agent("random", SPACE, 0))
    b = FirstObsRecorder(make_agent("oracle_myopic", SPACE, 0))
    evaluate(a, ENV, run_seed=3, n_episodes=5)
    evaluate(b, ENV, run_seed=3, n_episodes=5)
    for (ua, da), (ub, db) in zip(a.first_obs, b.first_obs, strict=True):
        assert np.array_equal(ua, ub) and np.array_equal(da, db)


def test_oracle_picks_top_k_by_true_interest():
    agent = make_agent("oracle_myopic", SPACE, 0)
    seeding.seed_global(1)
    env = make_env(ENV, 1)
    obs = env.reset()
    agent.attach_true_state(env)
    slate = agent.begin_episode(obs)
    interests = env._environment.user_model._user_state.user_interests
    scores = np.array([interests @ d for d in obs["doc"].values()])
    assert set(slate.tolist()) == set(np.argsort(-scores)[:3].tolist())


def test_oracle_requires_true_state():
    agent = make_agent("oracle_myopic", SPACE, 0)
    obs = make_env(ENV, 0).reset()
    with pytest.raises(RuntimeError):
        agent.begin_episode(obs)


def test_oracle_and_random_never_duplicate_items():
    for name in ("random", "oracle_myopic"):
        recs, _ = evaluate(make_agent(name, SPACE, 0), ENV, 0, 5, stream="tune")
        assert sum(r.duplicate_slates for r in recs) == 0


class BadSlateAgent(Agent):
    def __init__(self, slate):
        super().__init__(SPACE, 0)
        self._slate = slate

    def begin_episode(self, observation):
        return np.asarray(self._slate)

    def step(self, reward, observation):
        return np.asarray(self._slate)


@pytest.mark.parametrize("slate", [[0, 1], [0, 1, 10], [0.0, 1.0, 2.0], [-1, 0, 1]])
def test_invalid_slates_rejected(slate):
    with pytest.raises(SlateError):
        run_episode(BadSlateAgent(slate), ENV, env_seed=0)


def test_duplicate_slates_counted_not_hidden():
    rec = run_episode(BadSlateAgent([2, 2, 5]), ENV, env_seed=0).record
    assert rec.duplicate_slates == rec.length


def test_traces_only_for_first_n_episodes():
    _, traces = evaluate(make_agent("random", SPACE, 0), ENV, 0, 4, stream="tune", trace_episodes=2)
    assert {t["episode"] for t in traces} == {0, 1}
    t0 = traces[0]
    assert len(t0["user_interests"]) == 20 and len(t0["slate"]) == 3
    assert t0["time_budget_after"] < 200


def test_oracle_beats_random_pilot():
    """PROTOCOL §10 sanity. 150 paired tune-stream episodes; require mean diff > 2 SE.
    If this fails it is a FINDING about the pipeline, not a flaky test (it is deterministic)."""
    env = EnvConfig(num_candidates=10, slate_size=3)
    ro, _ = evaluate(make_agent("oracle_myopic", SPACE, 0), env, 9, 150, stream="tune")
    rr, _ = evaluate(make_agent("random", SPACE, 0), env, 9, 150, stream="tune")
    p = stats.paired_episode_stats([r.total_reward for r in ro], [r.total_reward for r in rr])
    assert p["mean_diff"] > 2 * p["se_diff"], p
