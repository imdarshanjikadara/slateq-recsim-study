# Overlap matrix (S5, search date 2026-11-13)

## Legend

| Cell value | Meaning |
|---|---|
| **done** | The paper does this |
| **partly** | Related but different (see note) |
| **not found** | Not found in the paper as read |
| **n/a** | Not applicable |

Rows are limited to claims our data supports. There is **no FullSlateQ row**, because `results/` contains no FullSlateQ runs (DEVIATIONS D9; OUR_SETUP_FACTS).

## Matrix

| Our claim / design element | SlateQ paper (ie2019slateq, E3) | GeMS (deffayet2023gems, E3) | Singha Roy 2024 (singharoy2024news, E3) | SlateFree (giovanidis2022slatefree, E3) | Pantea 2022 (pantea2022thesis, E3) | Singha Roy 2025 TORS (singharoy2025dontgetbored, E3) | Singha Roy 2023 RecSys (singharoy2023scalable, E3) |
|---|---|---|---|---|---|---|---|
| **RQ1:** SlateQ vs myopic, return per session, RecSim IE, N=10, k=3 | **done** (§7.1, p. 23: m=10, k=3, MYOP learned with γ=0) | partly (SlateQ and a short-term oracle in another simulator; metric = clicks) | partly (SlateQ vs Greedy; real-data RecSim; hit ratio) | not found (no myopic baseline) | partly (SlateQ in RecSim, no myopic baseline, γ=0.5) | not found (myopic baseline skipped on purpose, γ = 1; p. 8:14) | not found (myopic baseline skipped on purpose, γ = 1; p. 881) |
| **RQ2:** gap vs candidates N (5-80) | **not found** (only m=10 in simulation, p. 22) | not found (one collection size) | partly (candidate-subset % varied for inference cost, not the gap) | partly (K=10 and K=100; convergence, not the gap to myopic) | not found | partly (300 and 2,000 candidates, but SlateQ vs their actor; no gap to myopic) | partly (300 and 2,000 candidates, but SlateQ vs their actor; no gap to myopic) |
| **RQ2:** gap vs slate size k (2, 3, 5) | not found (k=3 only) | not found (k=10) | not found (k=10) | partly (N=1-5 at K=10; convergence only) | not found (k=2) | not found (k = 5 only) | not found (k = 5 only) |
| **RQ3:** graded misspecification (no-click mass, logit, cascade) | **partly** (one cascade setting, §7.3, p. 25; no grading) | partly (several click models; not graded; not vs myopic) | not found | partly (motivation: unknown choice model; no ladder) | not found | partly (changes user dynamics: "bored" explorative users; compared with their actor, not with myopic; no choice-model mismatch) | not found |
| **Method:** learned γ=0 control with the same architecture | **done** (MYOP = γ=0 Q-model, footnote 10, p. 17) | not found | not found (Greedy uses the choice model, not a γ=0 Q-model) | n/a | not found | not found | not found |
| **Method:** privileged oracle-myopic | not found | **done** (short-term oracle, §4) | not found | n/a | not found | not found | not found |
| **Method:** common random numbers (paired evaluation users) | not found (not stated) | not found (not stated) | partly (all seeds tested on the same 300 sessions; paired t-tests) | not found | not found | partly (each seed's model tested on the same 100 users; paired t-tests) | partly (each seed's model tested on the same 100 users; paired t-tests) |
| **Method:** ≥5 seeds with per-seed reporting | not found (seeds not reported) | done (10 seeds) | done (5 seeds) | not found | partly (3 seeds) | done (5 seeds) | done (5 seeds) |
| **Method:** pre-registered analysis plan | not found | not found | not found | not found | not found | not found | not found |
| **Method:** gap tested against both a learned and an oracle myopic baseline | not found | not found | not found | n/a | not found | not found | not found |

## Reading the matrix

1. **RQ1 is a replication.** The SlateQ paper already compares SlateQ with a learned γ=0 myopic model at our exact primary cell. Our contribution for RQ1 is independent re-measurement under a stricter protocol: 5 seeds, common random numbers, a pre-registered verdict rule, and an added oracle baseline.
2. **RQ2 has the least overlap.** The two Singha Roy scaling papers (RecSys 2023; ACM TORS, read in full on 2026-11-13) use larger candidate pools (300 and 2,000), but they compare SlateQ with their own faster actor at γ = 1 and leave out a myopic baseline on purpose. So they do not measure the SlateQ-versus-myopic gap, and they use one slate size. Our RQ2 novelty sentence (POSITIONING c) therefore stands as written, without the earlier caveat.
3. **RQ3 overlaps the SlateQ paper's §7.3 and GeMS.** What is ours is the *graded* ladder with a learned and an oracle baseline. The *finding* that the advantage shrinks to near zero under our cascade differs from §7.3's; see DISCREPANCIES.md.
4. **Methodology:** the combination of a learned γ=0 control, a privileged oracle, common random numbers and a pre-registered rule was not found in any single paper read. The individual elements all exist in prior work.
