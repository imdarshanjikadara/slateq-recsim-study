# Q&A preparation: literature, novelty and hard questions

## Sources and labels

- Our numbers: `docs/NUMBERS.md` (generated) and `docs/SUPPLEMENT_STATS.md` (post-hoc, supplementary).
- Other papers: `docs/literature/NOTES/`.
- **"Not tested"** marks anything a proposed diagnostic would answer but which was not run (`docs/literature/PROPOSED_DIAGNOSTICS.md`).
- Literature search date: 2026-11-13.

---

## 1. "Your key papers are from 2019. Isn't this outdated?"

### 30 seconds

SlateQ and RecSim are the original papers for the method and the simulator, so a replication has to start there. They are still in active use: we found 52 works dated 2026 among the 369 works citing them. SlateQ-style agents in RecSim were used in 2024-2025 papers (Singha Roy et al. 2024; FedSlate 2025). Newer work critiques the decomposition (GeMS, WSDM 2023) or scales it (Singha Roy et al. 2023-2025). We read the newer work and position against it. We do not claim to beat it.

### 2 minutes

- **What we are.** A measurement study of one specific question: does planning beyond the next click pay off, and how does the payoff change with catalog and slate size and with a wrong user model? That question is best asked of the original method in its original environment. Otherwise a difference could come from the new method or the new simulator, and not from the horizon.
- **What came after (2022-2025).** Three strands, all read:
  - work that removes SlateQ's assumptions (GeMS, SlateFree);
  - work that scales it to large item pools with real data (Singha Roy et al.);
  - critiques of evaluation practice (Deffayet et al., SIGIR Forum 2022).
- **What 2026 looks like.** The work citing SlateQ and RecSim is mostly generative and LLM-based slate ranking. None of it, as screened, re-measures SlateQ against a myopic baseline across sizes.
- **How we position.** A controlled, pre-registered replication and extension, not a state-of-the-art claim.
- **Limits.** Google Scholar was not queried, so the search is not exhaustive.

## 2. "Hasn't someone already done this?"

### 30 seconds

- **RQ1:** yes. The SlateQ paper itself compared SlateQ with a γ = 0 myopic model at 10 candidates and slate size 3. Our RQ1 is a deliberate replication with an independent implementation and stricter statistics.
- **RQ2:** the paper used that single size. We did not find a study of how the gap changes over a grid of sizes, among the sources we searched on 2026-11-13. The closest papers, two Singha Roy et al. papers on SlateQ with 300 and 2,000 candidates, compare SlateQ with their own faster actor and skip a myopic baseline on purpose. This is still "not found in the sources searched", not "not done".
- **RQ3:** the paper ran one cascade test. We run a graded ladder.

### 2 minutes

Add the overlap details (`OVERLAP_MATRIX.md`):

- **GeMS** also tests SlateQ under click models that break its assumptions, and uses a privileged short-term oracle.
- **SlateFree** varies catalog and slate size, but measures convergence, not the gap to myopic.
- **Singha Roy 2024** compares SlateQ with a greedy baseline on real news data at one size.
- **What is ours:** the size grid, the graded ladder, and running both a learned γ = 0 control and a privileged oracle under a pre-registered rule with common random numbers. Each element exists somewhere; the combination applied to these questions was not found.

---

## 3. Hard questions

**Q. Why is the RQ1 effect only about 1%?**

- +1.70 on 167.50 (NUMBERS RQ1).
- At N = 10 there are few high-quality candidates per step, so there is little to plan for.
- Our port's zero no-click value also shortens the effective horizon (D6; TRAINING_NOTES).
- For context only (different implementation): the SlateQ paper's own SARSA-TS was about 1.3 % above its MYOP-TS (NOTES/ie2019slateq).
- The effect is small but consistent: 5 of 5 seeds; the t-interval [+1.44, +1.96] excludes 0 (SUPPLEMENT_STATS).

**Q. Does the gap grow because SlateQ improves or because the baseline degrades?**

Both (NUMBERS, RQ2 secondary table):

- **SlateQ improves.** SlateQ − oracle rises from +1.60 at (10, 3) to +27.17 at (80, 3). Clicked quality rises from −0.583 to −0.186.
- **The baseline degrades.** Learned-myopic − oracle falls to −13.40 at (80, 3).
- **The headline is the oracle comparison**, because the oracle cannot be under-trained.
- Why learned-myopic degrades: **not tested** (DISCREPANCIES iv; D-1b).

**Q. An untrained network scored about 168 at step 0. How do we know it learned?**

- At step 0, tune-stream scores range 125.80-168.07 over seeds (mean 149.92; `results/rq2/curves.csv`). An untrained ranking is essentially random, and on some seeds it happens to be decent.
- Three signs of learning:
  1. After 50K steps every checkpoint is at about 168-171 on every seed (F1).
  2. Learned-myopic matches the privileged oracle at (10, 3): −0.09, CI [−0.24, +0.08]. An untrained network would not recover the oracle's ranking on all seeds.
  3. SlateQ's clicked-item quality rises with N, up to −0.186 at (80, 3), against −0.602 for the oracle. That is a learned preference for quality, which an untrained network has no reason to show.

**Q. Is a PyTorch port really SlateQ?**

- It ports RecSim's `SlateDecompQAgent` as SARSA-TS.
- Component tests match RecSim's scoring exactly, plus the top-k rule, the SARSA target and Dopamine's ε schedule (12 tests pass; OUR_SETUP_FACTS a).
- **Not done:** no end-to-end run against RecSim's TF1 agent (excluded stack, D1/D3). Say this plainly.
- Context only: our numbers at (10, 3) are close to the paper's §7.1 table, which is a plausibility check, not proof.

**Q. Why different learning rates for the two agents?**

- Equal tuning budget: the same 9-config grid, seeds and episodes. Each agent got its best rate (PROTOCOL 12.4-12.6).
- So "only γ differs" is not literally true; say "same architecture, data, budget and tuning budget".
- On the tune stream SlateQ is ahead at each matched rate: +1.59, +1.46, +1.91 (OUR_SETUP_FACTS b).
- An eval-stream matched-rate run is **not tested** (D-1).

**Q. Why does your cascade result differ from the SlateQ paper's?**

- The cascades are different. Ours is RecSim's default proportional cascade, which makes clicks rare:
  - random's return drops from 160.55 to 84.19;
  - sessions lengthen from 70.8 to 227.3 steps.
- In the paper, random barely changed (159.2 → 159.9).
- With rare clicks there is little quality-driven budget refund to plan for. Our port's zero no-click value further shortens the horizon (PLAUSIBLE).
- So we do not contradict the paper; our result shows the advantage depends on the cascade's parameters (DISCREPANCIES i).
- A paper-like cascade is **not tested** (D-3).

**Q. Random has the longest sessions but the lowest reward. Why?**

- In RecSim, a no-click step costs only the 0.5 step penalty, while a click costs the watch time (`interest_evolution.py`: `step_penalty`, `time_budget -= watch_time`).
- Random shows less appealing items, users skip more, and sessions get longer with less watching. Reward is watch time.

**Q. Why 5 seeds and seed-bootstrap CIs? What do t-intervals show?**

- 5 seeds was the proposal's target. Each seed averages 2400 paired sessions.
- The pre-registered rule also requires all 5 seeds to agree in sign.
- Post-hoc t-intervals (df = 4) agree with every pre-registered verdict:
  - all 14 RQ2 cells exclude 0;
  - the control (−0.01, [−0.07, +0.05]) and the cascade rung ([−0.04, +0.47]) include 0;
  - 0 disagreements (SUPPLEMENT_STATS).

**Q. The case-study user prefers random. Isn't that embarrassing?**

- The user was chosen by a pre-registered rule (median-gap seed, episode 0) before results existed.
- One user is not evidence; the averages over 5 × 2400 sessions are.
- Showing it as chosen is the honest choice.

**Q. The budget was frozen at N = 10. Is that fair at N = 80?**

- It is the same budget for both learned agents (fair between them).
- It may disadvantage both at large N. Learned-myopic falling below the oracle suggests it does disadvantage the myopic learner.
- That is why the RQ2 headline uses the oracle.
- Larger budgets at large N: **not tested**.

**Q. What does "catalog size" mean here?**

The number of candidates N redrawn every step (`num_candidates`, `resample_documents`; D5). There is no fixed catalogue in Interest Evolution.

**Q. Isn't the oracle-myopic unfair?**

- It is privileged on purpose: it reads the true user state, so it is a ceiling for click-maximisers, not a deployable baseline.
- GeMS uses the same kind of short-term oracle (NOTES/deffayet2023gems).
- Beating it means planning helps beyond perfect click prediction.

**Q. Why RecSim and not KuaiSim?**

- A replication must use SlateQ's environment.
- KuaiSim is data-driven and built around different tasks: request-level, session-level and retention (NOTES/zhao2023kuaisim).
- KuaiSim is out of scope per the approved proposal (no real data).
- Result transfer to KuaiSim: **not tested**.

**Q. What would GeMS or SlateFree change?**

- **GeMS:** removes the single-click, known-choice-model assumptions by learning a latent slate space from logged data. In click models that break SlateQ's assumptions it beats SlateQ (NOTES/deffayet2023gems). It might do better than SlateQ in our RQ3 cascade rung.
- **SlateFree:** needs no choice model and converges faster in tabular tests (NOTES/giovanidis2022slatefree).
- Neither was run (out of scope: no new algorithms). This is **not tested**.

**Q. What would real data change?**

- Real users violate the simulator's assumptions in unknown ways. Offline next-item metrics are themselves myopic (NOTES/deffayet2022offline).
- Singha Roy et al. 2024 extend RecSim with MIND data (NOTES/singharoy2024news).
- Our conclusions are about RecSim Interest Evolution only.

**Q. Which recent paper is closest, and how do you differ?**

- **Closest that we could read:** Singha Roy et al. 2024 (INRA@RecSys), which has SlateQ vs Greedy in RecSim with real data. It uses one size (300 candidates, k = 10), hit-ratio metrics and γ = 1, and has no learned γ = 0 control and no misspecification ladder.
- **Same group, read in full:** their RecSys 2023 and ACM TORS papers use 300 and 2,000 candidates, but compare SlateQ with their faster actor at γ = 1 and have no myopic baseline (NOTES/singharoy2023scalable, NOTES/singharoy2025dontgetbored).

---

## Slide spec: "Related work and where this fits"

**Bullets (3):**

1. SlateQ and RecSim (2019) introduced the decomposition and the simulator. Their simulation used one size: 10 candidates, slate size 3.
2. Later work relaxed SlateQ's assumptions (SlateFree 2022, GeMS 2023), scaled it to large real-data pools (Singha Roy et al. 2023-2025), and questioned offline evaluation (Deffayet et al. 2022).
3. This project replicates SlateQ vs myopic and extends it over 14 sizes and a graded user-model ladder, with a learned and an oracle baseline under a pre-registered rule. It is a measurement study, not a new method.

**Timeline (left to right):**

| Year | Work |
|---|---|
| 2015 | Slate-MDP (Sunehag et al.); large discrete actions (Dulac-Arnold et al.) |
| 2019 | SlateQ (IJCAI) and RecSim |
| 2022 | SlateFree; offline-evaluation critique (SIGIR Forum) |
| 2023 | GeMS (WSDM); KuaiSim (NeurIPS); Singha Roy et al. (RecSys) |
| 2024-2025 | Singha Roy et al. (INRA@RecSys 2024; ACM TORS 2025); FedSlate (TETCI 2025) |
| 2026 | This project |

**Footer:** "Literature search 2026-11-13; not exhaustive; see docs/literature."
