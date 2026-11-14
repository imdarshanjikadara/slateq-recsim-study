# Results: what the data shows and does not show

Every number below is copied from [`NUMBERS.md`](NUMBERS.md), which is generated from `results/rq2` and
`results/rq3` by `scripts/make_numbers.py`. Verdicts use the pre-registered rule (PROTOCOL 14.6):
"clear" only if the seed-bootstrap 95% CI excludes 0 **and** all 5 seeds have the same sign.
Runs: 300/300 (RQ1/RQ2) and 60/60 (RQ3) finished with status ok; no run was dropped or repeated.

## RQ1: does SlateQ beat a myopic recommender? (N=10, k=3)

**Shows.**
- SlateQ − learned-myopic = **+1.70** watch time per session, 95% CI [+1.54, +1.85], positive on all 5 seeds: a clear difference by the pre-registered rule (F2).
- SlateQ is also clearly above the privileged oracle-myopic (+1.60, CI [+1.46, +1.75]).
- Learned-myopic and oracle-myopic are indistinguishable (−0.09, CI [−0.24, +0.08]). The learned click model is therefore as good as the oracle's here, so the primary gap is about the planning horizon, not a weak baseline.
- Mechanism: SlateQ's clicked items have higher (hidden) quality (−0.583 vs −0.625 for learned-myopic). Its sessions are slightly longer (60.4 vs 59.8 steps) with slightly more clicks (42.9 vs 42.4). This fits the environment's design: clicked quality refunds time budget.

**Does not show.**
- The effect is small in relative terms: +1.70 on a base of 167.50, about 1%.
- Random has the *longest* sessions (70.8 steps) but the lowest reward (160.55). Session length alone is not engagement: random shows more items users skip.
- The pre-registered case-study user (seed 0, episode 0; F6 and demo) happens to be one where random earns most. It is one user, chosen by rule before the results, and is not representative. The averages above are the evidence.

## RQ2: how does the gap change with catalog size N and slate size k?

**Shows (F3, F4).**
- The primary gap is clearly positive in **14 of 14** grid cells.
- It grows steeply with N at every k:
  - k=3: +0.18 (N=5), +1.70 (N=10), +5.07 (N=20), +14.66 (N=40), +40.57 (N=80).
- At fixed N it shrinks as k grows:
  - N=80: +41.10 (k=2), +40.57 (k=3), +27.46 (k=5).
  - N=40: +18.51, +14.66, +9.03.
- The degenerate control (N=5, k=5: every candidate is shown, so the policy has no choice) gives −0.01, CI [−0.06, +0.02]. No clear difference, as it must be; this rules out an evaluation artefact.
- **Two causes contribute at large N.** The secondary comparisons (NUMBERS.md, "RQ2: secondary comparisons") separate them:
  1. SlateQ improves. SlateQ − oracle-myopic is clearly positive and grows from +1.60 (N=10, k=3) to +27.17 (N=80, k=3). SlateQ's clicked quality rises from −0.583 to −0.186 and its sessions lengthen from 60.4 to 78.3 steps. With more candidates there are more high-quality items to choose from, and only the long-horizon agent selects for them.
  2. Learned-myopic weakens. Learned-myopic − oracle-myopic becomes clearly negative at large N (−13.40 at N=80, k=3), and its clicked quality falls to −0.802. Part of the primary gap at N ≥ 40 is therefore learned-myopic doing worse than a perfect click-maximiser, not only SlateQ doing better.
- Read honestly, the planning gain is best measured against the oracle: +27.17 at N=80, k=3, still large and clear.

**Does not show.**
- That the trend continues beyond N=80, or holds at the same training budget for larger N. The budget was frozen once at N=10, k=3 (PROTOCOL 12.6).
- Why learned-myopic degrades at large N. This is plausibly harder click-model learning with more candidates at a fixed budget, but this study did not test that.
- Anything about a fixed catalogue. "Catalog size" here is the number of candidates resampled each step (DEVIATIONS D5).

## RQ3: sensitivity to a misspecified user choice model (N=10, k=3)

**Shows (F7).**

| Rung | Gap | 95% CI | Verdict |
|---|---|---|---|
| matched | +1.70 | [+1.54, +1.85] | clear |
| mild (no-click mass 3) | +1.12 | [+1.02, +1.25] | clear |
| moderate (logit) | +1.62 | [+1.41, +1.78] | clear |
| severe (cascade) | +0.22 | [+0.08, +0.38] | no clear difference: seed 1 is −0.01, so the all-seeds-agree condition fails although the CI excludes 0 |

- The advantage survives mild and moderate misspecification and largely disappears under the position-dependent cascade model.
- Under cascade all policies earn less (SlateQ 108.00, random 84.19), and sessions are much longer (about 181 steps for the learned agents).

**Does not show.**
- Which feature of the cascade model removes the advantage: position effects, the attention parameters, or the longer sessions. Only one cascade setting was run.
- Whether retraining with a matching choice model would restore the gap. Only the environment's user model was changed; the agents' assumed model stayed proportional by design.

## Phase 6b addendum: follow-up experiments E1–E5 (exploratory)

These experiments were **registered after the Phase 6 results above were seen** (PROTOCOL §16, committed before any Phase 6b run; DEVIATIONS D13–D16). They explain and stress-test the main results and do not replace them. The rules are unchanged: frozen hyperparameters, 5 seeds, 2400 evaluation episodes with common random numbers, and the §14.6 verdict rule. Many comparisons are made and no multiple-comparison correction is applied (§16.8), so isolated verdicts should be read with care. Runs: 80/80 finished with status ok (50 E1/E2, 10 E3, 20 E4); none was dropped or repeated. Numbers: NUMBERS.md, section "Phase 6b". Figures: F9 (horizon), F10 (clicks vs watch time), F11 (follow-up gaps).

### E1: is the gap a learning-rate artefact? (matched learning rates)

**Shows.**
- At (10, 3): SlateQ − learned-myopic is +1.53 [+1.38, +1.71] with both agents at lr 1e-3, and +1.53 [+1.30, +1.78] with both at lr 2.5e-4. Both are clear.
- At (80, 3): +36.58 [+31.18, +41.32] (both lr 1e-3) and +49.64 [+44.79, +55.05] (both lr 2.5e-4). Both are clear.
- By the reading fixed in §16.3, the SlateQ advantage in both cells **does not depend on the learning-rate difference**.
- Learned-myopic at lr 1e-3 is still clearly below the oracle at (80, 3) (−9.41 [−11.59, −7.53]). The learning rate does not explain its shortfall there.

**Does not show.**
- That the *size* of the gap is independent of the learning rate. At (80, 3) it varies with the learning rate (+36.58, +40.57 in RQ2, +49.64). Only the direction is robust.

### E2: how much planning is needed? (γ = 0, 0.5, 0.9, 0.95, 0.99, all at lr 1e-3)

**Shows (F9).**
- Every γ > 0 is clearly above the oracle-myopic in both cells.
  - (10, 3): +0.72 (γ 0.5), +1.03 (0.9), +1.63 (0.95), +1.60 (0.99).
  - (80, 3): +7.70, +24.46, +27.95, +27.17.
- The gain rises with γ and levels off between 0.95 and 0.99 in both cells.
- At (80, 3), γ = 0.5 already improves on γ = 0 clearly (+17.11 [+16.13, +18.18]), but recovers much less than γ ≥ 0.9.
- One comparison is not clear: γ 0.9 − γ 0 at (10, 3) (+0.95 [+0.40, +1.32]; seed 4 is −0.11).

**Does not show.**
- A "best γ". Five points are described from their CIs only. Nothing between or beyond them was run, and no curve is fitted (§16.4).

### E3: is learned-myopic under-trained at N = 80? (600K instead of 300K steps)

**Shows.**
- Learned-myopic with 600K steps − oracle-myopic = −6.23 [−10.12, −1.80], "no clear difference" by §14.6. The 300K value was −13.40, "first lower (clear)". By the reading fixed in §16.5, the shortfall is **consistent with under-training**.
- The change of verdict is weak. The CI still excludes 0, and 4 of 5 seeds are negative; only seed 1 is positive (+2.59). The direct comparison, learned-myopic 600K − 300K, is +7.17 [+0.35, +15.39], also "no clear difference" (seed 0 is −3.63).
- SlateQ does not change with more training: 600K − 300K = +0.41 [−1.52, +2.36].
- SlateQ − learned-myopic at 600K: +33.81 [+29.20, +38.41]. SlateQ − oracle at 600K: +27.58 [+22.31, +32.85]. Both are clear, so the main RQ2 result at (80, 3) holds at twice the budget.

**Does not show.**
- That under-training is the whole explanation, or a trend. Two budget points only.

### E4: the SlateQ paper's cascade (N = 10, k = 3)

**Shows.**
- SlateQ − learned-myopic = +2.54 [+2.16, +2.96], all 5 seeds positive: **clear**. SlateQ − oracle-myopic = +2.42 [+2.11, +2.76], also clear.
- Compared with RecSim's cascade (RQ3 severe rung, +0.22, no clear difference), the advantage is clear again under the paper's cascade.
- Why the two differ: random's watch time falls from 160.55 (matched) to 84.19 under RecSim's cascade, but only to 144.66 under the paper's cascade. Under the paper's cascade, clicks stay common enough for quality to extend sessions.
- What this supports: the RQ3 cascade result depends on the cascade's parameters. Under a cascade built from the paper's description, our port shows the same direction as the paper's robustness result. This is a different implementation: context only, not a numerical replication of the paper's §7.3.

**Does not show.**
- That SlateQ is robust to any wrong choice model. Two cascades are two data points.

### E5: does the click-maximiser get more clicks but less watch time?

All 19 conditions are covered (15 RQ2 cells including the control, the 3 RQ3 rungs, E4). Each is the myopic agent minus SlateQ (F10).

**Shows.**
- **Click rate (clicks per recommendation):** no clear difference in 18 of 19, for both oracle-myopic and learned-myopic. Every click-rate difference is below 0.001 in absolute size. At (80, 3), for example, all three agents click at 0.743.
- **The registered pattern "more clicks, less watch time" appears in 1 of 19 conditions only:** oracle-myopic at (40, 2), and learned-myopic at (5, 3).
- **The common pattern (16 of 19)** is no clear difference in clicks per recommendation, but less watch time per session.
- **Watch time per session:** the myopic agent is clearly lower in 17 of 19. The exceptions are the k = N control and RecSim's cascade.
- **Clicks per session:** the myopic agent is clearly lower in 17 of 19 (oracle) and 18 of 19 (learned-myopic). At (80, 3) the gap is −7.11 [−8.29, −5.72] for the oracle: 51.1 vs 58.2 clicks per session.
- **Watch time per click:** the myopic agent is clearly *higher* in 10 of 19, by a very small amount (3.914 vs 3.903 at (80, 3)). We did not analyse why.
- **Plain reading:** in this simulator, the click-maximiser and SlateQ are equally good at getting the next click. SlateQ's advantage comes from choosing **equally clickable but higher-quality** items, which make sessions last longer. The cost of click-maximising shows up as **shorter sessions** (fewer clicks and less watch time in total), not as fewer clicks per recommendation.

**Does not show.**
- That the click-maximiser gets *more* clicks. The registered hypothesis was mostly not observed.
- Anything about a real platform. In RecSim every video has length 4, so watch time per click can hardly differ by design, whereas on real platforms it varies widely.

## Threats and caveats (see also README "Limitations")

- Simulated users only; 5 run seeds; one training budget.
- SlateQ is a PyTorch port (D3).
- No-click continuation value is 0 (D6).
- Learning curves (F1) are flat after the first 50K steps for both agents. The gap is established early in training and is not a late-training effect.
- The earlier observation that an untrained network sometimes scores well (TRAINING_NOTES) reappears here. At step 0, the 200-episode tune-stream score ranges from 125.80 to 168.07 across seeds (`results/rq2/curves.csv`, train_steps = 0). The score depends strongly on the random initialisation, and on one seed it is close to the trained level. The mean over seeds (F1) still sits well below every later checkpoint. The study's conclusions rest on the trained agents' evaluation, not on this.
