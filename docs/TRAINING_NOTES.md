# Phase 3 — Training notes (SlateQ PyTorch port)

All rules below were fixed in `docs/PROTOCOL.md` §12 before the runs. Every number is read from a file in
`results/phase3/` produced by `scripts/phase3.py`. All Phase 3 runs train on the **train** stream and are scored on the
**tune** stream (500 episodes per run); the eval stream is untouched. These are **not** RQ1 results.

Reproduce: `uv run python scripts/phase3.py {ladder|budget|tune|final}` (add `--analyze-only` to re-analyse).

## Implementation summary

`src/slateq_study/agents/slateq.py`, tested in `tests/test_slateq.py` (12 tests):

- Scores equal RecSim's NumPy `MultinomialProportionalChoiceModel` to 1e-12 (the env's default true model).
- Top-k selection; greedy selection checked against the marginal rule and brute force.
- SARSA target matches a hand calculation of Eq. 19 with RecSim's normalisation (no-click in the denominator), including terminal masking and γ = 0.
- dopamine's ε schedule; compact replay (one-hot docs stored as cluster ids) with a round-trip test.
- Transitions store the next served slate and next candidates (SARSA). The step budget is exact. Eval mode stores nothing.
- Target sync and update counts follow the schedule. Exploration never touches the global `np.random`. Same seed gives identical training.
- Found and fixed while testing: network initialisation drew from torch's global RNG. It now depends only on the agent seed.

## Sanity ladder — cell (5,2), seeds 100–101, defaults (PROTOCOL 12.1), 300K steps

Source: `results/phase3/ladder.json`. **All four checks passed.**

| Check | Criterion (12.7) | Result |
|---|---|---|
| 1 Plumbing | finite loss/Q, replay = steps, final ε = 0.01, ≥ 1 target sync | **pass**: both agents, both seeds: replay 300000, ε 0.01, 70000 updates, 35 target syncs |
| 2 Beats random | paired mean diff > 2 SE, each agent and seed | **pass**: SlateQ +8.78 (SE 0.67) / +9.93 (0.67); learned-myopic +8.17 (0.66) / +8.91 (0.64) |
| 3 Calibration | learned-myopic recovers ≥ 90% of oracle's gain over random | **pass**: 0.988 (seed 100), 0.957 (seed 101), mean 0.972. Oracle − random: +8.27 (SE 0.67) / +9.31 (0.64) |
| 4 Q-scale | LM mean clicked Q in [2, 6]; SlateQ's larger and < 400 | **pass**: LM 3.95 / 3.95; SlateQ 8.86 / 8.67 |

Interpretation:
- **Calibration.** With γ = 0 the learned item value is close to the immediate watch time (≈ 4) for every item. Top-k by score × Q therefore reproduces the oracle's ranking, which is why learned-myopic nearly matches the oracle. This confirms that the reward, terminal handling, observations and eval mode are wired correctly.
- **SlateQ's Q-scale.** Its learned Q (≈ 8.7) is far below the 4/(1−γ) = 400 ceiling. This is what the reference's null-item handling implies (DEVIATIONS D6): the no-click option takes probability mass in the target but contributes no value, so each bootstrap step is effectively discounted by γ · P(click | slate), not by γ. The reference SlateQ's effective planning horizon is therefore much shorter than γ = 0.99 suggests. This is a mechanism to discuss in the report, not a measured result.

## Training budget rule (T2) — SlateQ defaults, cell (10,3), seeds 100–102

Source: `results/phase3/budget.json`. Curve points are taken at the first episode boundary at or after each 50K mark.

| Seed | reward @ ≈300K | reward @ 500K | difference |
|---|---|---|---|
| 100 | 173.55 | 173.15 | −0.40 |
| 101 | 170.08 | 169.67 | −0.41 |
| 102 | 168.95 | 169.35 | +0.40 |

mean(d) = −0.137 vs threshold 2·SD/√3 = 0.535, so **the budget is 300,000 environment steps** for every learned agent and cell. The curves are flat from about 100K steps on. (Levels differ between seeds because each seed's tune episodes are different users.)

Wall clock: a 300K-step run at (5,2) trains in about 8 minutes, one process (`train_wall_clock_sec` in each run's `meta.json`).

## Tuning (T3) — cell (10,3), seeds 100–101, 300K steps, 9 configs per agent

Source: `results/phase3/tune.json`. Values are mean tune-stream total reward over the 2 seeds (500 episodes each).

| lr \ target period | SlateQ 1000 | SlateQ 4000 | SlateQ 8000 | LM 1000 | LM 4000 | LM 8000 |
|---|---|---|---|---|---|---|
| 1e-4 | 169.88 | 169.95 | 169.92 | 168.29 | 168.29 | 168.29 |
| 2.5e-4 | 169.94 | 169.93 | 169.82 | 168.48 | 168.48 | 168.48 |
| 1e-3 | **170.22** | 169.86 | 169.51 | 168.31 | 168.31 | 168.31 |

Selected (rule 12.4, frozen in PROTOCOL 12.6): **SlateQ lr 1e-3, period 1000**; **learned-myopic lr 2.5e-4, period 1000**.
References on the same tune episodes: random 160.88 / 160.28, oracle-myopic 168.74 / 168.16 (seeds 100 / 101).

Observations:
- The whole SlateQ grid lies between 169.51 and 170.22, and learned-myopic between 168.29 and 168.48. Within-seed differences between configs are small compared with the episode-level SD (~6–7 reward, below). The selection is therefore close to arbitrary within each agent's grid. That is expected and harmless: the rule was fixed in advance, and both agents got the same grid and budget.
- For learned-myopic the target period has no effect at all (identical values in each row). With γ = 0 the bootstrap term is multiplied by zero, so the target network never enters the loss. This is a useful consistency check on the implementation, not a tuning result.
- These are tuning numbers on 2 seeds and the tune stream. They are **not** evidence for RQ1.

## Episode-count re-check (T4)

Source: `results/phase3/tune.json` (`episode_recheck`). Paired SD of (SlateQ − learned-myopic) per episode for the two selected configs: 7.17 (seed 100), 6.38 (seed 101). Required n = ⌈(SD/0.5)²⌉ = 206 / 163, far below 2400, so **eval_episodes stays 2400** (it is never lowered).

## Final curves (check 5) — cell (10,3), seeds 200–202, frozen configs

Source: `results/phase3/final.json`. Figure: `results/figures/phase3_learning_curves.png` (and `.pdf`). Curve points use 200 tune-stream episodes (the same episodes at every point of a seed); end-of-training scores use 500 tune-stream episodes. **Check 5 passes**: all curve values are finite.

| Seed | SlateQ | Learned-myopic | Oracle-myopic | Random | SlateQ − LM, paired (SE) |
|---|---|---|---|---|---|
| 200 | 169.62 | 167.81 | 167.81 | 161.32 | +1.81 (0.29) |
| 201 | 169.53 | 168.64 | 168.45 | 160.78 | +0.90 (0.25) |
| 202 | 169.19 | 168.05 | 168.03 | 159.95 | +1.14 (0.24) |

Curve means over the 3 seeds (SlateQ / learned-myopic): 50K 169.82 / 168.70, 300K 169.93 / 168.81. Both curves are flat after the first 50K steps, consistent with the budget rule.

Observations (Phase 3 tune stream, 3 seeds; **not the RQ1 result**, which uses run seeds 0–4 on the eval stream):
- Learned-myopic tracks the oracle-myopic closely on every seed, as the ladder's calibration check predicted.
- SlateQ is above learned-myopic on all three seeds. The direction matches the SlateQ paper's simulation; the size is for Phase 5 to measure under the protocol.
- **Untrained network (step 0).** Before any update both agents share the same network (same agent seed), so the step-0 points coincide: 173.06, 162.95, 178.18 on seeds 200–202 (mean 171.40, SD 7.75). On two seeds this arbitrary fixed ranking scores above every trained agent on the same 200 episodes. A plausible explanation, not yet tested: a fixed ranking that happens to prefer high-quality clusters lengthens sessions (clicked quality refunds time budget), which can matter more than per-step click probability. This fits the Phase 2 finding that the oracle-myopic has shorter sessions and no better clicked quality than random. It is flagged for the report as an open question about how much long-term value is available in this environment.
