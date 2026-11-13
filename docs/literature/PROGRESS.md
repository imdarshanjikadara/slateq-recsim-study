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
- Singha Roy 2023 (RecSys) and 2025 (TORS) full texts not obtainable by tool (ACM 403): student must open them; possible RQ2/RQ3 overlap unresolved.
- Google Scholar not queried.
- docs/papers/slateq.pdf and recsim.pdf are committed in the public repo (arXiv licence may not permit redistribution) - flagged in WORDING_ISSUES/FINAL_SUMMARY.
