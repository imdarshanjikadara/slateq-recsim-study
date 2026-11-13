# deffayet2022offline: Deffayet et al. 2022 (ACM SIGIR Forum)

- **Status:** ACM SIGIR Forum 56(2), Dec. 2022, pp. 1-14, doi 10.1145/3582900.3582905; arXiv:2301.00993. A perspective paper.
- **Evidence level:** E2-E3 (abstract, introduction and §4.1 read).
- **Claim (own words):**
  - The common offline next-item-prediction protocol is unsuitable for evaluating RL recommenders.
  - It is myopic: it rewards one-shot prediction and ignores the causal effect of recommendations on later interactions (§4.1).
  - The authors list further shortcomings and suggest alternatives, including simulation.
- **Use:**
  - Supports our choice to evaluate by **online interaction in a simulator** (return per session) rather than an offline next-item metric.
  - Also a reminder that simulator results are only as valid as the simulator.
