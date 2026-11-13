# Search log

Each row: date, source, exact query, filters, number of hits screened, kept candidates (keys).

| # | Date | Source | Query / action | Hits screened | Kept |
|---|---|---|---|---|---|
| 1 | 2026-11-13 | arXiv API (id_list) | metadata for 20 seed ids | 20 | all seeds (S1) |
| 2 | 2026-11-13 | Crossref API | 12 title lookups for venue/DOI | 36 | venue/DOI for 12 seeds |
| 3 | 2026-11-13 | DBLP API | title lookups | 0 (HTTP 429 rate limit) | none; not used |
| 4 | 2026-11-13 | CEUR-WS / GitHub API / TU Delft | Vol-3929 page; 4 repo licence lookups; thesis file | - | singharoy2024news venue; pantea2022thesis (TU Delft file closed; PDF from author repo) |
| 5 | 2026-11-13 | OpenAlex (cites:) | forward citations of SlateQ arXiv (W2946996695) and IJCAI (W2948345531) | 93 + 128 | see screening below |
| 6 | 2026-11-13 | OpenAlex (cites:) | forward citations of RecSim (W2972561734) | 213 | see screening below |
| 7 | 2026-11-13 | OpenAlex screening | union of the three sets, de-duplicated; keyword-scored on title+abstract (slateq, slate, myopic, choice model, misspecif, interest evolution, recsim, decompos, catalog/candidate/slate size, cascade, long-term, discount, reproduc, greedy); top 110 titles and 16 abstracts read | 369 unique; by year {2019: 9, 2020: 31, 2021: 64, 2022: 60, 2023: 57, 2024: 56, 2025: 40, 2026: 52} | kaushik2023gcitc, singharoy2025dontgetbored, singharoy2023scalable, singharoy2025slatellm, rajapakse2025reassessing, cavenaghi2023reproducibility, bergman2022rllib, deng2025fedslate, deffayet2023gems, giovanidis2022slatefree, dai2023lowrank |
| 8 | 2026-11-13 | arXiv API search (relevance, max 15) | all:SlateQ | 2 | 1905.12767; 2409.14872 |
| 9 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"slate recommendation" AND abs:"reinforcement learning" | 4 | 2309.08622; 2512.13726; 2301.08632; 2308.14165 |
| 10 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:slate AND abs:"catalog size" | 0 | - |
| 11 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:slate AND abs:"number of candidates" AND abs:reinforcement | 0 | - |
| 12 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:slate AND abs:"slate size" AND abs:reinforcement | 2 | 2610.22797; 2610.08743 |
| 13 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"choice model" AND abs:misspecification AND abs:recommend | 1 | 2602.10696 |
| 14 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"user choice model" AND abs:"reinforcement learning" AND abs:slate | 1 | 2412.10419 |
| 15 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"single click" AND abs:slate | 0 | - |
| 16 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:myopic AND abs:slate AND abs:reinforcement | 2 | 1905.12767; 2301.08632 |
| 17 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:myopic AND abs:"long-term" AND abs:recommender AND abs:simulation | 4 | 1905.12767; 2607.02818; 2301.08632; 2408.16032 |
| 18 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"discount factor" AND abs:recommender AND abs:"reinforcement learning" | 0 | - |
| 19 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"discount factor" AND abs:slate | 0 | - |
| 20 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:RecSim AND abs:"interest evolution" | 0 | - |
| 21 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:RecSim AND abs:SlateQ | 1 | 2409.14872 |
| 22 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:RecSim AND abs:benchmark | 1 | 2409.14872 |
| 23 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"cascade" AND abs:"click model" AND abs:"reinforcement learning" AND abs:recommend | 0 | - |
| 24 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"large discrete action" AND abs:recommend | 5 | 1811.05869; 2004.06651; 2410.11833; 2602.08616 |
| 25 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"combinatorial action" AND abs:recommend AND abs:"reinforcement learning" | 6 | 2003.00097; 2308.14165; 2305.18820; 2301.08632 |
| 26 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:reproducibility AND abs:"reinforcement learning" AND abs:recommender | 19 | 2110.03039; 1908.04683; 2006.10904; 2402.15164 |
| 27 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"Q-learning" AND abs:slate AND abs:decomposition | 1 | 1905.12767 |
| 28 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"slate" AND abs:"value decomposition" AND abs:recommend | 0 | - |
| 29 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"top-k" AND abs:slate AND abs:"reinforcement learning" AND abs:simulator | 0 | - |
| 30 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"oracle" AND abs:myopic AND abs:recommend | 2 | 2202.06135; 2608.12831 |
| 31 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"greedy" AND abs:"long-term engagement" AND abs:recommend AND abs:reinforcement | 0 | - |
| 32 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"user simulator" AND abs:slate AND abs:"reinforcement learning" | 0 | - |
| 33 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"generative" AND abs:slate AND abs:"reinforcement learning" | 12 | 2005.12206; 2301.08632; 2611.04720; 2610.22797 |
| 34 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"large language model" AND abs:slate AND abs:"long-term" | 1 | 2610.34673 |
| 35 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"semantic ID" AND abs:"reinforcement learning" AND abs:recommend | 20 | 2609.29973; 2609.39828; 2505.12396; 2611.08804 |
| 36 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:diffusion AND abs:slate AND abs:recommend | 2 | 2408.06883; 2610.36954 |
| 37 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"long-term engagement" AND abs:"reinforcement learning" AND abs:slate | 0 | - |
| 38 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"session" AND abs:slate AND abs:"deep Q" | 0 | - |
| 39 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"misspecified" AND abs:"user model" AND abs:recommend AND abs:reinforcement | 1 | 2510.15429 |
| 40 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"conditional logit" AND abs:slate AND abs:reinforcement | 0 | - |
| 41 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"candidate set" AND abs:"reinforcement learning" AND abs:recommend AND abs:scal | 0 | - |
| 42 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:"user choice" AND abs:robust AND abs:slate | 0 | - |
| 43 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:slate AND abs:reinforcement AND abs:recommend | 13 | 2308.14165; 2111.03340; 1905.12767; 2301.08632 |
| 44 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:slate AND abs:reinforcement AND abs:recommend AND abs:myopic | 2 | 1905.12767; 2301.08632 |
| 45 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:slate AND abs:recommend AND abs:choice AND abs:model AND abs:reinforcement | 0 | - |
| 46 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:RecSim | 5 | 1909.04847; 2103.08057; 2108.01455; 2409.14872 |
| 47 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:slate AND abs:recommend AND abs:simulat AND abs:reinforcement | 0 | - |
| 48 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:slate AND abs:reinforcement AND abs:recommend AND abs:2025 | 0 | - |
| 49 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:recommend AND abs:reinforcement AND abs:myopic AND abs:baseline | 5 | 2106.00589; 2202.08812; 2301.08632; 2607.02818 |
| 50 | 2026-11-13 | arXiv API search (relevance, max 15) | abs:slate AND abs:"Q-learning" | 3 | 2209.01876; 1512.01124; 1905.12767 |
| 51 | 2026-11-13 | Semantic Scholar search | slate recommendation reinforcement learning (year 2025) | rate-limited (HTTP 429), no result | - |
| 52 | 2026-11-13 | Semantic Scholar search | slate recommendation reinforcement learning (year 2026) | rate-limited (HTTP 429), no result | - |
| 53 | 2026-11-13 | Semantic Scholar search | SlateQ (year 2020-2026) | rate-limited (HTTP 429), no result | - |
| 54 | 2026-11-13 | Semantic Scholar search | RecSim SlateQ myopic (year 2020-2026) | rate-limited (HTTP 429), no result | - |
| 55 | 2026-11-13 | Semantic Scholar search | choice model misspecification slate reinforcement learning (year 2020-2026) | 2416 | - |
| 56 | 2026-11-13 | Semantic Scholar search | myopic baseline long-term engagement recommender simulation (year 2025-2026) | rate-limited (HTTP 429), no result | - |
| 57 | 2026-11-13 | Semantic Scholar search | SlateQ catalog size slate size (year 2020-2026) | rate-limited (HTTP 429), no result | - |
| 58 | 2026-11-13 | Semantic Scholar search | RLlib SlateQ (year 2020-2026) | 59 | bergman2022rllib |
| 59 | 2026-11-13 | web-fetch (ACM DL) | full text of 10.1145/3604915.3608843 and 10.1145/3733241 | HTTP 403 both | not read (E0/E1) |
| 60 | 2026-11-13 | Backward chaining | reference lists of GeMS, Singha Roy 2024, SlateFree, Afsar 2022, Lin 2024 grepped for slate/SlateQ/myopic/choice/cascade/RecSim/simulat | ~40 lines | no new candidate beyond those already found |

## Notes

- **2025 and 2026 searched separately** (OpenAlex year field; Semantic Scholar year filter, though rate-limited).
- **2026 records were found:** 52 of the forward citations are dated 2026. None of the 2026 records screened (titles for all; abstracts for those scoring >= 4) runs SlateQ against a myopic baseline across catalog/slate sizes or choice models. The closest 2026 items are generative slate ranking (OneTrans-GSR, arXiv 2611.04720) and a RecSys 2026 paper on noisy-score slate selection; neither overlaps our RQs.
- **Google Scholar was not queried** (not scriptable). OpenAlex forward citations are used in its place. OpenAlex coverage of SlateQ citations (221 combined) is likely lower than Google Scholar's; this is a stated gap.
- **Paywalled or blocked full texts** (ACM DL 403) are listed in FINAL_SUMMARY for the student to open.
