# Discrepancy analysis (S6). No experiments were run.

## Labels

| Label | Meaning |
|---|---|
| **SUPPORTED** | Shown by our files, or by the paper text |
| **PLAUSIBLE** | Consistent with the evidence, but not tested |
| **SPECULATIVE** | A possibility with no direct evidence |

## (i) Our RQ3 cascade result vs SlateQ paper §7.3

| | SlateQ paper §7.3 (ie2019slateq, p. 25) | Ours, severe_cascade rung (NUMBERS.md RQ3) |
|---|---|---|
| Finding | SlateQ "continues to outperform MYOP" | SlateQ − learned-myopic = +0.22, CI [+0.08, +0.38]. One of 5 seeds at −0.01, so **no clear difference** under PROTOCOL 14.6. Post-hoc t-interval [−0.04, +0.47] |
| SARSA-TS relative to MYOP-TS | +1.96 % (computed by us from their table) | +0.20 % (relative to learned-myopic) |

**Different implementation and settings: context only. Not a comparison.**

### Setting differences that could explain it

| # | Difference | Paper | Ours | Label |
|---|---|---|---|---|
| 1 | **Cascade parameterisation and click rate** | Inspection β0·β^j with β0 = 1.0, β = 0.65. An inspected item is chosen with the conditional model's normalised probability; the null item is kept (§6.3, p. 21). Random's return barely changes: 159.2 → 159.9 (§7.1 vs §7.3 tables). | RecSim `ProportionalCascadeChoiceModel` with Interest Evolution defaults: attention 0.65, score_scaling 0.05. Per-position click probability ≤ 0.65 × 0.05 × 2 = 0.065 (`choice_model.py:168-187`, `interest_evolution.py:433-434`). Random's return falls 160.55 → 84.19, and sessions lengthen from 70.8 to 227.3 steps (NUMBERS.md RQ3 tables). | **SUPPORTED.** Our cascade is a far harsher environment, with very few clicks. Fewer clicks means fewer budget refunds from quality, so there is less room for the long-term lever. |
| 2 | Gap measured against what | MYOP-TS (learned, γ = 0) | Learned-myopic (learned, γ = 0) **and** oracle-myopic. Our oracle ranks by the proportional model under cascade (D11). | SUPPORTED that the definitions match for the learned baseline. Under cascade, oracle and learned-myopic are both about 107.8 (NUMBERS.md), so the choice of baseline does not explain the difference. |
| 3 | Agent variant | SARSA-TS, plus QL variants. The authors note QL and SARSA react differently to a wrong model (p. 25). | SARSA-TS only | SUPPORTED that the variant matches for the row compared (SARSA-TS). Other variants: not tested. |
| 4 | γ | 1 (p. 22) | 0.99 | PLAUSIBLE but minor. The effective horizon is already shortened by the zero no-click value (D6; TRAINING_NOTES). Under cascade, with most steps being no-clicks, this shortening is much stronger: each bootstrap is discounted by roughly γ·P(click) (TRAINING_NOTES mechanism). **This is likely a large part of the explanation, but it is not measured.** |
| 5 | No-click continuation value | The paper's decomposition includes the null item (§3-4); its implementation is not described. | 0 (RecSim reference, D6) | PLAUSIBLE. It interacts with #1 and #4: with very low click rates, the zero-value no-click dominates the targets. |
| 6 | Training budget | 300K steps (p. 23) | 300K steps (PROTOCOL 12.6) | SUPPORTED: the same. Not an explanation. |
| 7 | Sizes | m = 10, k = 3 | N = 10, k = 3 | SUPPORTED: the same. Not an explanation. |
| 8 | Seeds and statistics | Not reported; 5000 users, "within a 95% CI" | 5 seeds × 2400 paired episodes; pre-registered all-seeds-agree rule | SUPPORTED that our rule is stricter. The point estimate is positive, and the bootstrap CI excludes 0. "Not clear" comes from one seed at −0.01. A more lenient rule might call it positive but tiny. |
| 9 | Metric | Average return per session | Mean total reward (watch time) per session | SUPPORTED: equivalent in kind. Not an explanation. |
| 10 | What the training data looks like under cascade | not described | Learned agents train in the cascade environment, so their replay holds mostly no-click transitions, which are not trained on (D6) | PLAUSIBLE. Far fewer effective training updates per step than under the matched model. |
| 11 | Implementation (TF Dopamine vs PyTorch port) | TF | PyTorch, component-level equivalence only (OUR_SETUP_FACTS a) | SPECULATIVE as an explanation. We have no evidence of a port error, but no end-to-end cross-check either. |
| 12 | Simulator itself | §6 simulator: fixed document length 4, budget 200, no-click cost 0.5 (p. 21) | RecSim IE as used by us: fixed `video_length=4.0` (`UtilityModelVideoSampler`, `interest_evolution.py:208-215`), budget 200, no-click cost 0.5. *(Corrected 2026-11-13; an earlier version cited the unused mean-4.3 sampler.)* | SUPPORTED that these parameters match. Other details not checked. Not an explanation for the cascade difference. |

### Bottom line

- The two cascade experiments are **not the same experiment**. The most clearly supported difference is #1: our cascade cuts clicks drastically, while the paper's does not.
- Our result therefore says: under RecSim's default cascade parameters, the SlateQ-vs-myopic advantage is not clearly different from zero. It does **not** say the SlateQ paper's robustness finding fails.
- A cascade closer to §7.3 would be a diagnostic (PROPOSED_DIAGNOSTICS D-3). It was not run.

## (ii) Learning-rate confound, from existing data

See OUR_SETUP_FACTS (b).

- Tune stream, (10, 3), 2 seeds: at each matched learning rate (1e-4, 2.5e-4, 1e-3), SlateQ − learned-myopic = +1.59, +1.46, +1.91.
- All 9 SlateQ configs are above all 9 learned-myopic configs.
- **SUPPORTED** at (10, 3) on the tune stream: the gap does not depend on the learning-rate difference.
- **Not tested:** eval stream with matched learning rates; cells with N ≥ 20; whether learned-myopic at 1e-3 would degrade less at N = 80. → PROPOSED_DIAGNOSTICS D-1.

## (iii) Versus Pantea 2022: which γ, and does it matter?

- **Pantea** used **γ = 0.5** for both FullSlateQ and SlateQ and found both behave largely myopically. The thesis names other discount factors as future work (pantea2022thesis, E3, PDF p. 9).
- **We** used **γ = 0.99** for SlateQ and **γ = 0** for the learned-myopic control (OUR_SETUP_FACTS a). Our control isolates the horizon at the two ends that matter for RQ1.
- **Does it matter?**
  - **SUPPORTED:** with γ = 0.99 we see a clear, consistent advantage over γ = 0 (NUMBERS.md RQ1).
  - **PLAUSIBLE:** Pantea's myopic-looking behaviour at γ = 0.5 is consistent with a short effective horizon (1/(1−γ) = 2 steps).
  - Our port's effective horizon is also shorter than 0.99 suggests, because of the zero no-click value (D6).
  - **Not tested:** intermediate γ values in our setup → PROPOSED_DIAGNOSTICS D-2.
- Pantea's environment (custom preference dynamics, budget 500, k = 2) also differs, so the two results are not comparable.

## (iv) Why learned-myopic may fall below the oracle at large N

**SUPPORTED** facts (NUMBERS.md RQ2 secondary table):

- Learned-myopic − oracle is clearly negative at (20, 2), (40, 2), (40, 3), (80, 2), (80, 3) and (80, 5). It is −13.40 at (80, 3).
- Learned-myopic's clicked quality falls to −0.802 at (80, 3), against −0.602 for the oracle.
- Its sessions are shorter (64.0 vs 68.7).

**PLAUSIBLE** explanations (none tested):

1. **Fixed budget.** Training budget and hyperparameters were frozen at (10, 3) (PROTOCOL 12.6). With 80 candidates per step, a click model learned from 300K steps (of which only clicked steps are trained, D6) may be less accurate.
   - Literature: scaling item-wise Q evaluation and learning to large candidate pools is the stated motivation of Singha Roy et al. (singharoy2024news, E3) and of large-action-space work (dulacarnold2015large, E2).
   - This is support for the general difficulty only, not for our specific mechanism.
2. **Clickbait-like selection.** A learned γ = 0 model maximises predicted immediate reward. If its estimates are noisier with more candidates, top-k by score × Q picks more over-estimated items (a winner's-curse effect, more likely with more candidates). The falling clicked quality is consistent with this, but **not tested**.
3. **Learning rate.** 2.5e-4 was tuned at (10, 3). **Not tested** at N = 80 (D-1).

**Implication for reporting:**

- The headline for RQ2 should be the **oracle comparison**: SlateQ − oracle is +27.17 at (80, 3) and clear in all 14 grid cells (NUMBERS.md).
- The primary (learned-myopic) gap at large N mixes "SlateQ gets better" with "the baseline gets worse" (POSITIONING A6/A7).
