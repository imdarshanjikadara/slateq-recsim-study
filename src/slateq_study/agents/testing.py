"""Test-only agent used to exercise failure handling (error.json, non-zero exit). Never use in
experiments."""

from __future__ import annotations

from slateq_study.agents.random import RandomAgent


class FailingAgent(RandomAgent):
    name = "_failing_for_tests"

    def step(self, reward, observation):
        raise RuntimeError("deliberate failure from FailingAgent (test fixture)")
