# deffayet2023gems: Deffayet et al. 2023, GeMS (WSDM 2023)

## Citation and status

- Deffayet, Thonet, Renders, de Rijke, "Generative Slate Recommendation with Reinforcement Learning", WSDM 2023, pp. 580-588, doi 10.1145/3539597.3570412. Peer-reviewed.
- Code: github.com/naver/gems.
- **Evidence level:** E3 for the text: §1-§6 read, including the baselines, simulator and results discussion. Table 2's numbers were not transcribed reliably (PDF extraction garbled them), so no number from Table 2 is used.

## Claim (own words)

- Prior slate RL methods tame the combinatorial action space with decompositions that rely on restrictive assumptions (§1, §4, Table 1).
- GeMS instead learns a VAE latent space of slates from logged data and runs SAC in that space.
- Across 6 simulator variants it beats the baselines on average (§6.1).

## Setup (§4-5)

| Item | Value |
|---|---|
| Collection / slate size | About 1000 items; **slate size 10** (§1) |
| Simulator | Their own. Boredom and influence dynamics. A **position-based click model** with variants TopDown, Mixed and DivPen; focused vs diffuse item embeddings. |
| Baselines | Short-term oracle (**privileged**: true embeddings, maximises immediate relevance), SAC+TopK (ideal / MF), **SlateQ (QL-TT-TS variant, given the true relevance and click model)**, Random, REINFORCE+SoftMax, SAC+WkNN |
| Seeds | **10 seeded runs**; 95 % CIs; significance markers in Table 2 |
| Metric | Cumulative clicks per test episode |

## Statements about SlateQ

- Table 1 lists SlateQ's assumptions. In their setup it needs access to the true relevance and click model (CM), which they call an unfair advantage (§4).
- They attribute SlateQ's weak performance to its approximate optimisation and its "restrictive single-click assumption" (§6.1, PDF page 7). Quote under 15 words.

## Overlap

| RQ | Overlap |
|---|---|
| RQ1 | Partial. They also include a **privileged short-term oracle**, like our oracle-myopic, and SlateQ. But their question is GeMS vs the baselines, not SlateQ vs myopic. |
| RQ2 | Not done (one collection size). |
| RQ3 | **Partial.** SlateQ runs in environments whose click model (position-based, Mixed, DivPen) departs from its single-click conditional assumption. This is a misspecification test in substance, but not graded and not framed as SlateQ vs myopic. |
| Methodology | Partial. 10 seeds and CIs. No learned γ = 0 control. |

**Comparable to ours?** No: different simulator and metric.

## Why it matters to us

- It is the main peer-reviewed critique of SlateQ's assumptions.
- It reduces the novelty of saying "SlateQ is sensitive to the click model".
