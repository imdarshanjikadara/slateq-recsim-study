# Related Work and Positioning (draft for docs/REPORT.md)

`docs/REPORT.md` does not exist yet, so this draft lives here. Citation keys refer to `references.bib`. Every sentence about another paper maps to a `NOTES/` file at E2 or higher (see the check at the end). Search date: 2026-11-13.

---

## Related Work

### Foundations

Slate recommendation as sequential decision making was formalised as the slate-MDP: the agent proposes a tuple of items, of which at most one is acted upon [sunehag2015slatemdp]. RL with very large discrete action sets has been approached by embedding actions and retrieving near neighbours [dulacarnold2015large]. A policy-gradient approach with a top-K off-policy correction was scaled to a production recommender [chen2019topk].

SlateQ [ie2019slateq_arxiv; ie2019slateq_ijcai] makes value-based RL tractable for slates by decomposing the slate Q-value into item-wise Q-values weighted by a user choice model. This rests on two assumptions: the user consumes at most one item per slate, and reward and transitions depend only on that item.

The paper's simulations use m = 10 candidates and slate size k = 3 only (§6.5). In that setting, SlateQ's long-term variants obtain higher return per session than a myopic model, which the paper defines as the same learned model with γ = 0 (footnote 10, §7.1). RecSim [ie2019recsim] released the simulation platform and reference agents. Its Interest Evolution environment is the one we use.

### Decomposition and its assumptions

Later work questions SlateQ's assumptions. GeMS [deffayet2023gems] argues that tractable slate decompositions rely on restrictive assumptions. It learns a latent slate space from logged data instead. In its simulators, which use position-based click models that violate the single-click assumption, SlateQ performs poorly relative to GeMS. Its baselines include a privileged short-term oracle, as ours do.

SlateFree [giovanidis2022slatefree, preprint] decomposes the slate Q-function without a known choice model. In tabular experiments it converges faster than SlateQ, and SlateQ fails to solve its larger catalog setting within the episode budget.

### Scaling to large catalogs

Singha Roy et al. [singharoy2024news, workshop] extend RecSim with real news data (MIND) and a learned choice model. They restrict SlateQ's Q-evaluations to a learned candidate subset (Proto-Slate). Their reported comparison is with 300 candidates and k = 10, against Random and Greedy baselines, over 5 seeds with paired t-tests. Their candidate-subset size is varied to reduce inference cost.

A RecSys 2023 paper and a 2025 ACM TORS article by the same group address SlateQ's scalability with large item pools [singharoy2023scalable; singharoy2025dontgetbored]. We could not read their full texts (see Limits of this review), so we make no claim about their content.

### Simulation and evaluation methodology

Offline next-item evaluation is itself myopic: it rewards one-step prediction and ignores the effect of recommendations on later behaviour [deffayet2022offline]. This motivates evaluating long-term policies by interaction with a simulator, as we do. Data-driven simulators such as KuaiSim [zhao2023kuaisim] aim at greater realism than rule-based ones. RecSim NG [mladenov2021recsimng] generalises RecSim to multi-agent ecosystems.

Simulator results hold only for the simulator. Our conclusions are limited to RecSim Interest Evolution.

### Surveys

For broader overviews see [afsar2022survey; lin2024survey; chen2021drlsurvey; chen2023offlinerl].

### Closest prior or informal comparisons

A TU Delft BSc thesis [pantea2022thesis, not peer-reviewed] compares SlateQ with FullSlateQ in a RecSim-based environment with preference shifts:

- 10 items, k = 2, γ = 0.5, 3 seeds, and no myopic baseline.
- Both agents behave largely myopically at γ = 0.5.
- The thesis names other discount factors as future work.

A FedSlate study [deng2025fedslate] builds a federated variant of SlateQ in a RecSim-built environment. Together with Singha Roy et al., this shows that SlateQ and RecSim are still used as baselines in 2024-2025.

---

## How this project relates to the SlateQ paper's setup

**Settings differ; numbers are not comparable.**

| Aspect | Ie et al. 2019 (§6-7) | This project |
|---|---|---|
| Environment | Stylised simulator of §6: budget 200, no-click cost 0.5 (as in RecSim IE); fixed document length 4 (RecSim IE samples mean 4.3, sd 1) | RecSim Interest Evolution, unmodified (pinned commit) |
| Candidates m / N, slate size k | m = 10, k = 3 only | N ∈ {5, 10, 20, 40, 80} × k ∈ {2, 3, 5}, plus control (5, 5) |
| Agent variant | SARSA-TS/GS/OS, several Q-learning variants | SARSA-TS (PyTorch port of RecSim's `SlateDecompQAgent`) |
| γ (long-term) | 1 | 0.99 |
| Myopic baseline | MYOP: learned model with γ = 0 | Learned-myopic (γ = 0; own tuned learning rate) **and** oracle-myopic (privileged true state) |
| Training budget | 300K steps | 300K steps (frozen at (10, 3)) |
| Seeds / evaluation | Seeds not reported; 5000 users; "within a 95% CI" | 5 run seeds × 2400 paired evaluation episodes (common random numbers); seed-bootstrap CIs; pre-registered rule |
| Metric | Average return per session | Mean total watch time per session |
| Misspecification | One exponential cascade (β0 = 1, β = 0.65, conditional-model base probabilities, null item kept) | Ladder: no-click mass 3; multinomial logit; RecSim proportional cascade (attention 0.65, score scaling 0.05) |

---

## RQ3 versus the SlateQ paper

Under its cascade users, the SlateQ paper reports SlateQ still ahead of MYOP. Under our cascade rung, the SlateQ − learned-myopic gap is +0.22 (95% CI [+0.08, +0.38]; one of five seeds at −0.01), which is "no clear difference" by our pre-registered rule. SlateQ still far exceeds random (108.00 vs 84.19).

The two experiments are not the same. Explanations, by label (DISCREPANCIES.md):

- **SUPPORTED: the cascades are parameterised differently.** In the paper, random's return barely changed under cascade. In ours, it fell from 160.55 to 84.19 and sessions lengthened from 70.8 to 227.3 steps, i.e. clicks became rare. Fewer clicks leave less room for the long-term lever (quality-driven budget refunds).
- **PLAUSIBLE: with rare clicks, the reference implementation's zero no-click value shortens SlateQ's effective horizon further, and most transitions are not trained on.**
- **SPECULATIVE: implementation differences** between Dopamine and our port. We have no evidence of an error, but no end-to-end cross-check either.

For context only (different implementation): the paper's SARSA-TS is +1.96 % over MYOP-TS under cascade. Ours is +0.20 % over learned-myopic.

We therefore do not read our result as contradicting the paper. It shows that the advantage depends on the cascade's parameters, which the paper did not vary.

---

## Our position

This project is a controlled, pre-registered **replication and extension** of SlateQ's simulated comparison with a myopic baseline. It is not a new method.

**RQ1, replication.** We re-measure the paper's comparison at its own setting with an independent port. SlateQ beats the learned γ = 0 baseline by +1.70 (CI [+1.54, +1.85]), about 1 %.

**RQ2, extension.** The paper used one size. Over 14 (N, k) settings, the gap is clearly positive everywhere, grows with N and shrinks with k.

- Against the privileged oracle it reaches +27.17 at (80, 3).
- Part of the larger primary gap at high N reflects the learned baseline weakening under a budget frozen at (10, 3).
- To our knowledge, among the sources we reviewed (search date 2026-11-13), we did not find a study reporting this gap over a grid of candidate and slate sizes. Two papers on SlateQ scaling could not be read in full.

**RQ3, extension.** We complement the paper's single cascade test with a graded ladder, judged against learned and privileged myopic baselines.

**Methodology.** Each element (γ = 0 control, privileged oracle, multiple seeds) appears in prior work. We did not find them combined with common random numbers and a pre-registered decision rule in one SlateQ study.

---

## Limits of this review

- **Searched 2026-11-13:**
  - arXiv API (43 queries);
  - OpenAlex forward citations of SlateQ (both versions) and RecSim (369 unique works, all titles screened);
  - Crossref, CEUR-WS and GitHub for metadata;
  - backward chaining from GeMS, Singha Roy 2024, SlateFree and two surveys.
- **Semantic Scholar** searches were mostly rate-limited.
- **Google Scholar** was not queried. OpenAlex citation coverage may be lower than Google Scholar's.
- **Not read in full** (publisher blocked automated access):
  - Singha Roy et al., RecSys 2023;
  - Singha Roy et al., ACM TORS 2025;
  - the 2023 GCITC paper comparing FullSlateQ and SlateQ (closed access).
- **Preprints and non-peer-reviewed sources are flagged:** SlateFree, RecSim, RecSim NG, the long SlateQ version, HSRL, and the Pantea thesis.
- **2026 work was found** (52 forward citations). None of the screened 2026 titles or abstracts ran SlateQ against a myopic baseline across sizes or choice models.
- This review is **not exhaustive**.

---

## Short README version (≈90 words)

> **Related work.** SlateQ (Ie et al., 2019) and RecSim (Ie et al., 2019) are the basis of this project. The paper's simulations compare SlateQ with a γ = 0 myopic model at 10 candidates and slate size 3; we replicate that comparison and extend it to 14 candidate/slate sizes and a graded choice-model ladder. Later work critiques SlateQ's assumptions (GeMS, WSDM 2023; SlateFree, preprint) and scales it to large item pools (Singha Roy et al., 2023-2025). See `docs/literature/` for the full review, its search date (2026-11-13) and its limits.

---

## Check 1: every cited sentence maps to a NOTE at E2 or higher

| Citation used | NOTE | Level | OK? |
|---|---|---|---|
| sunehag2015slatemdp | NOTES/sunehag2015slatemdp.md | E2 | yes |
| dulacarnold2015large | NOTES/dulacarnold2015large.md | E2 | yes |
| chen2019topk | NOTES/chen2019topk.md | E2 | yes |
| ie2019slateq_arxiv / _ijcai | NOTES/ie2019slateq.md | E3 (arXiv version) | yes. The IJCAI version is cited as the peer-reviewed record of the same work; section numbers refer to the arXiv version. |
| ie2019recsim | NOTES/ie2019recsim.md | E3 | yes |
| deffayet2023gems | NOTES/deffayet2023gems.md | E3 | yes |
| giovanidis2022slatefree | NOTES/giovanidis2022slatefree.md | E3 | yes |
| singharoy2024news | NOTES/singharoy2024news.md | E3 | yes |
| singharoy2023scalable; Singha Roy 2025 | NOTES/singharoy2023scalable.md (E0); NOTES/singharoy2025dontgetbored.md (E1) | E0/E1 | **Allowed only because the sentence makes no claim about content beyond the topic stated in the title, and says the texts were not read.** Flagged P2 in LIT_AUDIT. |
| deffayet2022offline | NOTES/deffayet2022offline.md | E2-E3 | yes |
| zhao2023kuaisim | NOTES/zhao2023kuaisim.md | E2 | yes |
| mladenov2021recsimng | NOTES/mladenov2021recsimng.md | E2 | yes |
| afsar2022survey, lin2024survey, chen2021drlsurvey, chen2023offlinerl | NOTES/*.md | E1 | Pointer only ("for broader overviews see"); no substantive claim. Flagged P2. |
| pantea2022thesis | NOTES/pantea2022thesis.md | E3 | yes |
| deng2025fedslate | NOTES/deng2025fedslate.md | E2 | yes |
