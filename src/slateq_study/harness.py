"""Episode loop. Owns the agent call order and per-episode seeding.

Each episode gets a FRESH env built with its own env seed, and the global np.random is seeded with
the same value. That makes episode i identical in its random inputs for every agent (common random
numbers), even though agents produce different episode lengths (RECON risk 3).
"""

from __future__ import annotations

import logging

import numpy as np

from slateq_study import seeding
from slateq_study.agents.base import Agent
from slateq_study.config import EnvConfig
from slateq_study.envs import make_env
from slateq_study.metrics import EpisodeRecord

log = logging.getLogger(__name__)


def run_episode(agent: Agent, env_cfg: EnvConfig, env_seed: int, episode: int = 0) -> EpisodeRecord:
    seeding.seed_global(env_seed)
    env = make_env(env_cfg, env_seed)
    obs = env.reset()
    slate = agent.begin_episode(obs)
    total, length, clicks, qualities = 0.0, 0, 0, []
    terminated = truncated = False
    while True:
        obs, reward, done, _ = env.step(slate)
        reward = float(reward)
        total += reward
        length += 1
        for resp in obs["response"]:
            if resp["click"]:
                clicks += 1
                qualities.append(float(resp["quality"]))
        terminated = bool(done)
        truncated = (not terminated) and length >= env_cfg.max_steps
        if terminated or truncated:
            agent.end_episode(reward, obs)
            break
        slate = agent.step(reward, obs)
    if truncated:
        log.warning("episode %d (env_seed %d) truncated at max_steps=%d", episode, env_seed, length)
    return EpisodeRecord(
        episode=episode,
        env_seed=env_seed,
        total_reward=total,
        length=length,
        clicks=clicks,
        mean_clicked_quality=float(np.mean(qualities)) if qualities else float("nan"),
        terminated=terminated,
        truncated=truncated,
    )


def evaluate(
    agent: Agent, env_cfg: EnvConfig, run_seed: int, n_episodes: int
) -> list[EpisodeRecord]:
    """Evaluation episodes on the EVAL seed stream (shared by all agents -> paired comparisons)."""
    agent.set_eval_mode(True)
    records = []
    for ep in range(n_episodes):
        rec = run_episode(agent, env_cfg, seeding.env_seed("eval", run_seed, ep), episode=ep)
        log.info("eval episode %d: reward=%.3f length=%d", ep, rec.total_reward, rec.length)
        records.append(rec)
    return records
