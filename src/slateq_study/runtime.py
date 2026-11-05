"""Per-process runtime setup. The ONE place that caps threads (replaces the old TF-era tf_compat).

Call `configure_process()` at the top of every entrypoint, before torch does any work.
Phase 0 measured 1 torch thread faster than 4 for our small network
(results/recon/pilot_and_bench.json), so we parallelise with processes, not threads.
"""

from __future__ import annotations

import os

_THREAD_ENV_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
_configured = False


def configure_process(threads: int = 1) -> None:
    """Idempotent: cap BLAS/torch threads and install the RecSim import shim."""
    global _configured
    if _configured:
        return
    for var in _THREAD_ENV_VARS:
        os.environ.setdefault(var, str(threads))
    import torch

    torch.set_num_threads(threads)
    try:
        torch.set_num_interop_threads(threads)
    except RuntimeError:  # can only be set once per process, before parallel work starts
        pass
    from slateq_study import recsim_compat

    recsim_compat.install()
    _configured = True
