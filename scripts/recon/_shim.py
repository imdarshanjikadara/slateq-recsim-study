"""Phase 0 import shim: load RecSim's environment code from third_party/recsim on a modern stack.

RecSim (2020) imports `gym`, `gin.tf`, and TensorFlow/dopamine from some package __init__ files.
The environment, choice models, RandomAgent and GreedyPCTRAgent only need numpy + spaces, so we:
  * map `gym` / `gym.spaces` -> gymnasium (spaces only; RecSim keeps its OLD reset/step API),
  * map `gin.tf` -> `gin` (only used for @gin.configurable),
  * pre-register `recsim.simulator`, `recsim.environments`, `recsim.agents` as bare packages so their
    __init__ files (which import TF/dopamine runners) are never executed.
third_party/recsim is never modified; bytecode writing is disabled so no __pycache__ lands there.
Phase 1 will promote this into src/slateq_study/recsim_compat.py.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

RECSIM_ROOT = Path(__file__).resolve().parents[2] / "third_party" / "recsim"


def install() -> None:
    if "recsim.environments.interest_evolution" in sys.modules:
        return
    sys.dont_write_bytecode = True
    import gin
    import gymnasium

    sys.modules.setdefault("gin.tf", gin)
    gym = types.ModuleType("gym")
    gym.spaces = gymnasium.spaces
    gym.Env = gymnasium.Env
    sys.modules.setdefault("gym", gym)
    sys.modules.setdefault("gym.spaces", gymnasium.spaces)
    sys.path.insert(0, str(RECSIM_ROOT))
    for pkg in ("recsim.simulator", "recsim.environments", "recsim.agents"):
        mod = types.ModuleType(pkg)
        mod.__path__ = [os.path.join(RECSIM_ROOT, *pkg.split("."))]
        sys.modules.setdefault(pkg, mod)


install()
