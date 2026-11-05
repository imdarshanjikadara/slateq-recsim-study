"""Statistics fixed by docs/PROTOCOL.md.

Unit of replication = SEED. Per-run summary = mean over that run's evaluation episodes.
Across seeds: mean, sample std, and a bootstrap 95% CI that resamples SEEDS (never episodes).
Method comparisons are PAIRED per seed: every method is evaluated on the same eval env seeds
(common random numbers), so we bootstrap the per-seed differences.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

N_BOOT = 10_000
BOOT_SEED = 20261105  # fixed so every CI is exactly reproducible
CI_LEVEL = 0.95


def bootstrap_ci(
    values: Sequence[float], n_boot: int = N_BOOT, seed: int = BOOT_SEED, level: float = CI_LEVEL
) -> tuple[float, float]:
    """Percentile bootstrap CI of the mean, resampling the given values (one per seed)."""
    x = np.asarray(values, dtype=float)
    if x.size == 0 or np.isnan(x).any():
        raise ValueError("bootstrap_ci needs a non-empty, NaN-free sample")
    if x.size == 1:
        return (float(x[0]), float(x[0]))
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, x.size, size=(n_boot, x.size))].mean(axis=1)
    alpha = (1 - level) / 2
    lo, hi = np.quantile(means, [alpha, 1 - alpha])
    return float(lo), float(hi)


def seed_summary(per_seed: Sequence[float]) -> dict:
    """Across-seed summary of per-run means."""
    x = np.asarray(per_seed, dtype=float)
    lo, hi = bootstrap_ci(x)
    return {
        "n_seeds": int(x.size),
        "mean": float(x.mean()),
        "std": float(x.std(ddof=1)) if x.size > 1 else math.nan,
        "ci95_low": lo,
        "ci95_high": hi,
    }


def paired_differences(a: dict[int, float], b: dict[int, float]) -> dict[int, float]:
    """Per-seed difference a - b. Both must cover exactly the same seeds (no silent dropping)."""
    if set(a) != set(b):
        raise ValueError(f"seed sets differ: {sorted(set(a) ^ set(b))}")
    return {s: a[s] - b[s] for s in sorted(a)}


def paired_episode_stats(a: Sequence[float], b: Sequence[float]) -> dict:
    """Within one seed: episode-by-episode paired difference a - b (same env seeds)."""
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if x.shape != y.shape or x.size < 2:
        raise ValueError("paired samples must have the same length >= 2")
    d = x - y
    sd = float(d.std(ddof=1))
    return {
        "n": int(d.size),
        "mean_diff": float(d.mean()),
        "sd_diff": sd,
        "se_diff": sd / math.sqrt(d.size),
    }


def episodes_for_target_se(sd_diff: float, target_se: float) -> int:
    """Smallest n with sd_diff / sqrt(n) <= target_se (PROTOCOL S2)."""
    if sd_diff < 0 or target_se <= 0:
        raise ValueError("need sd_diff >= 0 and target_se > 0")
    return max(2, math.ceil((sd_diff / target_se) ** 2))
