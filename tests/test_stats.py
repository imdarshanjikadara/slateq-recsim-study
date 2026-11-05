"""Known-answer tests for the protocol statistics."""

from __future__ import annotations

import math

import numpy as np
import pytest

from slateq_study import stats


def test_bootstrap_constant_sample_is_degenerate():
    assert stats.bootstrap_ci([3.0, 3.0, 3.0]) == (3.0, 3.0)


def test_bootstrap_ci_contains_mean_and_is_reproducible():
    x = [1.0, 2.0, 3.0, 4.0, 10.0]
    lo, hi = stats.bootstrap_ci(x)
    assert lo <= np.mean(x) <= hi
    assert (lo, hi) == stats.bootstrap_ci(x)
    assert lo >= min(x) and hi <= max(x)


def test_bootstrap_matches_exact_enumeration_for_two_values():
    # Resampling 2 values with replacement: means 0 (p=1/4), 0.5 (1/2), 1 (1/4) -> 95% CI [0, 1]
    assert stats.bootstrap_ci([0.0, 1.0]) == (0.0, 1.0)


def test_bootstrap_rejects_nan_and_empty():
    with pytest.raises(ValueError):
        stats.bootstrap_ci([])
    with pytest.raises(ValueError):
        stats.bootstrap_ci([1.0, float("nan")])


def test_seed_summary_values():
    s = stats.seed_summary([1.0, 2.0, 3.0])
    assert s["n_seeds"] == 3 and s["mean"] == 2.0 and math.isclose(s["std"], 1.0)


def test_paired_differences_requires_same_seeds():
    assert stats.paired_differences({0: 5.0, 1: 7.0}, {0: 4.0, 1: 4.0}) == {0: 1.0, 1: 3.0}
    with pytest.raises(ValueError):
        stats.paired_differences({0: 1.0, 1: 2.0}, {0: 1.0})


def test_paired_episode_stats_known_answer():
    p = stats.paired_episode_stats([3.0, 5.0, 7.0], [1.0, 2.0, 3.0])  # diffs 2, 3, 4
    assert p["mean_diff"] == 3.0 and math.isclose(p["sd_diff"], 1.0)
    assert math.isclose(p["se_diff"], 1 / math.sqrt(3))


def test_episodes_for_target_se():
    assert stats.episodes_for_target_se(10.0, 0.5) == 400
    assert stats.episodes_for_target_se(10.1, 0.5) == 409  # ceil(408.04)
