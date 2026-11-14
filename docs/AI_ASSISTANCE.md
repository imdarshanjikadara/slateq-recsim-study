# AI assistance log

A neutral record of where an AI coding assistant was used in this project, kept so the work can be reported under the course's AI-use policy. It lists what the assistant did and what the student decided. Entries before 2026-11-13 are reconstructed from the git history and the project documents; the student should check and complete them.

## Division of work (all phases)

| The student | The AI assistant |
|---|---|
| Chose the topic and wrote the proposal approved by the instructor (`docs/proposal.md`), including RQ1-RQ3 | Drafted code, tests, scripts and documents on request |
| Set the scope contract, the software policy (current, lightweight libraries) and the integrity rules | Followed those rules; ran commands and reported their output |
| Approved each phase plan before work started, and every choice that affects the science (for example the primary comparison, the RQ2 grid, the RQ3 ladder, the Phase 6b experiments) | Proposed plans and options, with reasons, for the student to accept or change |
| Supplied paywalled papers and checked sources by hand | Searched for and summarised literature; recorded every source it opened |
| Owns the conclusions | Wrote first drafts of interpretation, limited to what the result files support |

## By phase

| Date | Phase (commit) | Assistant's part |
|---|---|---|
| 2026-11-05 | Setup, Phase 0 recon | Read RecSim's source and the SlateQ paper; wrote the paper-to-code map (`docs/RECON.md`) and the environment notes (`docs/ENV.md`); set up the Python environment and import shim. |
| 2026-11-05 | Phase 1-2 | Project scaffolding, environment wrapper, random and oracle baselines, evaluation harness, variance study used to fix 2400 evaluation episodes. |
| 2026-11-06 | Phase 3 | PyTorch port of RecSim's SlateQ agent and its unit tests; sanity ladder, budget and tuning scripts. |
| 2026-11-06 | Phase 4 | Sweep runner and experiment specs; draft of the pre-registered analysis plan (PROTOCOL §14-15), approved by the student. |
| 2026-11-06/07 | Phase 6 | Analysis code, figures, static web page, README and NUMBERS generator; ran the sweeps; drafted `docs/RESULTS.md`. |
| 2026-11-07 | Licence, deployment | Added the MIT licence and the static-site configuration; diagnosed a deployment error. |
| 2026-11-13 | Literature track | Searched arXiv, OpenAlex and Crossref; wrote the notes, overlap matrix, positioning, related-work draft and Q&A preparation in `docs/literature/`; post-hoc t-interval check (`docs/SUPPLEMENT_STATS.md`). |
| 2026-11-13 | Phase 6b | Wrote PROTOCOL §16 and DEVIATIONS D13-D16 for the student's approval; added agent variants and the paper-style cascade; ran E1-E4; wrote the E1-E5 analysis, the explainer (`docs/EXPLAINER.md`), the real-data options review and the port-validity summary. Read the two Singha Roy et al. papers supplied by the student. |

## What the assistant did not do

- It did not choose the research questions, the scope, or which results to report.
- It did not invent numbers: every reported number is produced by code in this repository from files in `results/`.
- It did not change a pre-registered rule after seeing results; changes are logged in `docs/PROTOCOL.md` (change log) and `docs/DEVIATIONS.md`.
