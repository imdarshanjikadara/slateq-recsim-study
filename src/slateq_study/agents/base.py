"""The single agent interface every agent implements (plain, RecSim-wrapped, or PyTorch).

Call order for one episode (enforced by harness.run_episode):
    slate = agent.begin_episode(obs0)
    repeat:  obs, r, done = env.step(slate)
             if episode over: agent.end_episode(r, obs, truncated); stop
             slate = agent.step(r, obs)
so the final reward always reaches the agent through end_episode.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

Observation = dict[str, Any]


class Agent(ABC):
    """Base class. `slate_size` and `num_candidates` come from the env's action space."""

    name: str = "base"
    learns: bool = False
    privileged: bool = False  # True only for the oracle: harness calls attach_true_state()

    def __init__(self, action_space: Any, seed: int):
        self.num_candidates = int(action_space.nvec[0])
        self.slate_size = int(len(action_space.nvec))
        self.seed = seed
        self.eval_mode = False

    def set_eval_mode(self, flag: bool) -> None:
        self.eval_mode = bool(flag)

    @abstractmethod
    def begin_episode(self, observation: Observation) -> np.ndarray: ...

    @abstractmethod
    def step(self, reward: float, observation: Observation) -> np.ndarray: ...

    def end_episode(  # noqa: B027
        self, reward: float, observation: Observation, truncated: bool = False
    ) -> None:
        """Optional hook; learning agents use it to store the terminal transition."""

    def attach_true_state(self, env) -> None:
        """PRIVILEGED hook, called by the harness after env.reset() only if `privileged`."""
        raise NotImplementedError(f"{self.name} is not a privileged agent")
