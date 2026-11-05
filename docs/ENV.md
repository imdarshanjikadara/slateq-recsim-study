# Environment

Verified on 2026-11-05 on: Windows 11 Home (native), Intel Core i5-1135G7 (4C/8T), 8 GB RAM, CPU only.

## Recipe

```bash
python -m pip install --user uv     # or: winget install astral-sh.uv
uv sync                             # reads pyproject.toml + uv.lock, creates .venv on Python 3.14
```

`uv.lock` pins the exact versions. Torch comes from the PyTorch CPU index (`[tool.uv.sources]` in
`pyproject.toml`), so no CUDA packages are pulled in.

| Package | Version (uv.lock) | Role |
|---|---|---|
| Python | 3.14.7 | interpreter (uv-managed) |
| numpy | 2.5.4 | RecSim env + our code |
| torch | 2.15.0+cpu | SlateQ port |
| gymnasium | 1.4.0 | `spaces` only, stands in for `gym.spaces` |
| gin-config | 0.5.0 | stands in for `gin.tf` (decorators) |
| absl-py | 2.5.1 | RecSim logging/flags |
| six | 1.17.0 | RecSim py2/3 compat |
| pandas / scipy / matplotlib / pyyaml | 3.1.1 / 1.18.1 / 3.11.2 / 6.0.3 | analysis, config |
| pytest / ruff | 9.2.0 / 0.17.3 | dev |
| GNU make | 4.4.1 | `winget install ezwinports.make` |

RecSim itself is not pip-installed: it is a git submodule at `third_party/recsim`
(commit 55e50e4be736d222ffe8c2477ed1981b40f91605), loaded through the import shim.

## Known pitfalls

1. **Import shim first.** Anything that imports `recsim` must install the shim first (Phase 0:
   `scripts/recon/_shim.py`; Phase 1 moves it into the package). Without it, `recsim.simulator.__init__`
   imports dopamine/TensorFlow and fails.
2. **Old RecSim API.** `env.reset()` returns the observation dict; `env.step(slate)` returns a 4-tuple
   `(obs, reward, done, info)`. Gymnasium's 5-tuple API is NOT used. Keep it that way.
3. **Global NumPy RNG.** RecSim's choice model (`choice_model.py:88`, `np.random.choice`) and interest
   update (`interest_evolution.py:541`, `np.random.rand`) use the global `np.random`, not the env seed.
   Seed `np.random` explicitly per episode, or trajectories are not reproducible
   (verified: `results/recon/env_probe.json`, key `determinism`).
4. **No bytecode in third_party.** The shim sets `sys.dont_write_bytecode = True` so no `__pycache__`
   is written into the read-only RecSim checkout.
5. **Threads.** One torch thread per process was faster than four for this small network
   (`results/recon/pilot_and_bench.json`, `torch_bench`). Parallelise with processes, 1 thread each.
6. **PATH after installing make/uv.** Open a new terminal after `winget install` so `make` is found.
7. **uv on this machine.** `uv venv --python 3.10` failed once with "Missing expected target directory
   for Python minor version link"; passing the interpreter path explicitly worked. Not seen with 3.14.
