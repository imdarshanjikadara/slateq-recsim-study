"""Episode records and NaN-safe summaries."""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass

import numpy as np


@dataclass
class EpisodeRecord:
    episode: int
    env_seed: int
    total_reward: float
    length: int
    clicks: int
    mean_clicked_quality: float  # NaN when the episode had no clicks
    terminated: bool  # user's time budget ran out (true RecSim termination)
    truncated: bool  # stopped by our max_steps safeguard
    duplicate_slates: int = 0  # steps whose slate repeated an item

    @property
    def reward_per_step(self) -> float:
        return self.total_reward / self.length if self.length else math.nan

    def to_row(self) -> dict:
        return {**dataclasses.asdict(self), "reward_per_step": self.reward_per_step}


def nan_mean(values) -> float:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[~np.isnan(arr)]
    return float(arr.mean()) if arr.size else math.nan


def summarize(records: list[EpisodeRecord]) -> dict:
    """Per-run summary = mean over evaluation episodes (docs/PROTOCOL.md fixes the full spec)."""
    if not records:
        raise ValueError("no episodes to summarise")
    return {
        "episodes": len(records),
        "mean_total_reward": nan_mean(r.total_reward for r in records),
        "mean_length": nan_mean(r.length for r in records),
        "mean_clicks": nan_mean(r.clicks for r in records),
        "mean_clicked_quality": nan_mean(r.mean_clicked_quality for r in records),
        "mean_reward_per_step": nan_mean(r.reward_per_step for r in records),
        "truncated_episodes": sum(r.truncated for r in records),
        "duplicate_slates": sum(r.duplicate_slates for r in records),
    }
