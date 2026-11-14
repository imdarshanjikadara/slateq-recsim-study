# Candidates (S2, search date 2026-11-13)

Overlap risk is judged against our design: SlateQ vs a myopic baseline; the gap across catalog size N and slate size k; graded choice-model misspecification; learned γ=0 control plus oracle-myopic; common random numbers; 5 seeds; pre-registered protocol.

Evidence levels: E0 metadata only; E1 abstract; E2 introduction, related work and limitations; E3 full text. Notes are in `NOTES/<key>.md`.

## Top 10 by overlap risk

| # | Key | Citation (short) | Status | RQs touched | Relation to us | Ev. | Overlap risk |
|---|---|---|---|---|---|---|---|
| 1 | ie2019slateq | Ie et al. 2019, SlateQ (arXiv long version; IJCAI-19 short) | preprint / peer-reviewed | RQ1, RQ3 | Same comparison type: SlateQ vs a learned γ=0 MYOP at m=10, k=3 in the same simulator family (§7.1). Also a cascade robustness test (§7.3). **Our RQ1 is a replication of §7.1, and our RQ3 overlaps §7.3.** It did not vary m or k. | E3 | **high** (RQ1, RQ3) |
| 2 | singharoy2025dontgetbored | Singha Roy et al. 2025, ACM TORS | peer-reviewed | RQ2 theme only | SlateQ vs their faster actor at 300 and 2,000 candidates, k = 5, γ = 1; no myopic baseline; "bored" explorative users. Read in full 2026-11-13. | E3 | **low** (no gap to myopic) |
| 3 | deffayet2023gems | Deffayet et al. 2023, GeMS, WSDM | peer-reviewed | RQ3, methodology | SlateQ evaluated under click models that break its single-click assumption; a privileged short-term oracle baseline; 10 seeds. | E3 | partial |
| 4 | singharoy2023scalable | Singha Roy et al. 2023, RecSys | peer-reviewed | RQ2 theme only | SlateQ vs their faster actor at 300 and 2,000 candidates, k = 5, γ = 1; no myopic baseline. Read in full 2026-11-13. | E3 | **low** (no gap to myopic) |
| 5 | singharoy2024news | Singha Roy et al. 2024, INRA@RecSys | peer-reviewed workshop | RQ1 (partial) | SlateQ vs a greedy (myopic) baseline on a real-data RecSim extension; 300 candidates, k=10, γ=1, 5 seeds with paired t-tests. | E3 | partial |
| 6 | giovanidis2022slatefree | Giovanidis 2022, SlateFree | preprint | RQ2 (partial), RQ3 (motivation) | Varies catalog K and slate N, but measures convergence of SlateQ vs SlateFree, not the gap to a myopic baseline. Motivated by SlateQ's need for a known choice model. | E3 | partial |
| 7 | pantea2022thesis | Pantea 2022, TU Delft BSc thesis | thesis (not peer-reviewed) | RQ1 (partial) | SlateQ vs FullSlateQ in a custom RecSim environment; γ=0.5; 3 seeds; no myopic baseline. Its future work names exactly our γ question. | E3 | partial |
| 8 | kaushik2023gcitc | Kaushik et al. 2023, GCITC | peer-reviewed (IEEE conf.) | RQ1 (partial) | FullSlateQ vs SlateQ; abstract findings match Pantea 2022. | E1 | partial (low) |
| 9 | singharoy2025slatellm | Singha Roy et al. 2025, SlateLLM, RecSys 2025 | peer-reviewed | none directly | An LLM plus an RL slate recommender in a RecSim extension with real data (abstract). | E1 | low |
| 10 | deng2025fedslate | Deng et al., FedSlate, IEEE TETCI 2025 | peer-reviewed | none | A federated SlateQ in a RecSim-built environment; no myopic baseline. | E2 | low |

## Other candidates (context)

| Key | Citation (short) | Status | Relation | Ev. | Risk |
|---|---|---|---|---|---|
| rajapakse2025reassessing | Rajapakse & Jannach, "Reassessing the Effectiveness of RL based RecSys for Sequential Recommendation", SIGIR 2025, doi 10.1145/3726302.3730322 | peer-reviewed | Methodology: properly tuned supervised baselines beat RL models (abstract). Relevant to "baselines must be tuned" (we tuned both learned agents). | E1 | low |
| cavenaghi2023reproducibility | Cavenaghi et al., "A Systematic Study on Reproducibility of RL in Recommendation Systems", ACM TORS 2023, doi 10.1145/3596519 | peer-reviewed | Methodology: none of 60 RL-RecSys papers reproducible under strict ACM badges (abstract). Context for our reproducibility effort. | E1 | none |
| bergman2022rllib | Bergman & Hakhamaneshi, RecSys 2022 tutorial, "Hands-on RL for RecSys: From Bandits to SlateQ to Offline RL with Ray RLlib", doi 10.1145/3523227.3547370 | tutorial | An RLlib SlateQ implementation is used in a tutorial (abstract). | E1 | none |
| sunehag2015slatemdp | Sunehag et al. 2015 | preprint | Foundation (slate-MDP). | E2 | none |
| dulacarnold2015large | Dulac-Arnold et al. 2015 | preprint | Foundation (large discrete actions). | E2 | none |
| chen2019topk | Chen et al. 2019, WSDM | peer-reviewed | Policy-gradient alternative for top-K recommendation. | E2 | none |
| zhao2023kuaisim | Zhao et al. 2023, KuaiSim, NeurIPS | peer-reviewed | A newer data-driven simulator. | E2 | none |
| deffayet2022offline | Deffayet et al. 2022, SIGIR Forum | perspective | Next-item offline evaluation is myopic; motivates simulation-based evaluation. | E2-E3 | none |
| mladenov2021recsimng | Mladenov et al. 2021, RecSim NG | preprint | Successor simulator. | E2 | none |
| dai2023lowrank | Dai & Sun 2023, ICML workshop | workshop | Low-rank slate MDP theory in RecSim NG. | E1-E2 | none |
| wang2025hsrl | Wang et al. 2025, HSRL | preprint | 2025 trend: semantic action spaces. | E1 | none |
| tomasi2023playlist | Tomasi et al. 2023, KDD | peer-reviewed | Simulation-based RL at a music service. | E1 | none |
| futureimpact2024kdd | "Future Impact Decomposition in Request-level Recommendations", KDD 2024, doi 10.1145/3637528.3671506 | peer-reviewed | An item-level vs request-level decomposition (abstract). | E1 | none |
| onetransgsr2026 | "OneTrans-GSR", arXiv 2611.04720 (2026) | preprint | 2026 trend: generative slate ranking (abstract). | E1 | none |
| afsar2022survey, lin2024survey, chen2021drlsurvey, chen2023offlinerl | Surveys | mixed | Context. | E1 | none |

## Possible direct overlaps

Criterion: a SlateQ-style decomposition run against a myopic or greedy baseline (a) across catalog or slate sizes, (b) under another choice model, or (c) with a γ=0 control.

1. **ie2019slateq**
   - (b) and (c) are both done.
   - §7.1: SlateQ vs MYOP, where MYOP is a γ=0 learned model (footnote 10, p. 17).
   - §7.3: exponential cascade users.
   - (a) is not done (m=10, k=3 only).
2. **singharoy2025dontgetbored**
   - **Excluded after full reading (2026-11-13):** no myopic baseline (skipped on purpose, γ = 1), one slate size, so no gap-vs-size result.
3. **singharoy2023scalable**
   - **Excluded after full reading (2026-11-13):** same design as the journal version, no myopic baseline.
4. **deffayet2023gems**
   - (b) partially: SlateQ under non-matching click models, but compared with GeMS and other baselines, not framed as a SlateQ-vs-myopic gap.
5. **singharoy2024news**
   - SlateQ vs Greedy, at one candidate size (300) and one slate size (10).
   - It varies the candidate-subset fraction (20, 30, 40 %), but for Proto-Slate's inference, not for the SlateQ-vs-greedy gap.

**Not found** in the sources searched on 2026-11-13: a study reporting how the SlateQ-vs-myopic gap changes across a grid of candidate counts and slate sizes, with both a learned γ=0 control and a privileged oracle. Items 2 and 3 above are unread, so this statement is provisional.

## Independent SlateQ reimplementations found

| Implementation | Where | Licence | Maintenance (as checked 2026-11-13) | Evidence |
|---|---|---|---|---|
| RecSim reference `SlateDecompQAgent` (TF1 + Dopamine) | github.com/google-research/recsim | Apache-2.0 | **Archived**; last push 2022-01-03 | GitHub API |
| Ray RLlib SlateQ | Used in the RecSys 2022 RLlib tutorial (bergman2022rllib) | Apache-2.0 for Ray (not re-checked here) | Not checked (RLlib's current API was not inspected) | E1 (tutorial abstract) |
| Singha Roy et al. PyTorch RecSim + SlateQ | github.com/Asr419/rl_mind_dataset (cited in singharoy2024news) | not checked | not checked | E3 (paper) |
| Pantea 2022 (Dopamine-based, RecSim) | github.com/lucapantea/research-project | Apache-2.0 | Last push 2022-06-21 | GitHub API |
| GeMS repo SlateQ baseline | github.com/naver/gems | non-standard licence (GitHub: NOASSERTION) | Last push 2023-02-24 | GitHub API; deffayet2023gems |
| **This project** (PyTorch port of `SlateDecompQAgent`) | this repo | MIT | active | OUR_SETUP_FACTS.md |
