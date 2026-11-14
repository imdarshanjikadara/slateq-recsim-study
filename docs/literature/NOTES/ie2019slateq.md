# ie2019slateq: Ie et al. 2019, SlateQ (long arXiv version)

## Citation and status

- **Read:** Ie et al., "Reinforcement Learning for Slate-based Recommender Systems: A Tractable Decomposition and Practical Methodology", arXiv:1905.12767v2 (2019), 13 authors. This is a preprint, the long version.
- **Peer-reviewed short version:** IJCAI-19, pp. 2592-2599, doi 10.24963/ijcai.2019/360. Not read here; the section numbers below refer to the arXiv version.
- **Evidence level:** E3. Full text: `docs/papers/slateq.pdf` / `.txt`. Page numbers are the paper's printed page numbers.

## Claim (own words)

- An item-level Q decomposition makes TD learning tractable for slates. It holds under two assumptions: the user consumes at most one item per slate, and reward and transition depend only on the consumed item. Slate optimisation stays tractable with an LP, or with top-k / greedy heuristics.
- In simulation, long-term (LTV) SlateQ policies give higher return per session than myopic ones. They do so by recommending higher-quality items, which lengthens sessions.
- A live YouTube experiment is also reported (§9). It is not used here.

## Simulation setup (§6-7, pp. 19-25)

| Item | Value |
|---|---|
| Environment | Stylised simulator described in §6: topics, quality, user interest, time budget. The paper does not call it RecSim. It matches RecSim Interest Evolution on budget 200 and no-click cost 0.5 (p. 21; RecSim `interest_evolution.py:430-432`), and on document length: the paper uses a fixed length of 4 (p. 21), and RecSim's `UtilityModelVideoSampler`, used by RecSim's `create_environment` and by our `envs.py`, also fixes `video_length=4.0` (`interest_evolution.py:208-215, 649`). *(Corrected 2026-11-13: an earlier audit wrongly cited the unused `IEvVideoSampler`, mean 4.3.)* We have not checked every simulator detail, so we call them closely related, not identical. |
| Candidates and slate size | m = 10 candidates per step, k = 3 (§6.5, p. 22). **Only this one size is used in simulation.** The reason given is that small sizes allow enumerating slates for the FSQ comparison (p. 22). |
| Topics | \|T\| = 20 (§7.2, p. 24) |
| Discount factor | LTV policies use γ = 1 (p. 22); no discounting is needed because sessions terminate (p. 21). MYOP uses γ = 0. |
| Training budget | 300K training steps for all methods (§7.1, p. 23) |
| Evaluation | 5000 simulated users per training-serving strategy; "All results are within a 95% confidence interval" (p. 22) |
| Seeds | **Number of training seeds not reported** (searched for "seed", "trials" and "repeat": no hit). |
| Implementation | Dopamine; two-tower network (p. 22) |

## Agent variants and baselines

- **SARSA variants** (on-policy, one-step policy improvement) with serving TS / GS / OS.
- **Q-learning variants** QL-xT-yS (training optimisation × serving optimisation).
- **MYOP-TS / MYOP-GS.** Footnote 10 (p. 17): a myopic model equals a Q-learned model with γ = 0. **MYOP is therefore a learned myopic baseline, like our learned-myopic. It is not privileged.**
- **Random.**
- **FSQ** (non-decomposed full-slate Q-learning), in §7.2.
- **No privileged (oracle) myopic baseline** appears in §7.

## Choice model

- **Assumed:** the general conditional choice model with a null item (§6.3, p. 20).
- **§7.3 robustness ("Robustness to User Choice", pp. 24-25):**
  - Users follow an exponential cascade. Position j is inspected with probability β0·β^j, with β0 = 1.0 and β = 0.65 (§6.3, p. 21).
  - An inspected item is consumed with the conditional model's normalised probability P(u, d). The null item is kept so that probabilities stay calibrated (p. 21).
  - SlateQ is still trained, and serves, with the conditional model.

## Results (context only: different implementation and evaluation)

**§7.1 table (p. 23):**

| Policy | Return |
|---|---|
| Random | 159.2 |
| MYOP-TS | 166.3 |
| SARSA-TS | 168.4 |
| SARSA-GS | 172.1 |
| best (QL-OT-OS) | 174.6 |

Relative to MYOP-TS, computed by us from that table: SARSA-TS +1.26 %; SARSA-GS +3.49 %; QL-OT-OS +4.99 %. The paper itself reports percentages relative to **Random**, not relative to MYOP.

**§7.3 table, cascade users (p. 25):**

| Policy | Return |
|---|---|
| Random | 159.9 |
| MYOP-TS | 163.6 |
| SARSA-TS | 166.8 |
| QL-OT-OS | 167.6 |

SARSA-TS relative to MYOP-TS, computed by us: +1.96 %.

**Authors' interpretation of §7.3:**
- SlateQ "continues to outperform MYOP" under the wrong choice model (p. 25).
- QL-TT and SARSA swap order compared with §7.1. Their explanation: Q-learning exploits the incorrect choice model during training, while on-policy SARSA uses it only for expectations at serving time. SARSA may therefore be more robust (p. 25).
- Under cascade, Random's return (159.9) is close to its matched-model return (159.2). In their cascade, click behaviour was therefore not drastically reduced. Ours was: see S6.

## Assumptions and limitations

- Single choice per slate; reward and transition depend only on the consumed item.
- Stylised simulator.
- One (m, k) setting in simulation.
- Seeds and per-seed variability are not reported.

## Overlap with our RQs

| RQ | What they did | What they did not do |
|---|---|---|
| RQ1 | Same comparison type: SlateQ vs a learned γ = 0 myopic baseline, in essentially the same simulator, at m = 10, k = 3. Our RQ1 is therefore a **replication**, not a new question. | - |
| RQ2 | - | Did not vary m or k in simulation (p. 22). |
| RQ3 | Did test misspecification: one cascade setting, several variants, one reported table. **This overlaps RQ3.** | No graded ladder; no oracle-myopic; no seeds or CIs reported. |
| Methodology | - | No oracle-myopic; no common-random-number pairing or per-seed analysis stated; no pre-registration. |

**Comparable to ours?** The setting is close: same environment family, same primary cell, and the same baseline definition. But implementation, number of seeds, evaluation stream, SlateQ variants and the cascade parameterisation differ. Numbers are **context only**.
