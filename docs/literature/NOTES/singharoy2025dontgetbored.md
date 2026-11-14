# singharoy2025dontgetbored: Singha Roy et al. (ACM TORS)

## Citation and status

- Singha Roy, D'Amico, Tragos, Lawlor, Hurley, "Don't Get Bored: Enhancing Scalability and Diversity in Session-Based Slate Recommendation", ACM Transactions on Recommender Systems 4(1), Article 8, pp. 8:1-8:24, doi 10.1145/3733241. Peer-reviewed journal. CC BY 4.0.
- **Date:** the PDF's footer says "Publication date: July 2026" (© 2026). Crossref gave 2025, probably the online-first date. The bib key keeps "2025" so that existing references still resolve; `references.bib` records both dates.
- **Evidence level: E3.** Full text read on 2026-11-13 from the PDF the student downloaded (kept locally, not committed).

## What they do (own words)

- An extended journal version of singharoy2023scalable. SlateWolpertinger now has two actor types: a "proto-item" (one point in item space) and a "proto-slate" (one point per slate position) (§4).
- Simulator: their PyTorch RecSim-inspired environment (§5), with two user types (§5.2.1):
  - **decisive** users (the RecSim-like model);
  - **explorative** users, who get "bored": after 5 consecutive items of the same topic, the interest in it is set to -1.
- Experiments (§6): SlateQ vs SlateWolpertinger (5 %, 10 %, 20 % of candidates); **300 and 2,000 candidates; slate size 5; γ = 1.0**; 5 seeded runs; serving time.
- Finding (§6.2, §7): for explorative users, the proto-slate actor beats SlateQ; for decisive users it matches SlateQ while serving faster.

## Is there a myopic baseline? No.

- As in the 2023 paper, they skip it on purpose: "As SlateQ has already been shown to perform well over a myopic recommender" (p. 8:14, §6.1.1). They use γ = 1.0.
- Tables 2 and 3 compare only SlateQ and SlateWolpertinger variants.

## Overlap with our study

| Our element | This paper | Overlap |
|---|---|---|
| RQ1 SlateQ vs myopic | not run | none |
| RQ2 gap vs N and k | two candidate sizes, one slate size, no myopic baseline, so no gap | **none for the gap question**; same broad theme (SlateQ with many candidates) |
| RQ3 wrong choice model | They change user *dynamics* (boredom), not the choice model SlateQ assumes, and compare SlateQ with their actor, not with a myopic policy. | low |
| Phase 6b E2 (γ) | only γ = 1 | none |

## How we cite it

- As the journal version of the SlateQ-scalability line of work, and as an example of a different user-behaviour variation (boredom), which we do not study.
- The earlier abstract-only reading (E1) flagged a possible RQ2 overlap; the full text shows there is none for the gap question.
