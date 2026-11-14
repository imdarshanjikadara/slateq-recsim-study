# Literature track progress

| Stage | Status | Notes |
|---|---|---|
| S0 setup | done 2026-11-13 | Web access confirmed: arXiv API, Semantic Scholar API (rate-limited), curl to publisher pages, pdftotext. Google Scholar not scriptable. |
| S1 seed verification | done 2026-11-13 | 23 seeds verified (SEED_VERIFIED.md); 5 metadata corrections; references.bib from verified metadata only. |
| S2 systematic search | done 2026-11-13 | 369 forward citations (OpenAlex), 43 arXiv queries, S2 (rate-limited), backward chaining. CANDIDATES.md. |
| S3 deep reading | done 2026-11-13 | E3: SlateQ, GeMS, Pantea, Singha Roy 2024, SlateFree. Singha Roy 2023 + 2025 blocked (ACM 403). 25 NOTES. |
| S4 our-side facts | done 2026-11-13 | OUR_SETUP_FACTS.md: SARSA-TS, γ 0.99 vs 0 (from checkpoints), lr confound assessed on tune data; 12 port tests pass. |
| S5 overlap / positioning | done 2026-11-13 | OVERLAP_MATRIX.md, POSITIONING.md. |
| S6 discrepancies, supplement stats, proposed diagnostics | done 2026-11-13 | DISCREPANCIES.md, docs/SUPPLEMENT_STATS.md (scripts/supplement_stats.py), PROPOSED_DIAGNOSTICS.md (none run). |
| S7 related work draft + checks | done 2026-11-13 | RELATED_WORK_DRAFT.md (REPORT.md absent), citation check, WORDING_ISSUES.md. |
| S8 defense Q&A | done 2026-11-13 | docs/QA_LITERATURE.md incl. slide spec. |
| S9 self-audit, final summary, commit | done 2026-11-13 | LIT_AUDIT.md (1 P0 fixed, P1 fixed except open A4/A11), FINAL_SUMMARY.md. |

## Open issues
- ~~Singha Roy 2023 and 2025 full texts~~: resolved 2026-11-13 (student supplied PDFs; read to E3; no RQ2 overlap).
- Google Scholar not queried.
- docs/papers/slateq.pdf and recsim.pdf are committed in the public repo (arXiv licence may not permit redistribution) - flagged in WORDING_ISSUES/FINAL_SUMMARY.

## Phase 6b log (2026-11-13)

| Step | Status | Notes |
|---|---|---|
| Backup of results/raw | done | Two copies (D: and C:), 3,947 files, SHA-256 manifest verified on both. Outside the repo. |
| PROTOCOL 16 + DEVIATIONS D13-D16 | done | Registered after the Phase 6 results were seen, before any Phase 6b run; commit "phase 6b: register follow-up experiments E1-E5 (PROTOCOL 16) before any run". |
| Code | done | Agent variants in the sweep runner; SlateQ paper cascade (`src/slateq_study/paper_cascade.py`); tests 113 passed; `make demo` replay check passed. |
| Sweeps | done 2026-11-14 | 80/80 runs ok (E4 20, E1/E2 50, E3 10); none failed, none repeated. Order: phase6b_cascade (E4) -> phase6b (E1, E2) -> phase6b_budget (E3), 4 workers. Log: results/logs/phase6b_chain.log. |
| Chain restart | done | The first chain stopped after E4: the runner refuses a dirty tree, and E4 had written results/phase6b_cascade/runs.csv. That table was committed ("phase 6b: E4 sweep status table"), then phase6b was launched from a clean tree; phase6b_budget was launched with --allow-dirty, because only result tables and docs were uncommitted (src unchanged). |
| Analysis, NUMBERS, figures, site data | done 2026-11-14 | scripts/phase6b_analyze.py (fixed before results); NUMBERS 'Phase 6b' section (E5 table extended with clicks per session and per-metric verdict counts); F9-F11; web/data/site.json. |
| RESULTS addendum, EXPLAINER | done 2026-11-14 | docs/RESULTS.md 'Phase 6b addendum'; docs/EXPLAINER.md (new). E5's registered pattern 'more clicks, less watch time' appeared in 1 of 19 conditions; reported as is. |
| Singha Roy 2023 + TORS | done (E3) | No myopic baseline in either (skipped on purpose, γ = 1). No RQ2 overlap. NOTES, OVERLAP_MATRIX, POSITIONING, RELATED_WORK_DRAFT, CANDIDATES, SEED_VERIFIED, FINAL_SUMMARY, QA, LIT_AUDIT A4 updated. Bib year corrected to 2026 (PDF), key kept. |
| Port validity | done | OUR_SETUP_FACTS "Independent evidence" section; README limitation rewritten. The report does not exist yet: its limitations section must carry the same text (Phase 8). |
| Audit correction | done | LIT_AUDIT A1 was itself wrong: RecSim IE as used (UtilityModelVideoSampler) fixes video length at 4.0, like the SlateQ paper. NOTE, RELATED_WORK_DRAFT, DISCREPANCIES row 12 and LIT_AUDIT corrected. |
