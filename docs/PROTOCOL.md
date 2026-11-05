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

## 12. To be fixed in Phase 3, BEFORE any sweep (placeholders)

- Training budget (environment steps per learned run), identical for all learned agents: **TBD (Phase 3)**.
- Tuning grid (≤ 4 knobs × ≤ 3 values), tuning cells, tuning seeds (tune stream), budget, identical for SlateQ and learned-myopic: **TBD (Phase 3)**.
- FullSlateQ action-count cap: **TBD (Phase 3)**.

## 13. Change log

| Date | Change | Reason |
|---|---|---|
| 2026-11-05 | Protocol created; eval_episodes = 2400 from the variance study | Phase 2 |
