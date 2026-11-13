# Literature track: final summary (search date 2026-11-13)

## 1. Highest-overlap work, and exactly how we differ (what reduces our novelty comes first)

1. **The SlateQ paper itself (Ie et al. 2019) already did our RQ1 and part of our RQ3.**
   - §7.1 compares SlateQ with a *learned γ = 0* myopic model at 10 candidates and k = 3, in essentially the same simulator.
   - §7.3 tests an exponential-cascade user model and reports SlateQ still ahead.
   - **Consequence:** RQ1 is a *replication*, and RQ3 is an *extension* of an existing robustness test.
   - **How we differ:**
     - an independent port;
     - 5 seeds with common random numbers and a pre-registered rule (the paper reports no seeds);
     - an added oracle baseline;
     - a graded misspecification ladder;
     - **sizes:** the paper used only m = 10, k = 3.
2. **GeMS (WSDM 2023)** already shows SlateQ struggling under click models that break its assumptions, and already uses a privileged short-term oracle.
   - We differ: we measure SlateQ *vs myopic* along a graded ladder in RecSim IE; we do not propose a method.
3. **Singha Roy et al. 2023 (RecSys) and 2025 (ACM TORS)** study SlateQ scaling with large item pools. **We could not read either** (ACM blocked automated access). They may overlap RQ2.
4. **Singha Roy et al. 2024 (INRA@RecSys)** compares SlateQ vs Greedy in RecSim with real data, at one size (300 candidates, k = 10, γ = 1).
5. **SlateFree (preprint)** varies catalog and slate size, but for convergence speed, with no myopic baseline.
6. **Pantea 2022 (BSc thesis)** compares SlateQ vs FullSlateQ at γ = 0.5 with no myopic baseline, and lists our γ question as future work.

**Not found** (sources searched on 2026-11-13): a study of the SlateQ-vs-myopic gap over a grid of candidate and slate sizes, with both a learned γ = 0 control and a privileged oracle. This is provisional until item 3 is read.

## 2. Allowed claims (details in POSITIONING.md)

- A controlled, pre-registered replication and extension; not a new method or state of the art.
- RQ1 replicated: +1.70 (95% CI [+1.54, +1.85]), about 1 %, 5 of 5 seeds.
- RQ2 extends one size to 14: clear in 14 of 14 (t-intervals agree, post-hoc); the gap grows with N and shrinks with k.
- **Headline vs the oracle:** +27.17 at (80, 3). The learned baseline degrades at large N under a budget frozen at (10, 3).
- RQ3: clear under mild and logit misspecification. Under RecSim's default cascade, not clearly different from zero (+0.22; one seed at −0.01), while SlateQ stays far above random. That cascade is much harsher than the SlateQ paper's, so the results are **not in conflict**.

## 3. What could not be verified

- Full texts of Singha Roy 2023 and 2025, and of Kaushik 2023 (closed).
- Google Scholar forward citations (not queried; OpenAlex used).
- KuaiSim's NeurIPS track.
- GeMS Table 2 values.
- An **end-to-end equivalence of our port** with RecSim's TF agent (only component tests exist).

## 4. Open questions for your decision

**a. Proposed diagnostics (none run; PROPOSED_DIAGNOSTICS.md).**

| Diagnostic | Cost | My view |
|---|---|---|
| D-1(a) matched learning rate at (10, 3) | ~20 min | Recommended |
| D-2 γ sensitivity | ~40 min | Optional |
| D-3 paper-like cascade | ~50 min | Needs a parameter decision; post-hoc and exploratory |

**b. Wording problems elsewhere (WORDING_ISSUES.md).**

- **P0:** the website and README say "only the planning horizon differs", but the learning rates differ.
- **P1:**
  - RESULTS.md says "largely disappears";
  - the PROTOCOL needs a clarification row;
  - the README RQ2 headline should include the oracle;
  - the third-party PDFs committed in `docs/papers/` (licence).

**c. Port equivalence.** Component-level evidence only. Say so in the report; no cheap fix exists.

**d. Your question about changing the grid or ladder: no.**

- Changing N, k or the rungs after seeing results would break the pre-registration and weaken every claim.
- Nothing in the literature makes our grid wrong. The SlateQ paper used a single size, so any grid is an extension.
- The only literature-motivated addition is D-3. It would be an *extra*, labelled exploratory, not a replacement.

## 5. To open yourself

**Five citations to check by hand:**

1. Ie et al. 2019, arXiv:1905.12767, §6.3, §6.5, §7.1, §7.3 and footnote 10 (pp. 17, 20-25).
2. Singha Roy et al. 2025, ACM TORS 4(1), doi 10.1145/3733241.
3. Singha Roy et al. 2023, RecSys, doi 10.1145/3604915.3608843.
4. Deffayet et al. 2023, GeMS, WSDM, doi 10.1145/3539597.3570412: §4 and Table 2.
5. Pantea 2022 thesis, §4-6 (github.com/lucapantea/research-project).

**Three links:**

- https://dl.acm.org/doi/10.1145/3733241
- https://dl.acm.org/doi/10.1145/3604915.3608843
- https://arxiv.org/abs/1905.12767

**Six papers to read, in order:**

1. SlateQ §6-7.
2. Singha Roy 2025 (TORS).
3. Singha Roy 2023 (RecSys).
4. GeMS.
5. Singha Roy 2024 (INRA).
6. SlateFree §5.

**After reading 2-3:** if either reports SlateQ-vs-myopic gaps across pool sizes, narrow the RQ2 novelty sentence (LIT_AUDIT A4).
