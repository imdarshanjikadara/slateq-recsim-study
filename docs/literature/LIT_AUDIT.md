# Literature self-audit (S9, 2026-11-13)

This audit was done by a skeptical re-read **in the same session**, not by a fresh reviewer. A fresh-session audit is still recommended (see FINAL_SUMMARY).

## Checks performed

1. **References re-checked.** Every `references.bib` entry's title was checked against `SEED_VERIFIED.md`, whose metadata came from the arXiv API, Crossref, CEUR-WS or the thesis title page.
   - 24 of 26 entries match by script.
   - The 2 added later (singharoy2025dontgetbored, kaushik2023gcitc) come from Crossref DOI lookups recorded in their NOTES.
   - Bib keys without a NOTE: **0**. Keys cited in RELATED_WORK_DRAFT but missing from the bib: **0** (script output in this session).
2. **Cited sentences vs the paper's own text.** For E3 papers, each sentence in RELATED_WORK_DRAFT was re-checked against the extracted full text:
   - SlateQ: §6.3, §6.5, §7.1, §7.3 and footnote 10.
   - GeMS: §1, §4, §6.1.
   - SlateFree: §5.
   - Singha Roy 2024: §4-5.
   - Pantea: §4-6.
3. **Disallowed phrases** were grepped in all new files. The only hits are quotations of the SlateQ paper's own words ("continues to outperform MYOP"), the PROTOCOL_LIT rule text, "first-version date", and "not a state-of-the-art claim". None is a claim by us.
4. **Our numbers** in RELATED_WORK_DRAFT, POSITIONING, DISCREPANCIES and QA_LITERATURE were checked against NUMBERS.md and SUPPLEMENT_STATS.md.
5. **Numbers attributed to other papers** appear only:
   - as values copied from the SlateQ paper's tables (§7.1, §7.3), and
   - as percentages computed by us from them (+1.26 %, +1.96 %), always labelled "context only / computed by us".
   - Pantea's percentages are labelled as relative to Random.

## Findings

| ID | Severity | Finding | Status |
|---|---|---|---|
| A1 | **P0** | The NOTE and the Related Work table said the SlateQ paper's simulator matches RecSim IE on "document length 4". RecSim samples video length with mean 4.3 and sd 1.0 (`interest_evolution.py:170-171`). This was an unverified claim. | **Fixed** in NOTES/ie2019slateq.md and RELATED_WORK_DRAFT.md. Row 12 added to DISCREPANCIES. |
| A2 | P1 | The GeMS quote's page was first given as "page 6". `pdftotext` per-page search shows PDF page 7. | **Fixed** in NOTES/deffayet2023gems.md. |
| A3 | P1 | The Singha Roy 2025 citation in the Related Work initially lacked a bib key. | **Fixed:** bib entry added from Crossref; the text now cites `singharoy2025dontgetbored`. |
| A4 | P1 | Possible RQ2/RQ3 overlap in two unread papers (singharoy2023scalable at E0, singharoy2025dontgetbored at E1). The "not found" statements for RQ2 depend on them. | **Open.** Every novelty sentence carries the caveat. The student must read both (FINAL_SUMMARY). |
| A5 | P1 | GeMS Table 2 numbers could not be extracted reliably. We state only GeMS's textual conclusions. | Accepted. No GeMS number is used. |
| A6 | P2 | Sentences citing E0/E1 sources: the surveys (as a pointer), and singharoy2023scalable and singharoy2025dontgetbored (topic only, explicitly "not read"). | Accepted with labels. Not used for any substantive claim. |
| A7 | P2 | KuaiSim's NeurIPS track is not verified. Cited as "NeurIPS 2023" only. | Accepted. |
| A8 | P2 | kaushik2023gcitc's abstract matches the Pantea thesis findings. We note the similarity factually and draw no conclusion. | Accepted. It is not cited in the Related Work text. |
| A9 | P2 | The SlateQ paper cited is the long arXiv version (E3). The IJCAI short version was not read; it is cited only as the peer-reviewed record. | Accepted. Section numbers refer to the arXiv version, as stated in the NOTE. |
| A10 | P2 | Google Scholar not used; Semantic Scholar mostly rate-limited. | Stated in "Limits of this review" and SEARCH_LOG. |
| A11 | P1 | Issues outside the new files (website and README "only the horizon differs"; RESULTS.md "largely disappears"; committed third-party PDFs). | Listed in WORDING_ISSUES.md (W1-W12). **Not fixed:** outside scope and frozen. Needs the student's decision. |

## Residual risk

The weakest point of this review is A4. If Singha Roy et al. 2025 reports SlateQ-vs-greedy gaps across item-pool sizes, our RQ2 novelty statement must be narrowed to "slate size, the learned γ = 0 control and the oracle comparison in RecSim Interest Evolution".
