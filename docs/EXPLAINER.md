# Explainer: the whole project in plain language

This file walks through the project from start to finish: what the simulator does, what each agent is, how a number is produced, every experiment and why it was run, and what each result does and does not mean. Every number quoted here is copied from `docs/NUMBERS.md`, which is generated from `results/`. If the two ever disagree, NUMBERS.md is right.

## 1. The question in one paragraph

A recommender that only predicts the **next** click (a *myopic* recommender) picks whatever the user is most likely to click right now. A recommender that **plans ahead** can sometimes show something slightly less clickable that keeps the user around longer. SlateQ (Ie et al. 2019) is a reinforcement-learning method that plans ahead while still choosing a whole *slate* of k items at once. We ask: in Google's RecSim simulator, how much longer do users watch under SlateQ than under myopic recommenders (RQ1)? How does that change with the number of candidates N and the slate size k (RQ2)? And how much does it depend on SlateQ's assumption about how users choose (RQ3)?

## 2. The simulator (RecSim Interest Evolution)

- **User.** Each simulated user has hidden interests in 20 topics (numbers between -1 and 1) and a **time budget** of 200.
- **Each step.** The system draws N fresh candidate videos. Each video has one topic and a hidden **quality**. Quality depends on the topic: 14 of the 20 topics have a negative average quality ("trashy") and 6 a positive one ("nutritious"). The recommender shows k of the N videos (the slate).
- **Choice.** The user clicks at most one item, more likely the ones whose topic matches their interests. The probability rule is the **choice model**. By default it is "proportional": score = interest in the topic + 1, with a fixed score of 2 for "no click".
- **Reward.** If the user clicks, the reward is the **watch time**: every video is 4 long, so a click is worth 4 (less only if the budget is about to run out). No click: reward 0, and the budget drops by 0.5.
- **The trade-off.** Watching uses up budget, but a **high-quality** video gives part of it back, and a low-quality one takes extra. So a recommender that shows good-quality videos makes sessions longer, and total watch time per session grows. Interest drives clicks; quality drives how long the session lasts. A video from a topic the user likes but with low quality is "clickbait" in this simulator: likely to be clicked, bad for the session. That gap between "what gets clicked" and "what is good for the session" is the reason long-term planning can help.
- **The session ends** when the budget reaches 0. Total reward = total watch time in the session. This is the main metric.

## 3. The four agents

| Agent | What it does | Why it is in the study |
|---|---|---|
| **random** | Shows k random candidates | Floor: any learning should beat it |
| **oracle-myopic** | Is given the user's true hidden interests and the true choice model, and shows the k most clickable items | The best possible **click-maximiser**. It cannot be badly trained, so beating it means planning helps beyond perfect click prediction. Not a realistic system: it is privileged. |
| **learned-myopic** | Our SlateQ code with γ = 0: it learns to predict the immediate reward only | The fair myopic baseline: same network, same data, same training budget as SlateQ |
| **SlateQ** | Our SlateQ code with γ = 0.99: it learns long-term value | The method under study |

**How SlateQ chooses a slate.** It learns a value Q(user, item) for each item: "how much watch time from now on if the user clicks this item". It multiplies that by how likely the user is to click the item (the choice model's score) and shows the top k. Learning one value per *item* instead of one per *slate* is the "decomposition" that makes slates tractable.

**γ (gamma), the discount.** γ = 0 means "only the next reward matters". γ = 0.99 means "rewards 100 steps away still count a lot". The only conceptual difference between learned-myopic and SlateQ is γ. In practice each also has its own tuned learning rate (see E1).

## 4. How one number is produced

1. **Training** (learned agents only): 300,000 simulator steps on *training* users.
2. **Tuning** was done once, in Phase 3, on separate *tuning* users. Each learned agent got the same grid of 9 settings and kept its best. Results: SlateQ lr 1e-3, learned-myopic lr 2.5e-4. Frozen since then.
3. **Evaluation:** 2400 sessions on *evaluation* users that were never used for training or tuning. The **same 2400 users** are given to every agent (common random numbers), so differences come from the agents, not from luck in the users.
4. **Seeds:** all of this is repeated with 5 run seeds (different network starts, different training users).
5. **Comparison:** for each seed, mean watch time of agent A minus agent B. That gives 5 differences. We report their mean and a 95% bootstrap confidence interval over the 5 seeds.
6. **Verdict rule (fixed in advance, PROTOCOL 14.6):** "clear" only if the CI excludes 0 **and** all 5 seeds have the same sign. Otherwise "no clear difference". With only 5 seeds we never say "statistically significant".

Code path: `configs/experiments/*.yaml` → `scripts/sweep.py` (one process per agent, cell and seed) → `scripts/run_one.py` → `results/raw/...` (not committed) → `scripts/analyze.py` or `scripts/phase6b_analyze.py` → small tables in `results/` → `scripts/make_numbers.py` (NUMBERS.md), `scripts/figures.py`, `scripts/build_web.py`.

## 5. Why you can trust (and where you should doubt) the SlateQ code

We did not run Google's original TensorFlow agent next to ours (that software stack was excluded). Instead:

- Unit tests check each formula against RecSim's own code or a hand calculation (scores, top-k rule, SARSA target, exploration schedule).
- With γ = 0, our agent learns almost exactly what the privileged oracle does (97 % of the oracle's gain over random in Phase 3; "no clear difference" from the oracle in 7 of 8 small cells).
- Q-values have the size theory predicts, and saved models replay the recorded results exactly.

Remaining doubt: small differences from the TensorFlow agent (optimiser details, exploration schedule) could shift absolute numbers. Details: `docs/literature/OUR_SETUP_FACTS.md`.

## 6. The main experiments (Phase 6, pre-registered before any result)

### RQ1: does SlateQ beat a myopic recommender? (N = 10, k = 3)

- **Why this cell:** it is the setting of the SlateQ paper's own simulation (§7.1). So RQ1 is a **replication**: the same question asked again with independent code and stricter statistics.
- **Result:** SlateQ − learned-myopic = +1.70 watch time per session, 95% CI [+1.54, +1.85], positive on all 5 seeds: **clear**. SlateQ is also clearly above the oracle-myopic (+1.60), and learned-myopic and the oracle show no clear difference (−0.09).
- **What it means:** at this size, planning ahead gives a small but consistent gain (every seed agrees).
- **What it does not mean:** that SlateQ is "much better", or anything about real users. The gain is about 1 %.

### RQ2: how does the gap change with N and k?

- **Why:** the SlateQ paper used one size only. Real systems choose from far more candidates. With more candidates there are more good-quality *and* more clickbait videos to choose between, so planning has more to gain.
- **Result:** The gap is clear in **14 of 14** cells. At k = 3 it grows from +0.18 (N = 5) to +1.70 (N = 10), +5.07 (N = 20), +14.66 (N = 40) and +40.57 (N = 80). At fixed N it shrinks as k grows (N = 80: +41.10, +40.57, +27.46 for k = 2, 3, 5). The k = N control (no choice possible) gives −0.01, no clear difference, as it must.
- **Two readings of the large-N gap:** SlateQ gets better relative to the perfect click-maximiser (oracle), **and** the learned myopic baseline falls behind the oracle. That is why the oracle comparison is the headline. E1 and E3 below test two explanations for the baseline falling behind.

### RQ3: what if users do not choose the way SlateQ assumes?

- **Why:** SlateQ uses a choice model inside its decisions. Real users never follow it exactly.
- **The ladder:** more skipping (mild) → a different formula (logit, moderate) → RecSim's position-based cascade (severe), where clicks become rare.
- **Result:** matched +1.70 (clear), mild +1.12 (clear), moderate +1.62 (clear), severe cascade +0.22 (no clear difference: one seed is −0.01).
- **What it means:** the advantage survives mild and moderate mismatch. Under RecSim's cascade it is no longer clearly different from zero.
- **What it does not mean:** that the SlateQ paper was wrong. Its cascade is different and much milder (see E4).

## 7. The follow-up experiments (Phase 6b, registered after Phase 6 results were seen)

These were planned after seeing the Phase 6 results, so they are **exploratory**: they explain and stress-test the main results but do not replace them. The rules (seeds, evaluation users, verdict rule, no tuning) are the same. They were written down in PROTOCOL §16 and committed before any run.

### E1: are the results caused by the learning-rate difference?

- **Why:** learned-myopic uses learning rate 2.5e-4 and SlateQ uses 1e-3, because each kept its own best setting. A critic could say the gap comes from the learning rate, not from planning.
- **What we ran:** each agent at the other one's learning rate, at (10, 3) and (80, 3).
- **Reading fixed in advance:** if SlateQ still beats learned-myopic at **both** matched learning rates, the gap is not a learning-rate artefact in that cell.
- **Result:** Both matched-learning-rate gaps are clear in both cells: at (10, 3) +1.53 (both lr 1e-3) and +1.53 (both lr 2.5e-4); at (80, 3) +36.58 and +49.64. So the gap is **not** a learning-rate artefact. Its *size* at (80, 3) does depend on the learning rate; only the direction is robust.

### E2: how much planning is needed? (the horizon curve)

- **Why:** RQ1 compares only γ = 0 and γ = 0.99. This makes RQ1 more than a replication: it asks *how much* looking ahead pays. A BSc thesis (Pantea 2022) found SlateQ behaving myopically at γ = 0.5 and listed other γ values as future work.
- **What we ran:** SlateQ with γ = 0.5, 0.9 and 0.95 (plus γ = 0 and 0.99 from E1 and RQ2), all at learning rate 1e-3, at (10, 3) and (80, 3).
- **How to read it:** the curve shows each γ minus the oracle. No curve is fitted and no "best γ" is claimed beyond these five values.
- **Result:** Every γ > 0 is clearly above the oracle in both cells. At (80, 3): +7.70 (γ 0.5), +24.46 (0.9), +27.95 (0.95), +27.17 (0.99). The gain rises with γ and levels off between 0.95 and 0.99 (F9). One comparison is not clear (γ 0.9 − γ 0 at (10, 3), where one seed is negative).

### E3: is learned-myopic simply under-trained at N = 80?

- **Why:** at (80, 3), learned-myopic is far below the oracle, even though both are myopic. One explanation: 300K training steps (chosen at N = 10) are not enough with 80 candidates.
- **What we ran:** both learned agents with 600K steps at (80, 3).
- **Reading:** if learned-myopic moves up to the oracle with twice the training, the shortfall was under-training. Two budget points cannot show more than that.
- **Result:** With 600K steps, learned-myopic − oracle is −6.23 [−10.12, −1.80], "no clear difference" (at 300K it was −13.40, clear). By the rule fixed in advance this is **consistent with under-training**, but weakly: 4 of 5 seeds are still negative and the CI excludes 0. SlateQ did not change with more training (+0.41), and SlateQ − oracle at 600K is still clear (+27.58), so the RQ2 headline holds.

### E4: the SlateQ paper's own cascade

- **Why:** our RQ3 cascade (RecSim's) made SlateQ's advantage unclear, while the paper's cascade did not. The two cascades differ, so we ran the paper's version (its §6.3: the top item is always looked at, each next position 0.65 times as likely; a looked-at item is clicked with the usual choice-model probability).
- **Result:** SlateQ − learned-myopic = +2.54 [+2.16, +2.96], all 5 seeds positive: **clear**. SlateQ − oracle = +2.42, also clear. Under RecSim's cascade (RQ3) it was +0.22, not clear.
- **What it means / does not mean:** the RQ3 cascade result depends on the cascade's parameters. RecSim's cascade makes clicks rare (random's watch time falls from 160.55 to 84.19), while the paper's version keeps them common (144.66), so quality can still extend sessions. Under the paper's cascade our port shows the same direction as the paper. It does **not** mean SlateQ is robust to any wrong choice model: two cascades are two data points, and this is our implementation of the paper's description, not a numerical replication.

### E5: does the click-maximiser get more clicks but less watch time?

- **Why:** this is the project's motivating story: a system that maximises clicks may not maximise how much people actually watch. The oracle-myopic agent is the simulator's **best click-maximiser**, so it is the right agent to test this with.
- **What we measured (no new runs):** for every cell and condition, the click rate (clicks per recommendation) and the watch time per session, oracle-myopic minus SlateQ, and learned-myopic minus SlateQ.
- **Result:** Click rate: **no clear difference in 18 of 19** conditions (every difference is below 0.001). The registered pattern "more clicks, less watch time" appears in **1 of 19** only. Watch time per session: the myopic agent is clearly lower in 17 of 19. Clicks per session: clearly lower in 17 of 19 for the oracle, e.g. 51.1 vs 58.2 at (80, 3) (F10).
- **What it means:** the click-maximiser and SlateQ are equally good at getting the *next* click. SlateQ wins by choosing equally clickable but higher-quality videos, which make sessions last longer. So the cost of maximising clicks shows up as **shorter sessions**, not as fewer clicks per recommendation. The motivating hypothesis ("more clicks, but less watch time") was mostly **not** observed, and that is reported as it is.
- **What it does not mean:** anything about YouTube, Netflix or any real platform. The SlateQ paper itself (written at Google and YouTube) says practical systems have largely relied on predicting the next response, such as clicks or watch time (p. 2, p. 4), and it reports YouTube testing SlateQ live (p. 3). So "platforms only optimise clicks" is not something this project, or its sources, can claim.

## 8. Questions you should be ready for

| Question | Short answer | Where to look |
|---|---|---|
| "Isn't RQ1 just a replication?" | Yes, on purpose; the new parts are RQ2, the RQ3 ladder, E2's horizon curve and E5 | `docs/literature/POSITIONING.md` |
| "Did anyone do RQ2 before?" | Not found in the sources searched (2026-11-13). The closest papers (Singha Roy et al. 2023, and the ACM TORS version) use 300 and 2,000 candidates but have no myopic baseline | `docs/literature/OVERLAP_MATRIX.md` |
| "Is your SlateQ correct?" | Unit tests, γ = 0 calibration against the oracle, Q-value scale, exact replay. No TensorFlow side-by-side | Section 5 above |
| "Why only 5 seeds?" | Each seed already averages 2400 paired users; the verdict needs all 5 to agree | `docs/PROTOCOL.md` §7, §14.6 |
| "Did you change anything after seeing results?" | Phase 6 rules: no. Phase 6b was added after, is labelled exploratory and was registered before its runs | `docs/PROTOCOL.md` §16, `docs/DEVIATIONS.md` D13-D16 |
| "Why not real data?" | Out of scope; options and a small proposal are in REAL_DATA_OPTIONS | `docs/literature/REAL_DATA_OPTIONS.md` |
| "Does E5 prove that platforms optimise clicks?" | No. It is a statement about this simulator only. The click-maximiser did not even get more clicks per recommendation | `docs/RESULTS.md`, E5 |
