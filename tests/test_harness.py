from __future__ import annotations

import math

import numpy as np

from slateq_study.agents import make_agent
from slateq_study.agents.base import Agent
from slateq_study.config import EnvConfig
from slateq_study.envs import make_env
from slateq_study.harness import run_episode
from slateq_study.metrics import EpisodeRecord, summarize

ENV = EnvConfig(num_candidates=10, slate_size=3)


class RecordingAgent(Agent):
    """Picks the first k candidates; records the call sequence and rewards it receives."""

    name = "recording"

    def __init__(self, action_space, seed):
        super().__init__(action_space, seed)
        self.calls, self.rewards = [], []

    def _slate(self):
        return np.arange(self.slate_size)

    def begin_episode(self, observation):
        self.calls.append("begin")
        return self._slate()

    def step(self, reward, observation):
        self.calls.append("step")
        self.rewards.append(reward)
        return self._slate()

    def end_episode(self, reward, observation):
        self.calls.append("end")
        self.rewards.append(reward)


def _agent(cls=RecordingAgent):
    return cls(make_env(ENV, 0).action_space, seed=0)


def test_call_order_and_final_reward_delivered():
    agent = _agent()
    rec = run_episode(agent, ENV, env_seed=5).record
    assert agent.calls[0] == "begin" and agent.calls[-1] == "end"
    assert agent.calls.count("begin") == 1 and agent.calls.count("end") == 1
    assert len(agent.calls) == rec.length + 1  # begin + (length-1) steps + end
    # reward accounting: everything the agent was given sums to the episode total
    assert math.isclose(sum(agent.rewards), rec.total_reward, rel_tol=0, abs_tol=1e-9)
    assert rec.terminated and not rec.truncated


def test_same_seed_same_trajectory_random_agent():
    env = make_env(ENV, 0)
    a = run_episode(make_agent("random", env.action_space, 7), ENV, env_seed=11).record
    b = run_episode(make_agent("random", env.action_space, 7), ENV, env_seed=11).record
    assert a == b


def test_max_steps_truncation_counted_separately():
    short = EnvConfig(num_candidates=10, slate_size=3, max_steps=5)
    agent = _agent()
    rec = run_episode(agent, short, env_seed=1).record
    assert rec.length == 5 and rec.truncated and not rec.terminated
    assert agent.calls[-1] == "end"


def test_summary_nan_safe_when_no_clicks():
    recs = [
        EpisodeRecord(0, 0, 0.0, 3, 0, float("nan"), True, False),
        EpisodeRecord(1, 1, 4.0, 4, 1, 0.5, True, False),
    ]
    s = summarize(recs)
    assert s["mean_clicked_quality"] == 0.5
    all_nan = summarize(recs[:1])
    assert math.isnan(all_nan["mean_clicked_quality"]) and all_nan["mean_total_reward"] == 0.0
