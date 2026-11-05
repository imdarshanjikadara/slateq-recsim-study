"""Load RecSim's environment code from third_party/recsim on a modern stack (no TensorFlow).

RecSim (2020) imports `gym`, `gin.tf`, and TensorFlow/dopamine from some package __init__ files.
The environment, choice models, RandomAgent and GreedyPCTRAgent need only numpy + spaces, so:
  * `gym` / `gym.spaces` -> gymnasium (spaces only; RecSim keeps its OLD reset/step API),
  * `gin.tf` -> `gin` (only used for @gin.configurable),
  * `recsim.simulator`, `recsim.environments`, `recsim.agents` are pre-registered as bare
    packages so their TF-importing __init__ files never run.
third_party/recsim is never modified. Bytecode writing is disabled for the whole process so no
__pycache__ is written into the read-only checkout.

Call `install()` (idempotent) before importing anything from `recsim`.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

RECSIM_ROOT = Path(__file__).resolve().parents[2] / "third_party" / "recsim"
_BARE_PACKAGES = ("recsim.simulator", "recsim.environments", "recsim.agents")


def install() -> None:
    """Make `import recsim...` work without TensorFlow. Safe to call many times."""
    if getattr(sys.modules.get("recsim"), "_slateq_compat", False):
        return
    if not (RECSIM_ROOT / "recsim" / "__init__.py").is_file():
        raise FileNotFoundError(
            f"RecSim checkout not found at {RECSIM_ROOT}. Run: git submodule update --init"
        )
    sys.dont_write_bytecode = True
    import gin
    import gymnasium

    sys.modules.setdefault("gin.tf", gin)
    gym = types.ModuleType("gym")
    gym.spaces = gymnasium.spaces
    gym.Env = gymnasium.Env
    sys.modules.setdefault("gym", gym)
    sys.modules.setdefault("gym.spaces", gymnasium.spaces)
    root = str(RECSIM_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    for pkg in _BARE_PACKAGES:
        if pkg not in sys.modules:
            mod = types.ModuleType(pkg)
            mod.__path__ = [str(RECSIM_ROOT.joinpath(*pkg.split(".")))]
            sys.modules[pkg] = mod
    import recsim

    recsim._slateq_compat = True


def tensorflow_loaded() -> bool:
    return "tensorflow" in sys.modules
