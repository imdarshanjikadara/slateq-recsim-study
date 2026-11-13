# Proposed diagnostics (S6). NONE HAS BEEN RUN.

These are cheap, in-scope checks suggested by the literature review. Running any of them is the student's decision.

- Each would be **post-hoc and exploratory**, logged in DEVIATIONS.md, and reported separately from the pre-registered results.
- None would change an existing verdict.
- Cost is from logged wall-clock: mean `wall_clock_sec` per run in `results/rq2/runs.csv` and `results/rq3/runs.csv`. Wall time assumes 4 workers.

**Not proposed:** a side-by-side cross-check against RecSim's TF1 reference agent. It needs the TF1 + Dopamine stack excluded by D1, so it is not "cheap". Port evidence stays component-level (OUR_SETUP_FACTS a); this is stated as a limitation instead.

## D-1. Learning-rate swap on the primary cell (and the largest cell)

**Question:** does the SlateQ − learned-myopic gap depend on the agents having different learning rates? And does learned-myopic degrade less at N = 80 with a larger learning rate?

**Runs:**

| Part | Runs | Cost |
|---|---|---|
| a | (10, 3): SlateQ at lr 2.5e-4 (learned-myopic's rate), seeds 0-4. Learned-myopic at 2.5e-4 already exists, so this gives a matched-lr eval-stream comparison. | 5 runs × ~872 s ≈ 1.2 CPU-h ≈ **20 min** wall |
| b (optional) | (80, 3): learned-myopic at lr 1e-3, seeds 0-4 | 5 × ~2172 s ≈ 3.0 CPU-h ≈ **50 min** wall |

**Risk:**

- Low for (a): it only tests robustness of an existing claim.
- (b) could show part of the RQ2 primary gap is tuning-dependent. That would be an honest refinement, and the oracle-based headline is unaffected.

**DEVIATIONS entry (if run):** "D13 (post-hoc diagnostic): matched-learning-rate check of the primary gap; not part of the pre-registered analysis."

## D-2. γ sensitivity on the primary cell

**Question:** how does the gap change for γ between 0 and 0.99? This relates to Pantea 2022's γ = 0.5 finding and to our zero no-click value shortening the horizon.

**Runs:** (10, 3), SlateQ with γ ∈ {0.5, 0.9}, frozen SlateQ hyperparameters, seeds 0-4.

**Cost:** 10 runs × ~872 s ≈ 2.4 CPU-h ≈ **40 min** wall.

**Risk:** low. Exploratory; reported as a curve with no verdict.

**DEVIATIONS entry:** "D14 (post-hoc diagnostic): γ sensitivity at (10, 3)."

## D-3. A second cascade setting closer to the SlateQ paper's §7.3

**Question:** does SlateQ's advantage survive under a cascade with a click rate comparable to the matched model, as in the paper (where Random's return barely changed)? Or is the RQ3 null specific to RecSim's low-click default cascade?

**Runs:** (10, 3), all 4 agents, seeds 0-4. RecSim `ProportionalCascadeChoiceModel` with attention 0.65 and a larger score_scaling.

- **The value must be chosen before running, by a stated rule.** Suggested rule: the largest value allowed by RecSim's assertion (score_scaling × max score ≤ 1, i.e. 0.5).
- Alternative: an exponential cascade.
- **This choice affects the science, so it is the student's call.**

**Cost:** learned 10 runs × ~915 s + baselines 10 runs × ~170 s ≈ 3.0 CPU-h ≈ **50 min** wall.

**Risk:**

- Medium. Adding a condition after seeing results is a forking-paths risk.
- It must be labelled exploratory and must not replace the pre-registered severe rung.
- It changes no RQ3 verdict.

**DEVIATIONS entry:** "D15 (post-hoc, exploratory): additional cascade setting closer to Ie et al. 2019 §7.3; pre-registered RQ3 ladder unchanged."

## Recommendation

**If time allows, run D-1(a) first.**

- It is the cheapest (~20 min).
- It directly answers the most likely examiner question ("different learning rates?") with eval-stream data.

**D-3 is the most informative scientifically** but needs a decision on the cascade parameter.

**D-2 is optional.**
