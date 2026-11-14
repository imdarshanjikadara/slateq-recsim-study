# singharoy2023scalable: Singha Roy et al. 2023 (RecSys 2023)

## Citation and status

- Singha Roy, D'Amico, Tragos, Lawlor, Hurley, "Scalable Deep Q-Learning for Session-Based Slate Recommendation", RecSys 2023, pp. 877-882, doi 10.1145/3604915.3608843. Peer-reviewed short paper (6 pages). CC BY 4.0 (stated on p. 877).
- **Evidence level: E3.** Full text read on 2026-11-13 from the PDF the student downloaded (kept locally in `docs/papers/lit/`, not committed).

## What they do (own words)

- Problem: SlateQ must evaluate its item-wise Q-network on every candidate when it builds a slate, which is slow when there are thousands of candidates (§1, §2.1).
- Method: "SlateWolpertinger", an actor that proposes a point in item-feature space; only the k-nearest candidates are scored by SlateQ's Q-network (§3, Algorithm 1).
- Simulator: their own PyTorch reimplementation of RecSim-style dynamics. Satisfaction mixes interest and quality (weight 0.25), budget 200, document length 4, null-item budget cost 0.5 (§4, p. 880).
- Experiments (§5): SlateQ vs SlateWolpertinger using 5 %, 10 % and 20 % of candidates; **300 and 2000 candidates per user; slate size 5; γ = 1.0**; 5 seeded runs; paired t-tests; serving-time curve for 300-2000 candidates (Fig. 3).

## Is there a myopic baseline? No.

- They say they skip it on purpose and set γ = 1: "As SlateQ has already been shown to perform well over myopic recommender" (p. 881, §5.1).
- Table 1 (p. 882) reports only SlateQ and SlateWolpertinger variants.

## Overlap with our study

| Our element | This paper | Overlap |
|---|---|---|
| RQ1 SlateQ vs myopic | not run (explicitly skipped) | none |
| RQ2 gap vs N and k | two candidate sizes (300, 2000), one slate size (5), but **no gap to a myopic baseline**; the size question is about serving time and the approximation | **none for the gap question**; shares the general theme "SlateQ at larger candidate pools" |
| RQ3 choice-model misspecification | not studied | none |
| Phase 6b E2 (γ) | only γ = 1 | none |

## How we cite it

- As related work on scaling SlateQ's slate construction to large candidate pools; it does not measure the long-term-vs-myopic gap.
- Its remark that the SlateQ paper used 10 candidates (p. 881, §5.2) agrees with our NOTE on ie2019slateq.
- No number from it is compared with ours (different simulator and metrics).
