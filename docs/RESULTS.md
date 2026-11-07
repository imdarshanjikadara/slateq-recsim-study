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

## Threats and caveats (see also README "Limitations")

- Simulated users only; 5 run seeds; one training budget.
- SlateQ is a PyTorch port (D3).
- No-click continuation value is 0 (D6).
- Learning curves (F1) are flat after the first 50K steps for both agents. The gap is established early in training and is not a late-training effect.
- The earlier observation that an untrained network sometimes scores well (TRAINING_NOTES) reappears here. At step 0, the 200-episode tune-stream score ranges from 125.80 to 168.07 across seeds (`results/rq2/curves.csv`, train_steps = 0). The score depends strongly on the random initialisation, and on one seed it is close to the trained level. The mean over seeds (F1) still sits well below every later checkpoint. The study's conclusions rest on the trained agents' evaluation, not on this.
