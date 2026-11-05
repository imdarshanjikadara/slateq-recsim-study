"""Seed streams. One run seed -> disjoint train / tune / eval environment-seed streams.

Environment seeds live in disjoint integer ranges BY CONSTRUCTION (not by hashing luck):

    env_seed = STREAM_OFFSET[stream] + run_seed * EPISODES_PER_SEED + episode

with run_seed < MAX_RUN_SEEDS and episode < EPISODES_PER_SEED, so every value of one stream stays
below the next stream's offset and below 2**32 (np.random.seed's limit).

Common random numbers: eval env seeds depend only on (run_seed, episode), never on the agent, so
every method sees the same users and candidate draws in evaluation episode i of seed s.
"""

from __future__ import annotations

import random

import numpy as np

STREAMS = ("train", "tune", "eval")
EPISODES_PER_SEED = 100_000
MAX_RUN_SEEDS = 10_000
_STREAM_WIDTH = EPISODES_PER_SEED * MAX_RUN_SEEDS  # 1e9
STREAM_OFFSET = {name: i * _STREAM_WIDTH for i, name in enumerate(STREAMS)}
assert STREAM_OFFSET["eval"] + _STREAM_WIDTH < 2**32


def env_seed(stream: str, run_seed: int, episode: int) -> int:
    if stream not in STREAM_OFFSET:
        raise ValueError(f"unknown seed stream {stream!r}; expected one of {STREAMS}")
    if not 0 <= run_seed < MAX_RUN_SEEDS:
        raise ValueError(f"run_seed must be in [0, {MAX_RUN_SEEDS}), got {run_seed}")
    if not 0 <= episode < EPISODES_PER_SEED:
        raise ValueError(f"episode must be in [0, {EPISODES_PER_SEED}), got {episode}")
    return STREAM_OFFSET[stream] + run_seed * EPISODES_PER_SEED + episode


def agent_seed(run_seed: int) -> int:
    """Seed for an agent's own RNG (exploration, network init). Independent of env seeds."""
    return int(np.random.SeedSequence([run_seed, 0xA6E7]).generate_state(1)[0])


def seed_global(seed: int) -> None:
    """Seed Python's and NumPy's GLOBAL RNGs. RecSim's choice model and interest updates use
    np.random directly, so this must be called before every episode (docs/ENV.md pitfall 3)."""
    random.seed(seed)
    np.random.seed(seed)


def seed_torch(seed: int) -> None:
    import torch

    torch.manual_seed(seed)
