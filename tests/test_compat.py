"""Import shim: works in any import order, idempotent, never loads TensorFlow, never writes bytecode
into third_party. Each scenario runs in a fresh interpreter so import state cannot leak."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

SCENARIOS = {
    "compat_then_env": """
from slateq_study import recsim_compat
recsim_compat.install()
from recsim.environments import interest_evolution
""",
    "twice": """
from slateq_study import recsim_compat
recsim_compat.install(); recsim_compat.install()
from recsim.agents import random_agent, greedy_pctr_agent
""",
    "torch_first": """
import torch
from slateq_study import runtime
runtime.configure_process()
runtime.configure_process()
from recsim.environments import interest_evolution
""",
    "envs_module_first": """
from slateq_study.config import EnvConfig
from slateq_study.envs import make_env
env = make_env(EnvConfig(), seed=0)
obs = env.reset()
assert set(obs) == {"user", "doc", "response"}
""",
}


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_import_orders(name):
    code = SCENARIOS[name] + "\nimport sys\nassert 'tensorflow' not in sys.modules, 'TF loaded'\n"
    proc = subprocess.run([sys.executable, "-c", code], cwd=REPO, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[-2000:]


def test_no_bytecode_written_into_third_party():
    pycache = list((REPO / "third_party" / "recsim").rglob("__pycache__"))
    assert not pycache, f"__pycache__ found in read-only RecSim checkout: {pycache[:3]}"
