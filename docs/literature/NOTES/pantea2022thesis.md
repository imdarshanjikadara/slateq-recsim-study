# pantea2022thesis: Pantea 2022 (TU Delft BSc thesis)

## Citation and status

- Petru-Luca Pantea, "Adapting to Dynamic User Preferences in Recommendation Systems via Deep Reinforcement Learning".
- BSc thesis, TU Delft, dated 19 June 2022. **Not peer-reviewed.**
- The PDF was taken from github.com/lucapantea/research-project (Apache-2.0), because the TU Delft repository file is not public.
- **Evidence level:** E3 (full text read; 8 pages).

## Claim (own words)

- Under non-stationary user preferences in a RecSim-built environment, SlateQ gives higher engagement than FullSlateQ: an average improvement of about 10.57% over FullSlateQ (§5.1).
- With γ = 0.5, both agents behave largely myopically and fail to trade short-term interest for quality (§5.2).

## Setup (§4.1)

| Item | Value |
|---|---|
| Environment | RecSim with a **custom** document/user model; preference-shift dynamics added; Dopamine |
| Users and documents | Budget 500; document length ~ N(5, 1); no-click penalty 1 |
| Candidates / slate size / topics | **10 items, slate size 2**, 20 topics |
| Discount factor | **γ = 0.5** (§4.3, §5.2) |
| Seeds | **3 seeds**, averaged; results stated as "within a 95% confidence interval" |
| Agents | Random, tabular Q-learning, FullSlateQ, SlateQ |
| Myopic baseline | **None** (neither learned nor oracle) |
| Choice model | Multinomial proportional (§3.1.3); no misspecification experiment |

## Results (context only: different environment)

- Tables 1-3 report return under stationary, mild and high-frequency dynamics.
- SlateQ is +9.2 % to +14.2 % over Random. These are the thesis's own percentages, relative to Random.

## Limitations stated (§6)

- A linear preference-shift model.
- A stylised environment.
- **Future work:** try other discount factors, to evaluate whether long-term optimisation beats myopic approaches.

## Overlap

| RQ | Overlap |
|---|---|
| RQ1 | Partial. SlateQ is studied in RecSim, but there is no myopic baseline, and γ = 0.5 instead of near 1. Our design (γ = 0.99 vs a γ = 0 learned baseline) addresses exactly the future-work item the thesis states. |
| RQ2 | Not done: one size (10, 2). |
| RQ3 | Not done. |
| Methodology | Not done: 3 seeds and no paired design are described. |

**Comparable to ours?** No: different environment dynamics, γ, slate size and baselines.

## Related publication

A 2023 IEEE conference paper by different authors (kaushik2023gcitc) reports the same comparison, with a 10.57 % figure and a "moderate discount factor" finding in its abstract. See that note. The relationship between the two is not investigated here.
