# Our setup: facts with evidence (S4, 2026-11-13)

Every statement below cites a file or a command run on 2026-11-13. Nothing here was changed; this is read-only.

## (a) Which SlateQ we ran, and what shows the port is faithful

### Agent definition

| Fact | Value | Evidence |
|---|---|---|
| Algorithm variant | **SARSA target** (on-policy TD with the next served slate), **top-k selection** for training and serving. This is RecSim's `slate_topk_sarsa`, the paper's **SARSA-TS**. | `src/slateq_study/agents/slateq.py` docstring lines 1-17; `sarsa_target()` (line 71); constructor default `selection="topk"` (line 205); RQ2 run configs set no `selection`, e.g. `results/raw/rq2/441aee29c2d6/seed0/config.yaml` |
| γ, SlateQ | **0.99** | Constructor default `gamma=0.99` (line 194); the run config does not override it; the checkpoint records `gamma: 0.99` (`torch.load(results/raw/rq2/441aee29c2d6/seed0/model.pt)` → `{'training_steps': 300000, 'updates': 70000, 'gamma': 0.99}`); PROTOCOL 12.1 |
| γ, learned-myopic | **0** (enforced) | `LearnedMyopicAgent` raises if γ ≠ 0 (lines 406-415); checkpoint `71faa57996eb/seed0/model.pt` records `gamma: 0.0` |
| Assumed choice model | Multinomial proportional on dot(user, doc), with no-click mass 1 and min_normalizer −1. Fixed inside the agent; RQ3 changes only the environment's true model. | docstring lines 6-8; `score_documents()` (line 38) |
| No-click handling | No-click enters the choice probabilities but has value 0; only clicked transitions are trained | docstring lines 10-13; DEVIATIONS D6 |
| Network and optimiser | Item-wise MLP [user, doc] → 256 → 32 → 1; centred RMSProp; batch 32; update every 4 steps after 20K warm-up; ε decays to 0.01 over 100K; ε_eval = 0 | PROTOCOL 12.1; constructor defaults lines 190-206 |
| Training budget | 300,000 env steps for both learned agents | checkpoint `training_steps: 300000` (both); PROTOCOL 12.6 |

### Paper vs our port

| | SlateQ paper | Ours |
|---|---|---|
| LTV γ | 1 (§7.1, p. 22) | 0.99 |
| Myopic γ | 0 (footnote 10, p. 17) | 0 (same) |
| Agent variant | SARSA-TS is one of several reported variants | SARSA-TS only |

### Evidence the port matches RecSim's reference agent

**What exists** (all in `tests/test_slateq.py`; all 12 tests pass: `pytest -q tests/test_slateq.py`, output `12 passed` on 2026-11-13):

- `test_scores_match_recsim_multinomial_proportional`: our scores equal RecSim's NumPy `MultinomialProportionalChoiceModel` scores (atol 1e-12) and its no-click score.
- `test_topk_selects_largest_s_times_q`: top-k rule equals the reference's `select_slate_topk` rule (score × Q).
- `test_sarsa_target_hand_computed`: SARSA target checked against a hand computation of the reference formula.
- `test_epsilon_schedule_matches_dopamine`: ε schedule equals Dopamine's linear decay.
- `test_greedy_matches_marginal_rule_and_is_near_optimal`: greedy selector (not used in the sweeps).
- `test_learned_myopic_forces_gamma_zero`, `test_target_sync_and_update_counts`, `test_training_budget_exact_and_eval_mode_stores_nothing`, and others: mechanics.

**What does not exist** (said plainly):

- RecSim's TF1 `SlateDecompQAgent` was **never run side by side** with our port. Its stack (TF1 + Dopamine) is excluded by D1, so there is **no end-to-end equivalence test** (DEVIATIONS D3).
- Optimiser details differ slightly. Torch RMSProp puts eps outside the square root; TF puts it inside (D8).
- The equivalence evidence is therefore **component-level only**: scoring, selection, target and schedule.

### Independent evidence that our SlateQ port is correct (no TensorFlow side-by-side run)

We did not run RecSim's original TF1 agent next to ours (its stack is excluded, D1). The evidence below is independent of that check. It shows the parts are right and the trained agents behave as theory predicts, but it is **not** proof that our numbers equal what the TF agent would produce.

| # | Evidence | What it checks | Source (re-run with) |
|---|---|---|---|
| 1 | Analytic unit tests: scores equal RecSim's own `MultinomialProportionalChoiceModel`; top-k = largest score × Q; SARSA target equals a hand computation of r + γ Σ P(j \| s', A') Q(s', j); ε schedule equals Dopamine's; learned-myopic cannot have γ ≠ 0; replay stores the next served slate and the terminal flag | Each formula of the decomposition and target, separately | `tests/test_slateq.py` (12 tests; `make test`) |
| 2 | γ = 0 calibration against the oracle (Phase 3, pre-registered check 3): learned-myopic recovered 97.2 % of the oracle's improvement over random (threshold 90 %) | A γ = 0 agent trained with our code learns the same click-maximising ranking that the oracle computes from the true user state | `results/phase3/ladder.json` (`3_calibration_recovery_mean` = 0.972) |
| 3 | Same calibration in the final runs: learned-myopic − oracle-myopic shows "no clear difference" in 7 of the 8 cells with N ≤ 20 (e.g. −0.09, CI [−0.24, +0.08] at (10, 3)); the exception is (20, 2) at −0.97 | The learned γ = 0 model matches a model that cannot be wrong about clicks, on fresh evaluation users | `results/rq2/gaps.csv`, rows "learned-myopic - oracle-myopic" |
| 4 | Q-value scale (Phase 3 check 4): learned-myopic's mean clicked-item Q is 3.95 (both seeds), close to one step of watch time (about 4); SlateQ's is 8.7 to 8.9, above one step but far below 4 / (1 − γ) = 400 | γ = 0 learns immediate reward; γ = 0.99 learns a multi-step value, shortened by the zero no-click value (D6) | `results/phase3/ladder.json` (`4_q_scale_*`) |
| 5 | Replay check: reloading the saved networks and replaying an evaluation user reproduces the recorded rewards exactly, for every agent | Saved models, evaluation and logging agree | `make demo` ("replay matches the recorded evaluation", run 2026-11-13 on the Phase 6b code) |
| 6 | Determinism: the same seed gives the same training; exploration never touches the global random generator | Common random numbers are valid | `tests/test_slateq.py::test_same_seed_same_training`, `::test_exploration_does_not_touch_global_rng` |
| 7 | Sanity of the environment wrapper: with the default choice model our environment produces the same trajectory as RecSim's own `create_environment` | Results come from RecSim's unmodified environment | `tests/test_envs.py` |

**Remaining gap (limitation):** the evidence is component-level plus behavioural. Small implementation differences from the TF agent (optimiser epsilon placement, ε schedule length, ε_eval = 0; D8) could change absolute numbers slightly. No test can rule out an effect of these on the size of the SlateQ advantage. Our results are therefore results for **our port**, faithful to RecSim's reference in every component we could test.

**Informal plausibility only** (different implementation, evaluation and seeds; context only, not evidence of equivalence):

- Our random baseline, learned-myopic and SlateQ at (10, 3) score 160.55, 167.50 and 169.20 (NUMBERS.md RQ1 table).
- The paper's §7.1 table reports Random 159.2, MYOP-TS 166.3 and SARSA-TS 168.4 (NOTES/ie2019slateq.md).

## (b) Learning rates: what "same agent, only γ differs" really means

### Facts

- **Selected configs** (`results/phase3/tune.json` → `selected`, PROTOCOL 12.6):
  - SlateQ: learning rate **1e-3**, target period 1000.
  - Learned-myopic: learning rate **2.5e-4**, target period 1000.
- **Correct wording:** same architecture, data, budget and tuning budget (9-config grid each, same seeds 100-101, same tune episodes). **The learning rate was tuned separately per agent.**
- "Identical network and optimizer; only the horizon differs" is **not accurate**. Lines that say this (DEVIATIONS D7, PROTOCOL 14.3, RECON, the agent docstring) are listed in WORDING_ISSUES.md. They are not edited here.

### Confound assessment from existing data only

Source: `results/phase3/tune.json` → `grid`. Tune stream, cell (10, 3), 2 seeds × 500 episodes each, read with `python -c "import json; ..."` on 2026-11-13.

| Learning rate | SlateQ (period 1000) | Learned-myopic (period 1000) | SlateQ − LM |
|---|---|---|---|
| 1e-4 | 169.88 | 168.29 | +1.59 |
| 2.5e-4 | 169.94 | 168.48 | +1.46 |
| 1e-3 | 170.22 | 168.31 | +1.91 |

- **At every matched learning rate SlateQ is higher.** All 9 SlateQ configs (169.51-170.22) are above all learned-myopic configs (168.29-168.48).
- For learned-myopic the target period has no effect: γ = 0 means the target network never enters the loss, so its three periods give identical values (PROTOCOL 12.6).
- **Conclusion (scoped):** at (10, 3), on tune-stream data, the sign and rough size of the gap do not depend on giving the agents different learning rates.
- **Limits:** 2 seeds, not the eval stream, one cell. **Untested:** whether the learning-rate choice contributes to the large gaps at N ≥ 40, where learned-myopic falls below the oracle. See PROPOSED_DIAGNOSTICS D-1.

## Other facts needed for positioning

| Fact | Evidence |
|---|---|
| "Catalog size" = candidates resampled every step (N = `num_candidates`, `resample_documents: true`) | DEVIATIONS D5; run config above |
| Oracle-myopic is privileged: it reads the true user state and ranks by click propensity under the true model; for the cascade it uses the proportional model (D11) | `src/slateq_study/agents/oracle.py`; DEVIATIONS D11 |
| RQ3 cascade = RecSim's `ProportionalCascadeChoiceModel` with RecSim's own Interest Evolution defaults: attention_prob 0.65, score_scaling 0.05 (numpy-2 compat subclass, D12). Per-position click probability = 0.65 × 0.05 × (score + 1) ≤ 0.065. | `third_party/recsim/recsim/environments/interest_evolution.py:433-434`; `third_party/recsim/recsim/choice_model.py:168-187`; PROTOCOL §15 ("much lower click rate") |
| No FullSlateQ data exists in `results/`. Only an action-count figure (F8) exists. | DEVIATIONS D9; `results/figures/F8_action_count.*`; NUMBERS.md has no FullSlateQ row |
| Seeds: 5 run seeds (0-4) × 2400 eval episodes, with common random numbers (same eval env seeds for every policy) | PROTOCOL §4, §6, 14; `analysis.gap_tables` refuses mismatched eval seeds |
