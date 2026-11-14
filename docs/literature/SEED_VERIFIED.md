# Seed list, verified (S1, 2026-11-13)

## How this was checked

- **arXiv:** title, authors, first-version date, comments, journal_ref and DOI from the arXiv API (`export.arxiv.org/api/query`, fetched 2026-11-13).
- **Peer-reviewed venues:** venue, pages and DOI from the Crossref API (`api.crossref.org/works`), and from CEUR-WS for the workshop paper.
- **Thesis:** metadata from the thesis title page.
- **Licences:** from the GitHub API (`api.github.com/repos/...`).
- DBLP returned HTTP 429 (rate limit) and was not used.

## Evidence levels and PDFs

- The evidence level shown is the level at the end of S1. S3 raises it for the papers read in depth (see `NOTES/`).
- PDFs are in `docs/papers/lit/`. That folder is **not committed**: arXiv's default licence does not grant redistribution, so the files stay local (excluded via `.git/info/exclude`).

## Table

| Key | Verified title | Authors (from source) | Year | Venue / status | DOI or id | Code / licence | Ev. | Discrepancies with the seed list |
|---|---|---|---|---|---|---|---|---|
| ie2019slateq_arxiv | Reinforcement Learning for Slate-based Recommender Systems: A Tractable Decomposition and Practical Methodology | Ie, Jain, Wang, Narvekar, Agarwal, Wu, Cheng, Lustman, Gatto, Covington, McFadden, Chandra, Boutilier (13) | 2019 | arXiv preprint (long version); comment: "Short version to appear IJCAI-2019" | arXiv:1905.12767 | RecSim repo (below) | E3 (already read in Phase 1; `docs/papers/slateq.txt`) | The long version has **13 authors**; the IJCAI version has 9. Cite each version with its own author list. |
| ie2019slateq_ijcai | SlateQ: A Tractable Decomposition for Reinforcement Learning with Recommendation Sets | Ie, Jain, Wang, Narvekar, Agarwal, Wu, Cheng, Chandra, Boutilier (9) | 2019 | IJCAI-19 proceedings, pp. 2592-2599 (peer-reviewed) | 10.24963/ijcai.2019/360 | - | E0 (we read the long arXiv version, not this one) | Pages confirmed. |
| ie2019recsim | RecSim: A Configurable Simulation Platform for Recommender Systems | Ie, Hsu, Mladenov, Jain, Narvekar, Wang, Wu, Boutilier | 2019 | arXiv preprint (no journal_ref) | arXiv:1909.04847 | github.com/google-research/recsim, Apache-2.0, **archived** (last push 2022-01-03) | E3 (Phase 1) | The repository is archived, i.e. no longer maintained. |
| sunehag2015slatemdp | Deep Reinforcement Learning with Attention for Slate Markov Decision Processes with High-Dimensional States and Actions | Sunehag, Evans, Dulac-Arnold, Zwols, Visentin, Coppin | 2015 | arXiv preprint | arXiv:1512.01124 | - | E1 | None. |
| dulacarnold2015large | Deep Reinforcement Learning in Large Discrete Action Spaces | Dulac-Arnold, Evans, van Hasselt, Sunehag, Lillicrap, Hunt, Mann, Weber, Degris, Coppin | 2015 | arXiv preprint (no journal_ref given) | arXiv:1512.07679 | - | E1 | None. |
| chen2019topk | Top-K Off-Policy Correction for a REINFORCE Recommender System | Chen, Beutel, Covington, Jain, Belletti, Chi | 2019 | WSDM 2019, pp. 456-464 (peer-reviewed) | 10.1145/3289600.3290999; arXiv:1812.02353 | - | E1 | Link found (arXiv 1812.02353). |
| deffayet2023gems | Generative Slate Recommendation with Reinforcement Learning | Deffayet, Thonet, Renders, de Rijke | 2023 | WSDM 2023, pp. 580-588 (peer-reviewed) | 10.1145/3539597.3570412; arXiv:2301.08632 | github.com/naver/gems, licence not a standard SPDX id (GitHub: NOASSERTION); last push 2023-02-24 | E1 | Pages added. |
| deffayet2022offline | Offline Evaluation for Reinforcement Learning-based Recommendation: A Critical Issue and Some Alternatives | Deffayet, Thonet, Renders, de Rijke | **2022** | ACM SIGIR Forum 56(2), pp. 1-14 | 10.1145/3582900.3582905; arXiv:2301.00993 | - | E1 | Seed said "SIGIR Forum 56 (2023)". Crossref gives **2022, vol. 56, no. 2**; the arXiv version is dated 2023-01-03. |
| giovanidis2022slatefree | SlateFree: a Model-Free Decomposition for Reinforcement Learning with Slate Actions | Giovanidis | 2022 | arXiv preprint (not peer-reviewed as far as found) | arXiv:2209.01876 | - | E1 | None. |
| singharoy2023scalable | Scalable Deep Q-Learning for Session-Based Slate Recommendation | Singha Roy, D'Amico, Tragos, Lawlor, Hurley | 2023 | RecSys 2023, pp. 877-882 (peer-reviewed, short paper) | 10.1145/3604915.3608843 | full text read 2026-11-13 (student-supplied PDF; CC BY 4.0) | E3 (2026-11-13) | Metadata matches the PDF (pp. 877-882). |
| singharoy2024news | Simulating Real-World News Consumption: Deep Q-Learning for Diverse User-Centric Slate Recommendations | Singha Roy, Tragos, Lawlor, Hurley | 2024 | INRA 2024 workshop (co-located with RecSys 2024), CEUR-WS Vol-3929, short3 (peer-reviewed workshop) | ceur-ws.org/Vol-3929/short3.pdf | see note | E1 | Venue name added (INRA 2024). |
| dai2023lowrank | Representation Learning in Low-rank Slate-based Recommender Systems | Dai, Sun | 2023 | Workshop: arXiv comment "in MFPL, ICML 2023" (ICML 2023 workshop) | arXiv:2309.08622 | - | E1 | Venue verified as an ICML 2023 workshop, not the main conference. |
| wang2025hsrl | Hierarchical Semantic RL: Tackling the Problem of Dynamic Action Space for RL-based Recommendations | M. Wang, Liu, Yi, L. Wu, Zhao, Pan, Cai, Jiang | 2025 | arXiv preprint | arXiv:2510.09167 | - | E1 | Full title added. |
| pantea2022thesis | Adapting to Dynamic User Preferences in Recommendation Systems via Deep Reinforcement Learning | Petru-Luca Pantea (supervisor: Oliehoek) | 2022 | BSc thesis, TU Delft (**not peer-reviewed**), dated 19 June 2022 | TU Delft repository link returns "campus only / embargo / closed" (2026-11-13) | github.com/lucapantea/research-project, Apache-2.0, last push 2022-06-21; the thesis PDF is in the repo | E1 | First name is **Petru-Luca**. The TU Delft file link is not publicly accessible; the PDF was taken from the author's repository. |
| deng2024fedslate | FedSlate: A Federated Deep Reinforcement Learning Recommender System | Deng, Qiu, Tan, Jin | 2024 (arXiv) / **2025 (journal)** | IEEE Trans. Emerging Topics in Computational Intelligence 9(6):4202-4216 (peer-reviewed) | 10.1109/TETCI.2025.3573250; arXiv:2409.14872 | - | E1 | Seed listed it as arXiv only; it is now a **2025 journal paper**. |
| tomasi2023playlist | Automatic Music Playlist Generation via Simulation-based Reinforcement Learning | Tomasi, Cauteruccio, Kanoria, Ciosek, Rinaldi, Dai | 2023 | KDD 2023, pp. 4948-4957 (peer-reviewed) | 10.1145/3580305.3599777; arXiv:2310.09123 | - | E1 | Pages added. |
| zhao2023kuaisim | KuaiSim: A Comprehensive Simulator for Recommender Systems | Zhao, Liu, Cai, X. Zhao, Z. Liu, Zheng, Jiang, Gai | 2023 | NeurIPS 36 (2023), pp. 44880-44897 (peer-reviewed); **track not verified** from source | 10.52202/075280-1945; arXiv:2309.12645 | - | E1 | Track (main vs Datasets & Benchmarks) not stated by Crossref: UNVERIFIED. |
| wang2023rl4rs | RL4RS: A Real-World Dataset for Reinforcement Learning based Recommender System | K. Wang, Zou, M. Zhao, Deng, Shang, Liang, Wu, Shen, Lyu, Fan | 2023 | SIGIR 2023, pp. 2935-2944 (peer-reviewed) | 10.1145/3539618.3591899; arXiv:2110.11073 | github.com/fuxiAIlab/RL4RS, CC-BY-SA-4.0, last push 2024-02-03 | E1 | Paper citation verified. |
| mladenov2021recsimng | RecSim NG: Toward Principled Uncertainty Modeling for Recommender Ecosystems | Mladenov, Hsu, Jain, Ie, Colby, Mayoraz, Pham, Tran, Vendrov, Boutilier | 2021 | arXiv preprint | arXiv:2103.08057 | - | E1 | None. |
| yu2024easyrl4rec | EasyRL4Rec: An Easy-to-use Library for Reinforcement Learning Based Recommender Systems | Yu, Gao, J. Chen, Tang, Sun, Q. Chen, Ma, Zhang | 2024 | SIGIR 2024, pp. 977-987 (peer-reviewed) | 10.1145/3626772.3657868; arXiv:2402.15164 | - | E1 | Title and authors verified. |
| afsar2022survey | Reinforcement Learning based Recommender Systems: A Survey | Afsar, Crump, Far | 2022 | ACM Computing Surveys 55(7), pp. 1-38 | 10.1145/3543846; arXiv:2101.06286 | - | E1 | None. |
| lin2024survey | A Survey on Reinforcement Learning for Recommender Systems | Lin, Y. Liu, F. Lin, Zou, Wu, Zeng, H. Chen, Miao | 2024 | IEEE TNNLS 35(10):13164-13184 | 10.1109/TNNLS.2023.3280161; arXiv:2109.10665 | - | E1 | Pages added. |
| chen2021drlsurvey | A Survey of Deep Reinforcement Learning in Recommender Systems: A Systematic Review and Future Directions | X. Chen, Yao, McAuley, Zhou, X. Wang | 2021 | arXiv preprint (no venue found) | arXiv:2109.03540 | - | E1 | Venue: none found; treated as a preprint. |
| chen2023offlinerl | On the Opportunities and Challenges of Offline Reinforcement Learning for Recommender Systems | X. Chen, S. Wang, McAuley, Jannach, Yao | 2023 | arXiv preprint (comment "under review" on v1) | arXiv:2308.11336 | - | E1 | Later publication not checked. |

## Could not verify (S1)

- **singharoy2023scalable full text:** the ACM DL page is not open access and no arXiv copy was found (checked 2026-11-13). Its metadata is verified via Crossref (E0). It cannot support any substantive claim until the full text is read; it is listed in FINAL_SUMMARY "open yourself". *Update 2026-11-13: the student downloaded the PDF; read in full (E3).*
- **KuaiSim's NeurIPS track:** not stated in the sources fetched.
- **Pantea thesis official repository page:** not accessible publicly (embargoed or closed).
