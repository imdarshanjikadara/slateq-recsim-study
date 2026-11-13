# giovanidis2022slatefree: Giovanidis 2022, SlateFree (arXiv preprint)

## Citation and status

- A. Giovanidis, "SlateFree: a Model-Free Decomposition for Reinforcement Learning with Slate Actions", arXiv:2209.01876.
- **Preprint**; no peer-reviewed version found (searched 2026-11-13).
- **Evidence level:** E3 (theory sections skimmed; experiments §5 read).

## Claim (own words)

- The slate Q-function can be decomposed **without** a known user choice model: SlateFree learns item-level values for all slate items.
- In tabular experiments it converges faster than SlateQ. In the larger case, SlateQ did not solve the task within 1M episodes (§5, pp. 7-8).

## Setup (§5)

| Item | Value |
|---|---|
| Model | Tabular; synthetic catalog walk with costs (minimisation); three artificial user choice behaviours |
| Catalog / slate sizes | **K = 10, N = 4** (small) and **K = 100, N = 10** (large); **N varied in {1, ..., 5} at K = 10** (§5C) |
| Discount factor | **γ = 0.85** |
| Comparison | SlateQ with greedy selection; vanilla Q and SARSA |
| Myopic baseline | **None** |
| Seeds | Not stated; curves smoothed over windows |

## Overlap

| RQ | Overlap |
|---|---|
| RQ1 | Not done (no myopic baseline). |
| RQ2 | **Partial.** Varies catalog size and slate size, but measures **convergence speed** of SlateQ vs SlateFree, not the SlateQ-vs-myopic gap. |
| RQ3 | **Partial in spirit.** SlateFree's motivation is SlateQ's reliance on a known choice model. Their user behaviours are not SlateQ's assumed model, but no graded misspecification is run. |

**Comparable to ours?** No: tabular, a cost-minimisation task, a different question.
