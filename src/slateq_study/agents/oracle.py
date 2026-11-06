"""Oracle-myopic baseline: RecSim's GreedyPCTRAgent with PRIVILEGED access.

What it gets that learned agents do not (logged at construction):
  * the TRUE user-state object (re-attached after every env.reset(); a new user object is sampled
    per episode), and
  * the environment's TRUE choice model (PROTOCOL S4), instead of GreedyPCTR's default
    (MultinomialLogit, no_click_mass=5). Both rank candidates identically in Interest Evolution,
    since both scores are monotone in user_interest . doc_features.
It ranks candidates by click score and shows the top k: the best a click-maximiser can do.
Its scoring uses no random numbers, so it never disturbs the global RNG (common random numbers).
"""

from __future__ import annotations

import logging

import numpy as np

from slateq_study import recsim_compat
from slateq_study.agents.base import Agent, Observation
from slateq_study.envs import true_user_state, user_model

log = logging.getLogger(__name__)


class OracleMyopicAgent(Agent):
    name = "oracle_myopic"
    privileged = True

    def __init__(self, action_space, seed: int):
        super().__init__(action_space, seed)
        recsim_compat.install()
        self._action_space = action_space
        self._impl = None
        log.info(
            "oracle_myopic is PRIVILEGED: it reads the true user state and true choice model "
            "from the environment (learned agents do not)."
        )

    def attach_true_state(self, env) -> None:
        from recsim.agents import greedy_pctr_agent

        state = true_user_state(env)
        true_model = type(user_model(env).choice_model)(state.choice_features)
        self._impl = greedy_pctr_agent.GreedyPCTRAgent(
            self._action_space, belief_state=state, choice_model=true_model
        )

    def _act(self, observation: Observation) -> np.ndarray:
        if self._impl is None:
            raise RuntimeError("attach_true_state(env) must be called after env.reset()")
        return np.asarray(self._impl.step(0.0, observation))

    def begin_episode(self, observation: Observation) -> np.ndarray:
        return self._act(observation)

    def step(self, reward: float, observation: Observation) -> np.ndarray:
        return self._act(observation)

    def end_episode(self, reward: float, observation: Observation, truncated: bool = False) -> None:
        self._impl = None  # never reuse a previous user's state
