"""Random baseline: RecSim's own RandomAgent (uses its own RandomState, not the global RNG)."""

from __future__ import annotations

import numpy as np

from slateq_study import recsim_compat
from slateq_study.agents.base import Agent, Observation


class RandomAgent(Agent):
    name = "random"

    def __init__(self, action_space, seed: int):
        super().__init__(action_space, seed)
        recsim_compat.install()
        from recsim.agents import random_agent

        self._impl = random_agent.RandomAgent(action_space, random_seed=seed)

    def begin_episode(self, observation: Observation) -> np.ndarray:
        return np.asarray(self._impl.begin_episode(observation))

    def step(self, reward: float, observation: Observation) -> np.ndarray:
        return np.asarray(self._impl.step(reward, observation))
