# Literature review protocol

Written on 2026-11-13, **before any search was run**. Changes after this point are logged at the bottom.

## Question

For each research question, what is the **closest prior work**, and what exactly is new in this project?

- **RQ1:** SlateQ (decomposed) vs a myopic recommender in RecSim Interest Evolution.
- **RQ2:** the SlateQ - myopic gap as a function of candidates per step N and slate size k.
- **RQ3:** sensitivity of that gap to a misspecified user choice model.
- **Methodology:** learned-myopic control (gamma = 0), privileged oracle-myopic, common random numbers, 5 seeds, seed-bootstrap CIs, pre-registered protocol.

The experiments are frozen (PROTOCOL 12.6, 14, 15). This review changes how the results are **positioned**, not the results themselves.

## Sources

1. arXiv: the API (`export.arxiv.org/api/query`) for metadata and keyword search; abstract pages; PDFs.
2. Semantic Scholar Graph API: forward citations of SlateQ (arXiv 1905.12767, IJCAI 2019) and RecSim (arXiv 1909.04847); references of selected papers; keyword search.
3. Google Scholar: not scriptable from here. Any use is logged; gaps are stated, not hidden.
4. Publisher pages: ACM DL, IJCAI proceedings, CEUR-WS, OpenReview, TU Delft repository. Used for venue and DOI.
5. Venues of interest, 2019-2026: RecSys, WSDM, SIGIR, KDD, WWW, CIKM, NeurIPS, ICML, ICLR, AAAI, IJCAI.
6. Code: GitHub repositories of SlateQ reimplementations (licence, last commit).

**Date window:** 2019-05-01 to the search date.

## Inclusion criteria

- RL or bandit methods for **slate** (multi-item) recommendation that optimise long-term or cumulative engagement.
- Simulation platforms for RL recommenders (RecSim, RecSim NG, KuaiSim, RL4RS, EasyRL4Rec, ...).
- Work that evaluates, critiques, scales or reimplements SlateQ or its decomposition assumptions.
- Work on user choice or click-model misspecification in RL recommenders.
- Surveys of RL for recommender systems, for context only.

## Exclusion criteria

- Single-item (non-slate) RL recommenders, unless they address an issue central to an RQ (for example, myopic vs long-term baselines in a simulator).
- Pure supervised ranking or learning-to-rank without a sequential decision component.
- Non-recommendation slate problems (ads auctions, search) unless they use SlateQ-style decomposition.
- Papers we cannot open at least to the abstract (logged as UNVERIFIED and not cited).

## Evidence levels

| Level | What was read |
|---|---|
| E0 | metadata only (title, authors, venue) |
| E1 | abstract |
| E2 | introduction, related work and limitations |
| E3 | full text including results |

Every statement about another paper in our report must rest on a note at **E2 or higher**. E0/E1 items may appear only in "Limits of this review" or as context with no claim attached.

## Integrity rules

- Metadata (title, authors, year, venue, DOI) is taken from the source page or API, never from memory.
- Never write "has not been done". Write "we did not find it in the sources searched on <date>".
- No number from another paper is placed beside ours as a comparison unless the setting is identical. When shown for context, it is labelled "different environment, context only".
- Paraphrase. Any direct quote is at most 15 words and gives a page number.
- Numbers about our results come only from `docs/NUMBERS.md`, with their caveats.
- Preprints, theses and workshop papers are flagged as such wherever cited.

## Outputs

`SEARCH_LOG.md`, `CANDIDATES.md`, `SEED_VERIFIED.md`, `NOTES/<key>.md`, `references.bib`, `OUR_SETUP_FACTS.md`, `OVERLAP_MATRIX.md`, `POSITIONING.md`, `PROPOSED_DIAGNOSTICS.md`, `RELATED_WORK_DRAFT.md`, `WORDING_ISSUES.md`, `LIT_AUDIT.md`, `FINAL_SUMMARY.md`, `PROGRESS.md`; plus `docs/SUPPLEMENT_STATS.md` and `docs/QA_LITERATURE.md`.

## Change log

| Date | Change | Reason |
|---|---|---|
