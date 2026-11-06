# Evaluation protocol

Status: **fixed 2026-11-05, before any learned-agent experiment.** Sections 1–11 are frozen. Changes
are allowed only if logged in §13 with a reason, and never after seeing a comparison they could
affect. Section 12 must be completed in Phase 3, before any sweep is launched.

## 1. Environment and what "engagement" means

- RecSim Interest Evolution, built from RecSim's own classes (`src/slateq_study/envs.py`; equal step by step to RecSim's `create_environment`, see `tests/test_envs.py`).
- **Per-step reward** = watch time of the clicked item (`clicked_watchtime_reward`), = min(remaining time budget, video length 4); 0 when nothing is clicked.
- **Episode end** = the user's time budget (starts at 200) reaches ≤ 0. A click costs its watch time and refunds `alpha · watch_time · quality`; a no-click step costs 0.5. High-quality clicks lengthen the session.
- **Long-term engagement** = total reward over the episode (total watch time over the session).
- Safeguard: `max_steps = 1000`. A run reaching it is **truncated** (not terminated). Truncated episodes stay in all means and are reported as a count per run.
- "Catalog size" = `num_candidates` N, redrawn every step; "slate size" = k (DEVIATIONS D5).

## 2. Agents

| Agent | Information | Notes |
|---|---|---|
| `random` | observation only | RecSim `RandomAgent`, own RNG |
| `oracle_myopic` | **privileged**: true user-state object + the env's true choice model | RecSim `GreedyPCTRAgent`, top-k by click score. Uses no random numbers. `meta.json: privileged_agent = true`. |
| `learned_myopic` (Phase 3) | observation only | SlateQ port with γ = 0 |
| `slateq` (Phase 3) | observation only | SlateQ port, top-k, SARSA (DEVIATIONS D3, D6) |

S4: the oracle uses the env's true choice model rather than GreedyPCTR's default (MNL, no_click_mass 5). The ranking is identical either way.

## 3. Seeds

- **Run seeds:** 0, 1, 2, 3, 4 (**5 seeds**, S3). Never fewer than 3. Every agent × cell is run under the same run seeds.
- **Three disjoint env-seed streams**, disjoint by construction (`src/slateq_study/seeding.py`, tested): `env_seed = offset[stream] + run_seed · 100000 + episode` with offsets train 0, tune 1e9, eval 2e9.
  - `train`: training episodes of learned agents.
  - `tune`: hyperparameter tuning and protocol-sizing studies (e.g. §6).
  - `eval`: final evaluation only. No decision is ever taken from eval-stream data except the reported results.
- Agent RNG (exploration, network init) uses `agent_seed(run_seed)`, independent of env seeds.

## 4. Common random numbers (paired design)

Evaluation episode i of run seed s uses env seed `env_seed("eval", s, i)` for **every** agent. Before each episode the harness builds a fresh env with that seed and seeds the global `np.random` with it. Every agent therefore meets the same user at step 0 and the same initial candidates (tested), and comparisons are paired per seed. Agents must not draw from the global `np.random` during evaluation (learned agents use their own generator).

## 5. Metrics (S1)

- **Primary:** mean total episode reward (total watch time).
- **Secondary:** episode length (steps), clicks per episode, mean clicked-item quality (NaN-safe: an episode with no clicks is excluded from this metric only), reward per step.
- **Diagnostics (reported, not compared):** truncated episodes, slates with duplicate items, failed runs.

## 6. Number of evaluation episodes (S2) — **2400 per run**

Rule (fixed before measuring): choose n so that, within one seed, the standard error of the episode-level paired difference between two methods is ≤ **0.5 reward**. That is about a quarter of the ~2-point myopic-vs-SlateQ gap reported in the SlateQ paper's simulation (Ie et al. 2019, §7.1; the paper's claim, not ours).

Measurement (`scripts/variance_study.py` → `results/protocol/variance_study.json`): random vs oracle-myopic, 500 paired episodes on the **tune** stream, 5 seeds, cells (5,2), (10,3), (20,5). Required n per (cell, seed) = ⌈(SD_diff / 0.5)²⌉. Largest observed: 2362, at (20,5) seed 2. Rounding up to a multiple of 50 gives **eval_episodes = 2400**, used for every agent and every cell.

Assumption: the oracle-minus-random difference is a proxy for the SlateQ-minus-myopic difference. In Phase 3 the SD of the learned-agent paired difference is re-measured on tune seeds. If it needs a larger n, n is raised before any sweep. n is never lowered.

## 7. Summaries and uncertainty

- **Per-run summary** = mean over the run's 2400 evaluation episodes (`metrics.summarize`).
- **Across seeds** (unit of replication = seed): mean, sample std (ddof 1), and a **percentile bootstrap 95% CI resampling seeds** (10,000 resamples, generator seed 20261105; `src/slateq_study/stats.py`).
- **Method comparison:** per-seed paired difference of per-run means (A − B), then mean, std and bootstrap CI over seeds. Also reported: within-seed episode-level paired mean ± SE.
- **Reporting rules:** every seed is also shown individually. With ≤ 5 seeds we report effect sizes and CIs, not "statistically significant". A CI that includes 0 is reported as "no clear difference", not "no difference".

## 8. Trajectory traces (S5)

Per-step traces (user interests, slate, slate clusters and qualities, clicked position, reward, time budget after the step) are saved for the **first 5** evaluation episodes of each run (`trace_episodes: 5`): a fixed rule, never picked after looking. The time budget is read from the simulator for plotting only (privileged); no agent sees it.

## 9. Failures and missing data

A failed or timed-out run has `error.json` and no `DONE`; it is listed in a status table and never imputed or silently averaged. Every aggregate states its number of seeds. Runs with NaN/inf metrics are failures.

## 10. Sanity requirements before any comparison

- Oracle-myopic beats random on the primary metric with a CI excluding 0 on the baseline grid (Phase 2 acceptance). If this ever fails, stop and investigate.
- Phase 3 ladder (plumbing, beats random, γ=0 calibration toward the oracle, Q-scale, learning curves) must pass before SlateQ-vs-myopic results are considered meaningful.

## 11. Baseline grid (Phase 2 acceptance only)

Cells (5,2), (10,3), (20,5); agents random and oracle-myopic; run seeds 0–4; 2400 eval episodes; traces for the first 5 episodes. Script: `scripts/baselines.py` → `results/baselines/`. The RQ2 sweep grid is chosen in Phase 4.

## 12. Learned agents: training, budget and tuning (rules fixed 2026-11-06, before any Phase 3 run)

**12.1 Defaults (T1)** — `src/slateq_study/agents/slateq.py`, following RecSim's SlateDecompQAgent and dopamine's DQN defaults (dopamine source not in this repo: UNVERIFIED locally):
centered RMSProp (lr 2.5e-4, decay 0.95, eps 1e-5), γ 0.99 (learned-myopic: γ = 0), batch 32, one update every 4 env steps once the replay holds > 20,000 transitions, target-network sync every 8,000 steps, replay capacity ≥ training budget, ε-greedy ε = 1 during the 20K warmup and then linearly to 0.01 over 100,000 steps, **ε_eval = 0**, top-k serving, SARSA target, squared loss on clicked steps only, Glorot-uniform init.

**12.2 Phase 3 run seeds** (never 0–4, which are reserved for the final results): sanity ladder 100–101; budget rule 100–102; tuning 100–101; final Phase 3 curves 200–202. All Phase 3 runs train on the train stream and are scored on the **tune** stream (500 episodes per run; learning curves 200 episodes). The eval stream is not used in Phase 3.

**12.3 Training budget rule (T2).** SlateQ with the 12.1 defaults, cell (10,3), seeds 100–102, 500,000 steps, curve point every 50,000 steps. Let d_s = (curve reward at 500K) − (curve reward at 300K) for seed s. **Budget = 500,000 if mean(d) > 2 · SD(d)/√3, otherwise 300,000.** The budget is the same for every learned agent and every cell. It is fixed before tuning.

**12.4 Tuning (T3).** Grid: learning rate {1e-4, 2.5e-4, 1e-3} × target-update period {1000, 4000, 8000} = 9 configs; all other settings as 12.1. Cell (10,3), seeds 100–101, budget from 12.3, 500 tune-stream episodes per run. SlateQ and learned-myopic are tuned on the identical grid and budget (36 runs). **Selection: for each agent separately, the config with the highest mean (over the 2 seeds) tune-stream total reward.** Ties within 0.01 are broken by the earlier grid entry (lr ascending, then period ascending). The selected configs are then frozen for all later phases and written into §12.6.

**12.5 Re-check of the episode count (T4).** From the tuning runs of the two selected configs (same tune episodes for both, so paired), n = ⌈(SD_diff / 0.5)²⌉ per seed. If max n > 2400, eval_episodes is raised (rounded up to a multiple of 50) before Phase 4. It is never lowered.

**12.6 Frozen values** (filled in by Phase 3; source files in `results/phase3/`):
- Training budget: **300,000 environment steps** (`budget.json`: mean d = −0.137 ≤ 2·SD/√3 = 0.535).
- SlateQ hyperparameters: **learning rate 1e-3, target-update period 1,000**; everything else as 12.1 (`tune.json`).
- Learned-myopic hyperparameters: **learning rate 2.5e-4, target-update period 1,000**; everything else as 12.1 (`tune.json`). With γ = 0 the target network never enters the loss, so the three periods gave identical results and the tie went to the earliest grid entry.
- eval_episodes after 12.5: **2400 (unchanged)**. Required n per seed = 206 / 163 (`tune.json`, `episode_recheck`).

**12.7 Sanity-ladder pass criteria** (cell (5,2), seeds 100–101, 12.1 defaults, 300K steps, 500 paired tune episodes vs random and oracle on the same env seeds):
1. Plumbing: run completes; all logged loss/Q values finite; replay size = steps; final ε = 0.01; ≥ 1 target sync.
2. Beats random: for each learned agent and each seed, paired mean difference (agent − random) > 2 SE.
3. Calibration: learned-myopic recovers ≥ 90% of the oracle's improvement over random, i.e. (LM − random) / (oracle − random) ≥ 0.9, averaging both seeds. If it fails: stop and diagnose the pipeline first.
4. Q-scale: learned-myopic's mean clicked-item Q in its last diagnostics window lies in [2, 6] (immediate watch time ≈ 4); SlateQ's is larger than learned-myopic's and below 400 = 4/(1−γ).
5. Learning curves over 3 seeds with frozen hyperparameters (stage "final") are reported; no pass threshold beyond finite values.

**12.8 FullSlateQ (T5):** deferred until after Phase 3; cap proposed in Phase 4 from measured timings (RECON suggests ~720 ordered slates).

## 13. Change log

| Date | Change | Reason |
|---|---|---|
| 2026-11-05 | Protocol created; eval_episodes = 2400 from the variance study | Phase 2 |
| 2026-11-06 | §12 rules for learned agents (defaults, seeds, budget rule, tuning grid, selection, n re-check) fixed before any Phase 3 run | Phase 3, approved T1–T6 |
| 2026-11-06 | §12.6 filled in: budget 300K, selected SlateQ / learned-myopic configs, eval_episodes stays 2400 | Outcome of the pre-registered rules 12.3–12.5 |
