"""Environment factory: RecSim Interest Evolution, unmodified, behind the import shim.

Mapping to the proposal: "catalog size" = num_candidates (N, redrawn every step when
resample_documents=True; DEVIATIONS D5); "slate size" = slate_size (k).
Phase 2 adds the choice-model parameter (RQ3) and documents the full spec.
"""

from __future__ import annotations

from typing import Any

from slateq_study import recsim_compat
from slateq_study.config import EnvConfig


def make_env(env_cfg: EnvConfig, seed: int) -> Any:
    """Build a RecSim gym env. OLD API: reset() -> obs dict; step(slate) -> (obs, r, done, info).

    `seed` seeds RecSim's user and document samplers. RecSim's choice model and interest updates
    also draw from the GLOBAL np.random, which the harness seeds per episode (seeding.seed_global).
    """
    env_cfg.validate()
    recsim_compat.install()
    from recsim.environments import interest_evolution

    return interest_evolution.create_environment(
        {
            "num_candidates": env_cfg.num_candidates,
            "slate_size": env_cfg.slate_size,
            "resample_documents": env_cfg.resample_documents,
            "seed": int(seed),
        }
    )
