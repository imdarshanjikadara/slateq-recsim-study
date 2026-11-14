# Real-data options: KuaiRec, KuaiRand, KuaiSim, RL4RS (checked 2026-11-13)

**Scope reminder.** The approved study is a RecSim study. Nothing below was downloaded or run. This file says what each resource is, how it is obtained, its licence, and whether it could help, so that a later decision is informed.

**Sources opened this session:** arXiv API records; the GitHub README and licence (GitHub API) of each repository; Crossref for DOIs; the KuaiSim and RL4RS paper PDFs already in `docs/papers/lit/` (local only). Sizes and counts below are copied from the READMEs, not measured by us.

## 1. What each one is

| | KuaiRec | KuaiRand | KuaiSim | RL4RS |
|---|---|---|---|---|
| Type | **Dataset** (logged user-video feedback) | **Dataset** (logged feedback with random exposures) | **Simulator** built from logged data | **Dataset + simulators + benchmark code** |
| Source | Kuaishou short-video app | Kuaishou short-video app | Kuaishou (built on KuaiRand) | A NetEase game's item shop |
| Key property | "Fully observed" small matrix: 1,411 users × 3,327 videos, 99.6 % dense (almost every user rated every video); a big matrix of 7,176 × 10,728 at 16.3 % | About 0.37 % of the recommended videos were replaced by **randomly chosen** videos, so part of the log is unaffected by the recommender. 12 feedback signals (click, like, view time, ...) | User model trained on KuaiRand, with immediate feedback, session-level and cross-session (retention) tasks; also adapted to ML-1m | Slate recommendation: 3 lists of 3 items per page; RL4RS-Slate (one page) and RL4RS-SeqSlate (several pages). Data before and after an RL policy was deployed |
| Feedback label | `watch_ratio` = play time / video length (no clicks; README says there is no "like" signal) | `is_click`, `long_view`, `play_time_ms`, `is_like`, ... (`is_click` means a click in the two-column UI, a "valid play" in the one-column UI) | simulated clicks, likes, view time, leave/return | purchase-based reward per slate |
| Paper | Gao et al., CIKM 2022, pp. 540-550, doi 10.1145/3511808.3557220 (arXiv 2202.10842) | Gao et al., CIKM 2022 (resource track), pp. 3953-3957, doi 10.1145/3511808.3557624 (arXiv 2208.08696) | Zhao et al., NeurIPS 2023 (arXiv 2309.12645); NOTES/zhao2023kuaisim.md | Wang et al., SIGIR 2023 per the arXiv comment (arXiv 2110.11073); NOTES/wang2023rl4rs.md |

## 2. Access and licence

| | How to get it | Size (README) | Licence (GitHub) | Note |
|---|---|---|---|---|
| KuaiRec | Zenodo record 18164998 (`wget` link in README), no sign-up | not stated in the lines we read | **CC BY-SA 4.0** | Share-alike: derived *data* we publish must use the same licence. Our code licence (MIT) is not affected if we only read the data. |
| KuaiRand | Zenodo record 10439422; three versions: **Pure** (184 MB logs + 10 MB features), **1K** (829 MB + 3.5 GB), **27K** (23 GB + 23 GB) | as listed | **CC BY-SA 4.0** | The Pure version fits easily on this laptop (8 GB RAM). |
| KuaiSim | GitHub `Applied-Machine-Learning-Lab/KuaiSim` (code); needs KuaiRand data | - | **Apache 2.0** (code) | Data licence is KuaiRand's. |
| RL4RS | Zenodo record 6622390 (data only) or a Google Drive archive (data + simulators) | not stated in the lines we read | **Conflict:** GitHub API reports CC BY-SA 4.0, while the README badge links to CC BY 4.0 | README says it needs Linux and **at least 64 GB of memory**. Not runnable on this laptop. |

## 3. Do they help us?

| Question | Answer |
|---|---|
| Could any replace RecSim for RQ1-RQ3? | **No.** RQ1 is a replication, so it must use SlateQ's environment. Changing the simulator would change two things at once. Also out of the approved scope. |
| Could KuaiSim run SlateQ-vs-myopic? | Possibly, but KuaiSim's tasks are request-level, session-level and retention, not RecSim's choice-model slate setting. SlateQ would need its choice model adapted. A separate project. |
| Could RL4RS? | It is a slate dataset, but its rules (locked lists, purchases in a game shop) are far from video watching, and the 64 GB memory requirement rules it out here. |
| Can real data test an **assumption** behind our results? | **Yes, cheaply: KuaiRand-Pure.** Our E5 question (does a click-maximiser get more clicks but less watch time?) relies on items that are attractive to click but not worth watching. KuaiRand's **random-exposure** log shows how real users respond to items the recommender did not choose, so click rates and view times there are not biased by the recommender. |

## 4. Recommendation: (c) a small sanity-check proposal (proposal only; not run)

Cite all four in related work as well (option a), and name a data-driven simulator as future work (option b). But the most useful thing for this project is a small check of one simulator assumption on real data:

**Proposal S1: "Is there a click-versus-watch-time trade-off in real short-video logs?"**

- **Data:** KuaiRand-Pure, file `log_random_4_22_to_5_08_pure.csv` (random exposures only, 83 MB).
- **Method:** for each video with at least a minimum number of random exposures (threshold fixed before looking), compute its click rate (`is_click`) and its mean view time among clicks (`play_time_ms`, also relative to `duration_ms`). Report the rank correlation across videos with a bootstrap CI. Do this separately per UI (`tab`), because `is_click` means different things in the two UIs.
- **What it can show:** whether, in real data, the videos people click most are also the ones they watch longest (no trade-off), or not (a trade-off like RecSim's appeal-vs-quality split).
- **What it cannot show:** anything about YouTube or Netflix; anything about long-term effects. One app, one period, observational data.
- **Cost:** under an hour, laptop-sized. Needs a new PROTOCOL section first, written before the data is opened.
- **Scope:** outside the approved RecSim study. Only with the instructor's agreement, and reported as a separate appendix.

If at the end you want a "more realistic simulation", the honest route is **future work**: port SlateQ and the myopic baselines into KuaiSim and repeat RQ1 there. That is a new study, not a check.

## 5. Citations to add (metadata verified above)

- Gao, Li, Lei, ... "KuaiRec: A Fully-observed Dataset and Insights for Evaluating Recommender Systems", CIKM 2022, pp. 540-550, doi 10.1145/3511808.3557220.
- Gao, Li, Zhang, Chen, Li, Lei, Jiang, He, "KuaiRand: An Unbiased Sequential Recommendation Dataset with Randomly Exposed Videos", CIKM 2022, pp. 3953-3957, doi 10.1145/3511808.3557624.
- KuaiSim and RL4RS are already in `references.bib` (zhao2023kuaisim, wang2023rl4rs).

Evidence levels: KuaiRec and KuaiRand at E2 (README and arXiv record read; papers not read in full). The RL4RS note is raised to E2 (§3 of the paper read for the slate rules).
