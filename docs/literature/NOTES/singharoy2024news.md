# singharoy2024news: Singha Roy et al. 2024 (INRA 2024 workshop)

## Citation and status

- Singha Roy, Tragos, Lawlor, Hurley, "Simulating Real-World News Consumption: Deep Q-Learning for Diverse User-Centric Slate Recommendations".
- INRA 2024, co-located with RecSys 2024; CEUR-WS Vol-3929, short3. Peer-reviewed workshop.
- **Evidence level:** E3 (full text read).

## Claim (own words)

- They extend RecSim with real MIND news data and a learned user choice model.
- They propose Proto-Slate, which reduces the candidate items evaluated by the Q-function to a learned subset. It is SlateQ combined with a Wolpertinger-style policy.
- Proto-Slate keeps SlateQ-level hit ratio while improving topic diversity for "generalist" users, and cuts serving time (§4-5).

## Setup (§4-5)

| Item | Value |
|---|---|
| Environment | RecSim in PyTorch with MIND-large data. The user choice model is learned from data and is softmax-normalised over the slate. The reward mixes relevance and diversity. |
| Candidates / slate size | **300 candidates per user**; slate size **k = 10**. Candidate subset sizes 20, 30, 40 % were tried on a single seeded run (§5). |
| Discount factor | **γ = 1.0**, "extreme non-myopic setting" (§5) |
| Training budget | 80,000 user sessions = 400 RL steps (§5, as stated) |
| Seeds and tests | **5 seeded runs**; mean ± standard error; paired t-tests after Shapiro-Wilk and Levene checks (§5, Table 1) |
| Baselines | Random, **Greedy** (top scores of the user choice model, i.e. a myopic baseline using the learned choice model), SlateQ, Random+SlateQ, KNN+SlateQ |
| Metrics | Hit ratio and S-recall against logged test clicks; serving time |
| Code | github.com/Asr419/rl_mind_dataset (licence not checked) |

## Results (context only: different environment and metrics)

Table 1: SlateQ's hit ratio is above Greedy's for all three user types. Values are given in Table 1; no percentages are computed here.

## Overlap

| RQ | Overlap |
|---|---|
| RQ1 | Partial. SlateQ vs a greedy baseline, but in a real-data RecSim extension, with hit-ratio metrics rather than session return. The greedy baseline is neither our learned γ = 0 agent nor our privileged oracle. |
| RQ2 | Not done as a study of the gap. Candidate-subset size is varied for inference cost only. |
| RQ3 | Not done. |
| Methodology | Partial. 5 seeds and paired tests, as in ours. Not pre-registered, as far as stated. |

**Comparable to ours?** No.
