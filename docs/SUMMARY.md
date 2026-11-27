# Summary

**Question.** A recommender shows a few videos at a time (a *slate*). Does one that plans for the whole session
(SlateQ, Ie et al. 2019) keep simulated viewers watching longer than one that chases the next click?

**Setting.** RecSim Interest Evolution, simulated viewers only:
- Each step, the recommender shows k of N fresh candidate videos, and the viewer watches at most one.
- Reward = watch time. Watching a high-quality video gives time budget back, so the session lasts longer.

**Recommenders compared.**

| Name | What it is |
|---|---|
| SlateQ | our PyTorch port of RecSim's SlateQ agent, γ = 0.99 |
| learned myopic | the same agent with γ = 0 (the main comparison) |
| oracle myopic | given the true click model; the best possible click-chaser |
| random | shows random videos |

**Method** (rules fixed before any run, [PROTOCOL](PROTOCOL.md)):
- 5 run seeds × 2400 evaluation viewers; every recommender sees the same viewers.
- 95% bootstrap confidence intervals over seeds.
- A difference is called *clear* only if the interval excludes 0 **and** all 5 seeds agree.

## Key results

All numbers are copied from [NUMBERS.md](NUMBERS.md), which is generated from `results/`. Watch time per session, SlateQ minus the other recommender:

| Question | Result | Verdict |
|---|---|---|
| RQ1: N = 10, k = 3, vs learned myopic | +1.70 [+1.54, +1.85], about 1% | clear |
| RQ2: all 14 (N, k) cells | positive in every cell; at k = 3: +0.18 (N = 5) up to +40.57 (N = 80) | clear in 14 of 14 |
| RQ2: N = 80, k = 3, vs oracle myopic | +27.17 [+21.79, +31.75] | clear |
| RQ2: control N = k = 5 (no choice possible) | −0.01 [−0.06, +0.02] | no clear difference |
| RQ3: users skip more | +1.12 [+1.02, +1.25] | clear |
| RQ3: different choice formula (logit) | +1.62 [+1.41, +1.78] | clear |
| RQ3: RecSim cascade | +0.22 [+0.08, +0.38] | no clear difference |

**Follow-ups E1–E5** (exploratory: planned after the results above, registered before their own runs):
- **E1:** with both agents at the same learning rate, SlateQ still wins (+1.53 at N = 10 for both rates).
- **E2:** more planning helps; the gain levels off between γ = 0.95 and 0.99.
- **E3:** twice the training narrows the myopic agent's shortfall at N = 80; SlateQ − oracle stays +27.58.
- **E4:** under the SlateQ paper's own cascade, SlateQ wins clearly (+2.54).
- **E5:** the click-chaser gets the same click rate (0.743 at N = 80) but shorter sessions (51.1 vs 58.2 videos watched).

## What this does not show

- Anything about real platforms: the viewers are simulated.
- The trend beyond N = 80.
- Behaviour under other cascade settings.
- An end-to-end match with Google's original TensorFlow agent (our port is checked by tests instead).

## Where to look

| For | File |
|---|---|
| Every number | [NUMBERS.md](NUMBERS.md) |
| What each result shows and does not show | [RESULTS.md](RESULTS.md) |
| Plain-language walkthrough | [EXPLAINER.md](EXPLAINER.md) |
| Rules and changes | [PROTOCOL.md](PROTOCOL.md), [DEVIATIONS.md](DEVIATIONS.md) |
| Figures | [`results/figures/`](../results/figures/) |
| Interactive replay | [SlateStream](https://slatestream.vercel.app) |
