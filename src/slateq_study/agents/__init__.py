"""Agent registry and factory."""

from __future__ import annotations

from typing import Any

from slateq_study.agents.base import Agent
from slateq_study.agents.random import RandomAgent
from slateq_study.agents.testing import FailingAgent

AGENTS: dict[str, type[Agent]] = {
    RandomAgent.name: RandomAgent,
    FailingAgent.name: FailingAgent,
}


def make_agent(name: str, action_space: Any, seed: int, **params: Any) -> Agent:
    if name not in AGENTS:
        raise ValueError(f"unknown agent {name!r}; known: {sorted(AGENTS)}")
    return AGENTS[name](action_space, seed, **params)


__all__ = ["AGENTS", "Agent", "make_agent"]
