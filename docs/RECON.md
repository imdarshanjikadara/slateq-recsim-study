# Phase 0 — Reconnaissance and feasibility

Date: 2026-11-05. Machine: Windows 11 native, i5-1135G7 (4C/8T), 8 GB RAM, CPU only.
Stack: modern (see `docs/ENV.md`, `docs/DEVIATIONS.md` D1–D3). Every number below is read from
`results/recon/env_probe.json` (made by `scripts/recon/probe_env.py`) or
`results/recon/pilot_and_bench.json` (made by `scripts/recon/pilot_and_bench.py`).
Numbers labelled **PILOT** or **BENCH** are not results. **ESTIMATE** = arithmetic on BENCH numbers.

Reproduce:
```bash
.venv/Scripts/python scripts/recon/probe_env.py
.venv/Scripts/python scripts/recon/pilot_and_bench.py
```

## 1. Verified facts

| ID | Hypothesis | Status | Evidence |
|---|---|---|---|
| H1 | Default `pip install recsim` on a current stack fails at import | NOT TESTED (moot) | We no longer pip-install RecSim (D1). The source confirms why it would fail: `recsim/simulator/runner_lib.py:26` imports dopamine; `interest_evolution.py:24` imports `gin.tf`. |
| H2 | Pinned TF 2.15 stack works | SUPERSEDED | Replaced by the modern stack. **Verified instead:** RecSim's Interest Evolution runs on Python 3.14.7 / numpy 2.5.4 / gymnasium 1.4.0 via the import shim, with TensorFlow never imported (`env_probe.json`: `tensorflow_imported: false`). |
| H3 | `FullSlateQAgent` is non-decomposed; SlateQ = `SlateDecompQAgent` via `create_agent` names | CONFIRMED (source) | `full_slate_q_agent.py:31-32` ("nondecomposed … treats each slate atomically"), `:57` `itertools.permutations`. `slate_decomp_q_agent.py:730-790` lists `dp_random`, `slate_topk_sarsa`, `myopic_slate_topk_sarsa` (gamma=0), `slate_greedy_sarsa`, `myopic_slate_greedy_sarsa`, `slate_greedy_optimal_q`, `slate_topk_topk_q`, `slate_topk_optimal_q`, `slate_optimal_optimal_q`, `slate_greedy_greedy_q`. |
| H4 | `GreedyPCTRAgent` is an oracle myopic baseline | CONFIRMED, with a nuance | `greedy_pctr_agent.py`: takes a `belief_state` (we pass the true user-state object) and ranks candidates top-k by choice-model score. Nuances: (a) its default choice model is MNL with `no_click_mass=5`, while the env uses MultinomialProportional. For top-k ranking this makes no difference, since both scores are monotone in `user_interest · doc_features`. (b) In this env the user observation **already equals** the true interests (`user_obs_equals_true_interests: true`), so its only real privilege is a known choice model, which SlateQ also assumes. |
| H5 | `create_environment({num_candidates, slate_size, resample_documents, seed})`; old gym API; candidates redrawn each step | CONFIRMED (run) | `env_probe.json`: obs keys `user, doc, response`; `step` returns a 4-tuple; candidate ids changed on 64 of 64 steps of a random episode. |
| H6 | Choice models shipped | CONFIRMED (run) | `MultinomialLogit`, `MultinomialProportional`, `Cascade`, `ExponentialCascade`, `ProportionalCascade` (`env_probe.json: choice_model_classes`). Env default = `MultinomialProportionalChoiceModel`. |

## 2. Refuted / changed assumptions

- **"The oracle has privileged state information"** is weak in this environment: the learned agents also see the true interest vector. What nobody sees is item **quality** (doc features are a one-hot cluster id: `doc_obs_is_one_hot: true`). Quality only shows up in the response *after* a slate is shown.
- **Determinism needs the global NumPy RNG.** The env seed alone does not fix a trajectory. Same env seed with the same `np.random.seed` gave identical trajectories; with a different global seed it did not (`env_probe.json: determinism`). Sources: `choice_model.py:88`, `interest_evolution.py:541`.
- **The reference SlateQ drops the null item's continuation value** (see §3, row "null item"). The paper's decomposition includes it.

## 3. Paper-to-code map (SlateQ, Ie et al. 2019 → RecSim reference → our planned port)

Our port will live in `src/slateq_study/agents/slateq.py` (Phase 3).

| Paper concept | Paper location | RecSim reference (`agents/slate_decomp_q_agent.py`) | Notes / discrepancies |
|---|---|---|---|
| Item-wise LTV Q̄(s,i) | §4, Eq. 14 | `_network_adapter` (l.495) runs one net per candidate on `[user, doc]` | Network = `recsim_dqn_network` (`dopamine/dqn_agent.py:141`): concat(user 20, doc 20) → 256 ReLU → 32 ReLU → 1. Port: same shape. |
| Assumptions SC (single choice) + RTDS | §4, l.495-500 | Implicit: loss uses only the clicked item (`_build_train_op`, l.523) | Interest Evolution satisfies SC (one choice per slate). |
| Decomposition Q(s,A)=Σ P(i\|s,A) Q̄(s,i) | Prop. 1 | `compute_probs_tf` (l.24) | Conditional-choice probabilities from `score_documents(_tf)`: dot(user, doc), then proportional (`- min_normalizer`, = -1) or MNL. Defaults `no_click_mass=1`, `min_normalizer=-1`, proportional. These **match the env's true choice model** exactly (matched condition by default). |
| Null item ⊥ | §3, l.352-355 | `compute_probs_tf` returns `all_probs[:-1]`: no-click mass is in the denominator, but no Q̄(s,⊥) term is added | **Discrepancy:** the paper's sum over A includes ⊥. The reference effectively sets the no-click continuation value to 0, and trains only on clicked transitions (l.523-560). Open question Q2. |
| SARSA update | Eq. 19 | `compute_target_sarsa` (l.220): r + γ Σ_j P(j\|s',A') Q̄_target(s',j)·(1-terminal), using the **next state's candidates** and the slate actually served next | Port must store the next served slate A' in replay, mask terminals, and use s' candidates. |
| Q-learning targets | Eq. 9; §5.3 | `compute_target_topk_q` (l.323), `_greedy_q` (l.261), `_optimal_q` (l.370) | Optional variants only. |
| Top-k slate selection ("TS") | §5.2 | `select_slate_topk`: top-k of `s * q` | Primary serving rule. The paper inserts items by v(s,i)Q̄(s,i). |
| Greedy selection ("GS") | §5.2 | `select_slate_greedy` | Optional variant. The paper reports GS > TS. |
| Exact LP optimisation ("OS/OT") | §5.1 | `select_slate_optimal` enumerates all slates (not an LP) | Out of scope (exponential); not planned. |
| Exploration / evaluation | — | `_select_action` (l.634): ε-greedy with a random slate; `epsilon_eval` in eval mode | Reference uses the global `np.random` for ε. Port: own RNG so evaluation stays CRN-safe. |
| Myopic ablation | §7.1 "MYOP" (γ=0) | `myopic_slate_topk_sarsa` (`gamma=0`) | Same network/optimiser; only γ differs. |
| Hyperparameters | §7 (300K training steps) | Optimiser default RMSProp lr 2.5e-4 (`dopamine/dqn_agent.py:171-176`); γ, replay size, ε schedule and target period come from **dopamine's** `DQNAgent` defaults | Dopamine source is not in this repo, so those defaults are UNVERIFIED here. They become explicit, documented choices in PROTOCOL.md (Phase 3). |

## 4. Environment spec (RecSim Interest Evolution, as configured by `create_environment`)

- **User state** (`UtilityModelUserSampler`, `interest_evolution.py:407`): interest vector in [-1,1]^20 (uniform), `time_budget=200`, `step_penalty=0.5`, `no_click_mass=1`, `min_normalizer=-1`, `user_quality_factor=0`, `document_quality_factor=1`, `user_update_alpha=0.9/3.4` (`env_probe.json: user_params`). `score_scaling` and `attention_prob` are set but unused by the proportional choice model.
- **Documents** (`UtilityModelVideoSampler`, l.208): 20 topic clusters; features = one-hot cluster; 14 "trashy" clusters with quality means spread from -3 to 0 and 6 "nutritious" clusters from 0 to +3 (std 0.1); `video_length=4`.
- **Choice model (true):** MultinomialProportional. P(click item i) ∝ interest_i + 1, with no-click weight 2.
- **Per-step reward:** `clicked_watchtime_reward` (l.608) = watch time of the clicked item = min(remaining budget, 4); 0 on no click. Verified: the recomputed reward matched the env reward on every step (`reward_mismatch_steps: 0`).
- **Budget dynamics** (l.505-560): on a click, budget -= watch_time, then budget += alpha · watch_time · quality. On no click, budget -= 0.5. **High-quality clicks lengthen the session.** That is the long-term lever a myopic click-maximiser ignores.
- **Interest dynamics:** on a click, interests move toward or away from the clicked topic (step size shrinks with |interest|). The direction is random, with P(toward) = (interest+1)/2, drawn from the global RNG.
- **Termination:** `is_terminal` (l.501): `time_budget <= 0`. There is no max-steps limit in RecSim. Random-agent episode lengths over 20 users at N=10, k=3: min 53, max 87, mean 69.75 (`random_lengths_20_users`). We will still add a max-steps safeguard (Phase 2).
- **Observation:** `user` = true interest vector (20); `doc` = OrderedDict of N one-hot vectors; `response` = per-slate-item `click, watch_time, liked, quality, cluster_id`. The response exposes the quality of every shown item. The reference SlateQ trains only on `click` and `watch_time`; the port will do the same.
- **"Catalog size" vs code:** the proposal's "catalog size" maps to `num_candidates` N, a fresh candidate set drawn every step. There is no fixed catalogue. "Slate size" maps to `slate_size` k. (DEVIATIONS D5, open question Q1.)

## 5. Benchmarks (BENCH; 1 process, this laptop)

Environment + baseline agent throughput (env steps/s, from the pilot runs):

| Cell (N,k) | random | oracle-myopic |
|---|---|---|
| (5,2) | 4435 / 4501 | 3129 / 3138 |
| (10,3) | 3433 / 3369 | 2315 / 2294 |
| (20,5) | 2245 / 2211 | 1412 / 1501 |

PyTorch SlateQ-shaped network (batch-32 update including the next-state target over N candidates; per-step action scoring):

| N | updates/s, 1 thread | updates/s, 4 threads | action selections/s, 1 thread |
|---|---|---|---|
| 5 | 329 | 247 | 7685 |
| 10 | 276 | 214 | 7827 |
| 20 | 186 | 177 | 5742 |

One thread is faster than four, so we parallelise with processes.

**FullSlateQ action counts** (RecSim enumerates ordered slates, N!/(N−k)!): (5,2) 20 · (10,2) 90 · (10,3) 720 · (20,3) 6,840 · (20,5) 1,860,480. Unordered: 10 · 45 · 120 · 1,140 · 15,504. (20,5) is clearly intractable as a Q-head; a cap of about 720 ordered actions looks workable. To be confirmed in Phase 3.

**ESTIMATE** (arithmetic on the BENCH rows; real numbers come in Phase 3). With one gradient update per env step at N=10, each step costs about 1/276 s (update) + 1/7827 s (scoring) + 1/3400 s (env) ≈ 4.1 ms, so 300K steps (the paper's budget) ≈ 20 min per run. With one update every 4 steps (the DQN convention), ≈ 7 min. Process-level parallelism: 3 workers is the likely safe limit on 8 GB RAM (memory per process not yet measured).

## 6. Plausibility PILOT (2 seeds × 100 episodes per cell; common random numbers)

| Cell | Agent | mean total reward (seed 0 / 1) | mean length | mean clicked quality |
|---|---|---|---|---|
| (5,2) | random | 154.4 / 154.0 | 84.0 / 83.3 | -0.610 / -0.620 |
| (5,2) | oracle-myopic | 161.1 / 161.8 | 68.2 / 68.6 | -0.666 / -0.632 |
| (10,3) | random | 161.0 / 161.2 | 71.2 / 71.6 | -0.592 / -0.581 |
| (10,3) | oracle-myopic | 167.8 / 166.1 | 59.0 / 59.8 | -0.637 / -0.642 |
| (20,5) | random | 164.4 / 162.9 | 59.4 / 59.6 | -0.651 / -0.678 |
| (20,5) | oracle-myopic | 169.7 / 170.2 | 52.6 / 53.1 | -0.683 / -0.645 |

Paired difference oracle − random (mean ± SE over 100 CRN episodes): (5,2) 6.77±1.60 / 7.74±1.47; (10,3) 6.75±2.09 / 4.95±1.82; (20,5) 5.30±2.28 / 7.25±2.04.

**Is a long-term-vs-myopic gap plausible?** Yes, mechanistically. The oracle-myopic agent wins on immediate engagement (more clicks per step, more reward) but has *lower* clicked quality and *shorter* sessions than random. Quality is exactly what extends the time budget. So a policy that gives up some click probability for quality should be able to beat myopic.

**Caution on effect size.** The SlateQ paper's own simulation (their §7.1 table, 300K training steps, 5000 users) reports MYOP-TS 166.3 vs SARSA-TS 168.4 average return. That is the paper's claim, not ours. A gap of that size is small next to the per-episode standard deviation we see (about 17–26 for oracle-myopic). Detecting it needs CRN pairing and many evaluation episodes per seed. Phase 2 sizes this from measured variance.

## 7. Risks and edge cases found

1. **Small true effect** (above). This drives the eval-episode count and the seed count. A null RQ1 result is a real possibility, and reportable.
2. **Global-RNG coupling.** Agents or harness code that draw from `np.random` desynchronise CRN. Our agents must use their own `np.random.Generator`. The harness seeds `np.random` per episode.
3. **CRN across episodes.** Agents produce different episode lengths, so the doc sampler's RNG stream diverges after episode 1 if one env is reused. Fix: build/reseed the env per evaluation episode (as the pilot does).
4. **Null-item handling** (§3). Faithful port vs paper semantics changes the target values. Needs a decision (Q2).
5. **Unverified dopamine defaults** (§3). Hyperparameters become explicit choices, tuned under the same budget for SlateQ and learned-myopic.
6. **FullSlateQ intractability** grows factorially. It's a result for RQ2, and the first thing to cut (Appendix C).
7. **Compute:** 4 cores / 8 GB. A full grid (e.g. 4×3 cells × 2 learned agents × 5 seeds = 120 runs at about 7–20 min each, ESTIMATE) is roughly 5–13 h with 3 workers. Feasible overnight, but fix the grid before launch.
8. **Windows specifics:** paths via `pathlib`; `make` from winget; the old uv minor-version-link glitch (ENV.md).

## 8. Fallback assessment (PyTorch port vs staying on TF)

Decided by the student (D1): the PyTorch port is now the main path. Effort is moderate: about 300 lines for a vectorised SlateQ with replay, a target network and top-k/greedy selection. The main risk is silent divergence from the reference. Mitigation: unit tests for scoring (against RecSim's NumPy `score_documents`), top-k selection, and the SARSA target (against hand-computed values from Eq. 19), plus the γ=0 calibration test against oracle-myopic.

## 9. Open questions for the student

**Decisions (student, 2026-11-05):** Q1, Q2 and Q3 accepted as recommended:
- Catalog size = `num_candidates` N, resampled every step.
- Primary SlateQ is a faithful port of the RecSim reference (no-click continuation value = 0, trained on clicked steps only). The paper's learned Q̄(s,⊥) is stated as a limitation.
- Primary agent = `slate_topk_sarsa`; greedy serving is an optional variant.

Q4 is deferred to Phase 3. Q5 and Q6 are still open.

- **Q1 Catalog size.** OK to define "catalog size" as `num_candidates` N, resampled every step (D5)? The alternative, a fixed per-episode catalogue (`resample_documents=False`), departs from the RecSim/SlateQ setup.
- **Q2 Null item.** Port the RecSim reference faithfully (no-click continuation value = 0, train on clicked steps only), or follow the paper's decomposition with a learned Q̄(s,⊥)? Recommendation: faithful to the reference for the primary agent; mention the paper's variant as a limitation.
- **Q3 Primary agent.** `slate_topk_sarsa` (SARSA-TS, the variant the paper live-tested) as primary SlateQ? Greedy serving (GS, which the paper says is better) as an optional variant.
- **Q4 Training budget.** Fix it in Phase 3 from learning curves. The paper's 300K steps is the reference point and looks affordable (about 7–20 min/run, ESTIMATE).
- **Q5 Deadline.** When is the final submission? It decides the grid size and seed count (target 5).
- **Q6 Commits.** OK to make the initial commit (setup) and then "phase 0: recon" now?

## 10. Recommended plan for Phases 1–8, with go/no-go gates

| Phase | Adjusted for the modern stack | Go/no-go gate |
|---|---|---|
| 1 Scaffolding | Promote the shim to `src/slateq_study/recsim_compat.py`; seeding module owns the global `np.random`; per-run subprocess with 1 torch thread; Makefile via winget make | `make setup/test/smoke` green from a clean clone |
| 2 Env, baselines, protocol | Per-episode env re-seeding for CRN; GreedyPCTR rebound to the new user state each episode; PROTOCOL.md with eval-episode count sized from the measured variance | Oracle > random with CI (PILOT says yes); PROTOCOL.md approved |
| 3 SlateQ (PyTorch) | Port + unit tests vs the reference maths; ladder 1–5; γ=0 calibration vs oracle | Calibration passes; hyperparameters frozen |
| 4 Sweeps | Grid chosen from Phase 3 timings; 3 workers | Kill/resume mini-sweep passes; dry-run approved |
| 5 RQ3 | The agent's assumed model is fixed in our code (proportional, `no_click_mass=1`); vary the env's true choice model (MNL temperature, cascade variants, `no_click_mass`) | Protocol addendum before the sweep |
| 6–9 | As in the playbook | As in the playbook |
