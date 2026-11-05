# Deviations from the approved proposal

Every change relative to `docs/proposal.md` is logged here with date, reason and impact.
The report's "Deviations" section is built from this file.

| # | Date | Deviation | Reason | Impact on the science |
|---|---|---|---|---|
| D1 | 2026-11-05 | **Modern software stack** (Python 3.14, numpy 2, PyTorch, gymnasium) instead of RecSim's original TF1 / dopamine / gym stack. | Instructed by the student: use current, lightweight library versions. RecSim's original stack does not import on current TensorFlow. | Environment unchanged (see D2). Learning agents are re-implemented (see D3). |
| D2 | 2026-11-05 | RecSim's environment is loaded from `third_party/recsim` (unmodified) through an **import shim** (`gym` → `gymnasium.spaces`, `gin.tf` → `gin`, TF-importing package `__init__` files bypassed). | Lets us keep RecSim's original Interest Evolution user model, reward, choice model and dynamics without TensorFlow. | None intended: the simulator code is RecSim's own. Verified in Phase 0 (`results/recon/env_probe.json`). |
| D3 | 2026-11-05 | **SlateQ is our own PyTorch port** of RecSim's `SlateDecompQAgent` (top-k selection, SARSA target, same network shape and scoring functions). The proposal says "SlateQ agent from RecSim". | RecSim's agent depends on TF1 + dopamine (excluded by D1). | We cannot run RecSim's TF agent side by side. Mitigation: unit tests against RecSim's NumPy `score_documents` and against the paper's equations (Phase 3). Hyperparameter defaults are taken from the reference where they are readable in source; the rest are documented as our choices. |
| D4 | 2026-11-05 | Naming correction: the proposal's "Full SlateQ Agent" means the **decomposed** SlateQ (`SlateDecompQAgent`). RecSim's `FullSlateQAgent` is the non-decomposed baseline. | Found while reading the RecSim source. | Wording only; the research questions are unchanged. |
| D5 | 2026-11-05 | "Catalog size" is operationalised as RecSim's `num_candidates` (N), the candidate set **redrawn every step** (`resample_documents=True`). | RecSim has no fixed catalogue in Interest Evolution: documents are sampled fresh each step. | Must be stated in the report. Confirmed by the student on 2026-11-05 (RECON Q1). |
| D6 | 2026-11-05 | The SlateQ port follows the **RecSim reference's null-item handling**: the no-click option enters choice probabilities, but its continuation value Q̄(s,⊥) is 0, and only clicked transitions are trained. The paper's decomposition (§3–4) includes ⊥ in the slate sum. | Faithful to the reference implementation the proposal names; decided by the student (RECON Q2). | Targets omit the value of continuing after a no-click. Stated as a limitation in the report. |

Planned additions that still need logging when they are implemented: learned-myopic ablation (gamma = 0); FullSlateQ at small sizes.
