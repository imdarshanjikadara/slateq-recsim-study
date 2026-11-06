"""SlateQ port vs the reference maths (RecSim slate_decomp_q_agent.py, Ie et al. 2019 Eq. 19)."""

from __future__ import annotations

import itertools

import numpy as np
import pytest
import torch

from slateq_study import recsim_compat
from slateq_study.agents import make_agent
from slateq_study.agents.slateq import (
    ReplayBuffer,
    linearly_decaying_epsilon,
    sarsa_target,
    score_documents,
    select_slate_greedy,
    select_slate_topk,
)
from slateq_study.config import EnvConfig
from slateq_study.envs import make_env
from slateq_study.harness import run_episode, train

ENV = EnvConfig(num_candidates=5, slate_size=2)
SPACE = make_env(ENV, 0).action_space


def test_scores_match_recsim_multinomial_proportional():
    """Agent's assumed model == RecSim's numpy MultinomialProportionalChoiceModel (env default)."""
    recsim_compat.install()
    from recsim import choice_model
    from recsim.environments import interest_evolution as ie

    rng = np.random.default_rng(0)
    user_state = ie.UtilityModelUserSampler(seed=3).sample_user()
    docs = np.eye(20)[rng.integers(0, 20, size=7)]
    cm = choice_model.MultinomialProportionalChoiceModel(user_state.choice_features)
    cm.score_documents(user_state, docs)
    s, s0 = score_documents(
        torch.tensor(user_state.user_interests, dtype=torch.float64),
        torch.tensor(docs, dtype=torch.float64),
    )
    np.testing.assert_allclose(s.numpy(), cm.scores, rtol=0, atol=1e-12)
    assert float(s0) == pytest.approx(cm.score_no_click)


def test_topk_selects_largest_s_times_q():
    s = torch.tensor([1.0, 2.0, 0.5, 1.5])
    q = torch.tensor([4.0, 1.0, 10.0, 2.0])  # s*q = 4, 2, 5, 3
    assert sorted(select_slate_topk(2, 2.0, s, q).tolist()) == [0, 2]


def _slate_value(slate, s, q, s0):
    den = s0 + sum(s[i] for i in slate)
    return sum(s[i] * q[i] for i in slate) / den


def test_greedy_matches_marginal_rule_and_is_near_optimal():
    rng = np.random.default_rng(1)
    for _ in range(50):
        s = torch.tensor(rng.uniform(0.1, 2.0, 6))
        q = torch.tensor(rng.uniform(0.0, 10.0, 6))
        g = select_slate_greedy(3, 2.0, s, q).tolist()
        assert len(set(g)) == 3
        # first pick is the best single item
        best1 = max(range(6), key=lambda i: _slate_value([i], s, q, 2.0))
        assert g[0] == best1
        best = max(_slate_value(c, s, q, 2.0) for c in itertools.combinations(range(6), 3))
        assert _slate_value(g, s, q, 2.0) <= best + 1e-12


def test_sarsa_target_hand_computed():
    # next candidates scores s' = [1, 3, 2], no-click 2; next slate A' = [1, 2]
    # P = [3, 2] / (3 + 2 + 2) = [3/7, 2/7]; Q_target = [10, 5, 7] -> expected = (3*5 + 2*7)/7
    reward = torch.tensor([4.0, 4.0])
    next_s = torch.tensor([[1.0, 3.0, 2.0]] * 2)
    next_q = torch.tensor([[10.0, 5.0, 7.0]] * 2)
    s0 = torch.tensor([2.0, 2.0])
    slate = torch.tensor([[1, 2]] * 2)
    term = torch.tensor([False, True])
    t = sarsa_target(reward, 0.9, slate, next_q, next_s, s0, term)
    assert t[0].item() == pytest.approx(4.0 + 0.9 * 29.0 / 7.0)
    assert t[1].item() == pytest.approx(4.0)  # terminal: no bootstrap
    t0 = sarsa_target(reward, 0.0, slate, next_q, next_s, s0, term)
    assert torch.allclose(t0, reward)  # gamma = 0: myopic target


def test_epsilon_schedule_matches_dopamine():
    f = linearly_decaying_epsilon
    assert f(100, 0, 20, 0.01) == 1.0
    assert f(100, 20, 20, 0.01) == 1.0  # still 1 at end of warmup
    assert f(100, 70, 20, 0.01) == pytest.approx(0.01 + 0.99 * 0.5)
    assert f(100, 1000, 20, 0.01) == 0.01


def test_replay_roundtrip_and_one_hot_guard():
    rb = ReplayBuffer(4, 20, 3, 20, 2)
    docs = np.eye(20)[[3, 7, 11]]
    ids = ReplayBuffer.encode_docs(docs)
    for i in range(6):  # wraps around
        rb.add(
            np.full(20, i, np.float32),
            ids,
            [0, 1],
            i % 2 - 1,
            float(i),
            np.zeros(20),
            ids,
            [1, 2],
            i == 5,
        )
    assert rb.size == 4 and rb.add_count == 6
    b = rb.sample(np.random.default_rng(0), 8)
    assert torch.equal(b["docs"][0], torch.tensor(docs, dtype=torch.float32))
    with pytest.raises(ValueError):
        ReplayBuffer.encode_docs(np.full((3, 20), 0.5))


def test_learned_myopic_forces_gamma_zero():
    assert make_agent("learned_myopic", SPACE, 0).gamma == 0.0
    with pytest.raises(ValueError):
        make_agent("learned_myopic", SPACE, 0, gamma=0.99)


def _small_agent(name="slateq", **kw):
    params = dict(
        min_replay_history=200, epsilon_decay_period=300, target_update_period=100, update_period=4
    )
    params.update(kw)
    return make_agent(name, SPACE, seed=0, **params)


def test_transitions_store_next_slate_and_terminal():
    agent = _small_agent()
    rec = run_episode(agent, ENV, env_seed=5).record
    rb = agent.replay
    assert rb.size == rec.length  # one transition per env step
    assert rb.terminal[: rb.size].sum() == 1 and rb.terminal[rb.size - 1]
    # SARSA: next_slate of transition t == slate of transition t+1 within the episode
    assert np.array_equal(rb.next_slate[: rb.size - 1], rb.slate[1 : rb.size])
    # next candidates of t == candidates of t+1 (resampled set, seen by the agent)
    assert np.array_equal(rb.next_docs[: rb.size - 1], rb.docs[1 : rb.size])
    clicked = rb.click_pos[: rb.size] >= 0
    assert (rb.reward[: rb.size][~clicked] == 0).all()
    assert rec.total_reward == pytest.approx(float(rb.reward[: rb.size].sum()))


def test_training_budget_exact_and_eval_mode_stores_nothing():
    agent = _small_agent()
    curves = train(agent, ENV, run_seed=0, total_steps=700, eval_every=350, curve_episodes=2)
    assert agent.training_steps == 700 and agent.replay.add_count == 700
    assert [c["train_steps"] for c in curves][0] == 0 and curves[-1]["train_steps"] == 700
    assert all(np.isfinite(c["mean_total_reward"]) for c in curves)
    before = agent.replay.add_count
    agent.set_eval_mode(True)
    run_episode(agent, ENV, env_seed=1)
    assert agent.replay.add_count == before and agent.training_steps == 700
    assert agent.epsilon == 0.0


def test_target_sync_and_update_counts():
    agent = _small_agent()
    train(agent, ENV, run_seed=1, total_steps=1000, eval_every=0)
    # updates every 4 steps after replay exceeds 200 transitions; syncs every 100 steps after that
    assert agent.updates <= (1000 - 200) // 4 + 1
    assert agent.updates >= (1000 - 200) // 4 - 5  # a few batches may have no clicks
    assert agent.target_syncs == len([t for t in range(201, 1001) if t % 100 == 0])
    for p, pt in zip(agent.online.parameters(), agent.target.parameters(), strict=True):
        assert torch.equal(p, pt)  # synced at step 1000


def test_exploration_does_not_touch_global_rng():
    agent = _small_agent()
    np.random.seed(123)
    expected = np.random.rand()
    np.random.seed(123)
    for _ in range(20):
        agent._act(make_env(ENV, 0).reset())
    assert np.random.rand() == expected


def test_same_seed_same_training():
    a, b = _small_agent(), _small_agent()
    train(a, ENV, 0, 600)
    train(b, ENV, 0, 600)
    for p, q in zip(a.online.parameters(), b.online.parameters(), strict=True):
        assert torch.equal(p, q)
