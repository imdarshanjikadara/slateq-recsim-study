from __future__ import annotations

import itertools

import numpy as np
import pytest

from slateq_study import seeding


def test_streams_disjoint_at_boundaries():
    edges = [0, 1, seeding.MAX_RUN_SEEDS - 1]
    eps = [0, 1, seeding.EPISODES_PER_SEED - 1]
    by_stream = {
        s: {seeding.env_seed(s, r, e) for r, e in itertools.product(edges, eps)}
        for s in seeding.STREAMS
    }
    for a, b in itertools.combinations(seeding.STREAMS, 2):
        assert not by_stream[a] & by_stream[b]
    # ranges are ordered and non-overlapping
    for a, b in zip(seeding.STREAMS, seeding.STREAMS[1:], strict=False):
        assert max(by_stream[a]) < min(by_stream[b])
    assert max(by_stream["eval"]) < 2**32


def test_env_seed_unique_within_stream():
    seeds = {seeding.env_seed("eval", r, e) for r in range(5) for e in range(200)}
    assert len(seeds) == 1000


@pytest.mark.parametrize(
    "args",
    [
        ("bogus", 0, 0),
        ("eval", -1, 0),
        ("eval", seeding.MAX_RUN_SEEDS, 0),
        ("eval", 0, seeding.EPISODES_PER_SEED),
    ],
)
def test_env_seed_rejects_out_of_range(args):
    with pytest.raises(ValueError):
        seeding.env_seed(*args)


def test_seed_global_is_reproducible():
    seeding.seed_global(42)
    a = np.random.rand(5)
    seeding.seed_global(42)
    assert np.array_equal(a, np.random.rand(5))


def test_agent_seed_deterministic_and_distinct():
    assert seeding.agent_seed(3) == seeding.agent_seed(3)
    assert seeding.agent_seed(3) != seeding.agent_seed(4)
