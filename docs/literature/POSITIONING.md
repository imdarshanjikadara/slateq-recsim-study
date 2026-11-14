# Positioning (S5, search date 2026-11-13)

Our numbers come from `docs/NUMBERS.md` (generated) and `docs/SUPPLEMENT_STATS.md` (post-hoc, supplementary). Claims about other papers come from `NOTES/` at E2 or higher.

**One-line position:** a controlled, pre-registered **replication and extension** of SlateQ's simulation result in RecSim Interest Evolution. It is not a new method and not a state-of-the-art comparison.

## (a) ALLOWED claims

| # | Allowed claim (wording to use) | Our evidence (NUMBERS.md / file) | Literature support (note, level) |
|---|---|---|---|
| A1 | "We replicate the SlateQ paper's simulated comparison of SlateQ against a myopic (γ = 0) baseline at 10 candidates and slate size 3, with an independent PyTorch port of RecSim's agent." | RQ1 table; OUR_SETUP_FACTS (a) | ie2019slateq (E3): §7.1, footnote 10 |
| A2 | "In our runs, SlateQ's return per session exceeds the learned-myopic baseline by +1.70 (95% CI [+1.54, +1.85], 5 of 5 seeds positive), about 1% of the baseline's 167.50." | RQ1 PRIMARY row; RQ3 matched row (+1.01%) | - |
| A3 | "The same direction as the original paper's simulation; magnitudes are not comparable (different implementation, seeds and evaluation)." | as A2 | ie2019slateq (E3) §7.1 table, context only |
| A4 | "The SlateQ paper reports simulation results at a single size (m = 10, k = 3). We measure how the gap changes over N ∈ {5, ..., 80} and k ∈ {2, 3, 5}." | RQ2 table | ie2019slateq (E3) §6.5 p. 22 |
| A5 | "Across the 14 grid cells the primary gap is clearly positive in all 14 (pre-registered rule); t-based intervals (post-hoc) agree. It grows with N and shrinks with k." | RQ2 table; verdict counts; SUPPLEMENT_STATS summary | - |
| A6 | "Against the privileged oracle-myopic, SlateQ's advantage is also clear in 14 of 15 cells (all except the k = N control) and grows from +1.60 at (10, 3) to +27.17 at (80, 3)." | RQ2 secondary table; RQ1 table | - |
| A7 | "Part of the large-N primary gap reflects the learned-myopic baseline falling below the oracle (−13.40 at (80, 3)), under a training budget and hyperparameters frozen at (10, 3)." | RQ2 secondary table; PROTOCOL 12.6 | - |
| A8 | "The degenerate control (N = k = 5) shows no difference (−0.01, CI [−0.06, +0.02]; t-interval also includes 0)." | RQ2 control row; SUPPLEMENT_STATS | - |
| A9 | "Under mild (no-click mass 3) and moderate (logit) misspecification the advantage remains clear (+1.12, +1.62). Under RecSim's proportional cascade with its default parameters, the advantage over the myopic baselines is not clearly different from zero (+0.22; one of five seeds at −0.01; t-interval includes 0), while SlateQ stays far above random (108.00 vs 84.19)." | RQ3 tables; SUPPLEMENT_STATS | - |
| A10 | "The SlateQ paper reports SlateQ still outperforming its myopic baseline under an exponential cascade. Our cascade differs from theirs in parameterisation and click rate, so the results are not in conflict and are not directly comparable." | RQ3 mechanism table | ie2019slateq (E3) §6.3, §7.3; DISCREPANCIES.md |
| A11 | "Methodologically, we combine a learned γ = 0 control, a privileged oracle, common random numbers, 5 seeds and a pre-registered decision rule. To our knowledge, among the sources we reviewed (search date 2026-11-13), no single study of SlateQ combined all of these." | PROTOCOL; NUMBERS | OVERLAP_MATRIX (each element exists separately in prior work) |
| A12 | "SlateQ's assumptions (single choice per slate, known choice model) are criticised and relaxed in later work (GeMS, SlateFree)." | - | deffayet2023gems (E3); giovanidis2022slatefree (E3) |
| A13 | "SlateQ and RecSim remain in use as a baseline and simulator in 2024-2025 work." | - | singharoy2024news (E3); singharoy2023scalable (E3); singharoy2025dontgetbored (E3); deng2025fedslate (E2) |
| A14 | "Simulation-based evaluation avoids the myopic bias of next-item offline protocols, but results hold only for the simulator." | - | deffayet2022offline (E2-E3) |
| A15 | Motivation wording about real systems (use only this): "The SlateQ paper notes that practical recommender systems largely focus on myopic prediction of a user's immediate response (Ie et al. 2019, p. 2), such as predicted click-through rate or watch time (p. 4). The same paper reports a live experiment on YouTube in which SlateQ improved engagement over myopic recommendations (p. 3)." Our oracle-myopic baseline is the simulator's best click-maximiser. | - | ie2019slateq (E3): arXiv version pp. 2-4 (checked 2026-11-13) |

## (b) DISALLOWED claims (do not write these anywhere)

| Disallowed | Why |
|---|---|
| "first", "novel", "new method", "novel algorithm" | Not supported; RQ1 is a replication, and no method is new. |
| "state of the art", "outperforms recent methods" | No recent method was run. |
| "SlateQ greatly / substantially / dramatically outperforms" (for RQ1) | The RQ1 effect is about 1% (+1.70 on 167.50). |
| "identical network and optimizer; only the horizon differs" | Learning rates differ (1e-3 vs 2.5e-4). Use: "same architecture, data, budget and tuning budget; learning rate tuned per agent" (OUR_SETUP_FACTS b). |
| "the advantage disappears / vanishes under misspecification" (unqualified) | It is not clearly different from zero only under our cascade setting, with qualifiers: one seed about zero, SlateQ still far above random, and a cascade harsher than the paper's. |
| "SlateQ's advantage grows to +40 because SlateQ improves" (unqualified) | Part of the growth is the learned-myopic baseline degrading; state both (A6, A7). |
| "the decomposition is necessary / FullSlateQ is intractable here" (as an empirical result) | No FullSlateQ data; only an action-count figure. |
| Causal claims about real users or platforms | Simulation only. |
| "YouTube / Netflix optimise for clicks" (or any claim about what a named platform does today) | No source opened in this review supports it. The SlateQ paper (Google/YouTube authors) reports YouTube testing a long-term method. Use A15 instead, and say "click-maximising recommender" for our baseline. |
| "Our results contradict the SlateQ paper's robustness result" | Settings differ (DISCREPANCIES.md); not comparable. |
| "Nobody has studied this" / "has not been done" | Use the safe phrasings below; the search is not exhaustive (Google Scholar not queried). |
| Placing our numbers beside another paper's as a comparison | Only "different environment / implementation, context only". |

## (c) SAFE novelty phrasings

- "To our knowledge, among the sources we reviewed (search date 2026-11-13; arXiv, OpenAlex forward citations of SlateQ and RecSim, Crossref, CEUR-WS), we did not find a study that reports how the SlateQ-versus-myopic gap changes over a grid of candidate-set sizes and slate sizes."
  - The two Singha Roy et al. scaling papers (RecSys 2023; ACM TORS), read in full on 2026-11-13, use 300 and 2,000 candidates but compare SlateQ with their own actor at γ = 1 and skip a myopic baseline on purpose. They support the theme "SlateQ with many candidates" but not the gap question, so the sentence above stands.
- "We extend the SlateQ paper's single-setting simulation (m = 10, k = 3) to 14 settings plus a control."
- "We complement the paper's single cascade robustness test with a graded three-step ladder, judged against both a learned and a privileged myopic baseline."
- "Our contribution is methodological rigour and measurement, not a new algorithm."
