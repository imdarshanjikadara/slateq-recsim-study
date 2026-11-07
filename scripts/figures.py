"""Phase 6 figures F1-F8 from the committed result tables (results/rq2, results/rq3).

    python scripts/figures.py [--rq2 results/rq2] [--rq3 results/rq3] [--out results/figures]

Deterministic: reads only the CSV/JSON/JSONL tables written by scripts/analyze.py, so it works
from a clean checkout. Figures built from PILOT tables are watermarked. Palette: validated
categorical slots 1-4 (light mode), every series also direct-labelled; diverging blue/red with a
gray midpoint for the RQ2 gap heatmap; one-hue ordinal ramp for ordered parameters (N, k).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from slateq_study.io import REPO_ROOT  # noqa: E402

AGENTS = ["slateq", "learned_myopic", "oracle_myopic", "random"]
LABEL = {
    "slateq": "SlateQ",
    "learned_myopic": "Learned myopic",
    "oracle_myopic": "Oracle myopic",
    "random": "Random",
}
COLOR = {
    "slateq": "#2a78d6",
    "learned_myopic": "#eb6834",
    "oracle_myopic": "#1baf7a",
    "random": "#eda100",
}
MARKER = {"slateq": "o", "learned_myopic": "s", "oracle_myopic": "D", "random": "^"}
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
ORDINAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]  # blue 250..650
DIVERGING = LinearSegmentedColormap.from_list("gap", ["#e34948", "#f0efec", "#2a78d6"])
RUNGS = ["matched", "mild_noclick3", "moderate_logit", "severe_cascade"]
RUNG_LABEL = {
    "matched": "matched",
    "mild_noclick3": "mild\n(no-click mass 3)",
    "moderate_logit": "moderate\n(logit)",
    "severe_cascade": "severe\n(cascade)",
}
PRIMARY = "SlateQ - learned-myopic"
CAPTIONS: dict[str, str] = {}


def style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK,
            "xtick.color": INK2,
            "ytick.color": INK2,
            "text.color": INK,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "lines.linewidth": 2,
            "legend.frameon": False,
            "legend.fontsize": 8,
        }
    )


def save(fig, out: Path, name: str, caption: str, pilot: bool) -> None:
    if pilot:
        fig.text(
            0.5,
            0.5,
            "PILOT - not results",
            fontsize=34,
            color="#e34948",
            alpha=0.18,
            ha="center",
            va="center",
            rotation=25,
            transform=fig.transFigure,
        )
    out.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"{name}.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)
    CAPTIONS[name] = caption + (" PILOT DATA: plumbing check only." if pilot else "")
    print(f"  {name}")


def seed_cols(row: pd.Series, prefix: str) -> list[float]:
    return [row[c] for c in row.index if c.startswith(prefix) and not pd.isna(row[c])]


# ---------------------------------------------------------------------------------------- F1
def f1_curves(d: Path, out: Path, pilot: bool) -> None:
    p = d / "curves.csv"
    if not p.exists():
        return
    c = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for a in ("slateq", "learned_myopic"):
        s = c[c.agent == a]
        if s.empty:
            continue
        piv = s.pivot_table(index="train_steps", columns="seed", values="mean_total_reward")
        # curve points sit at the first episode boundary after each mark: align by rank
        mat = np.array(
            [
                s[s.seed == k].sort_values("train_steps").mean_total_reward.to_numpy()
                for k in piv.columns
            ]
        )
        x = (
            np.array(
                [
                    s[s.seed == k].sort_values("train_steps").train_steps.to_numpy()
                    for k in piv.columns
                ]
            ).mean(0)
            / 1000
        )
        m, sd = mat.mean(0), mat.std(0, ddof=1) if len(mat) > 1 else np.zeros(mat.shape[1])
        ax.plot(x, m, color=COLOR[a], marker=MARKER[a], ms=4, label=LABEL[a])
        ax.fill_between(x, m - sd, m + sd, color=COLOR[a], alpha=0.15, lw=0)
        ax.annotate(
            LABEL[a],
            (x[-1], m[-1]),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
            color=INK,
        )
    n = c.seed.nunique()
    ax.set_xlabel("training steps (thousands)")
    ax.set_ylabel("mean total reward per episode\n(tune-stream episodes)")
    ax.set_title("F1  Learning curves, N=10, k=3")
    ax.legend(loc="lower right")
    ax.margins(x=0.12)
    save(
        fig,
        out,
        "F1_learning_curves",
        f"F1. Learning curves at the primary cell (N=10, k=3). Line = mean over {n} seeds of the "
        "mean total reward on 200 tune-stream episodes per point; band = +-1 SD over seeds.",
        pilot,
    )


# ---------------------------------------------------------------------------------------- F2
def f2_headline(d: Path, out: Path, pilot: bool) -> None:
    ag = pd.read_csv(d / "agents.csv")
    gp = pd.read_csv(d / "gaps.csv")
    ag = ag[(ag.condition == "matched") & (ag.num_candidates == 10) & (ag.slate_size == 3)]
    gp = gp[(gp.condition == "matched") & (gp.num_candidates == 10) & (gp.slate_size == 3)]
    if ag.empty:
        return
    fig, (a1, a2) = plt.subplots(
        1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.75}
    )
    for i, a in enumerate(AGENTS):
        r = ag[ag.agent == a]
        if r.empty:
            continue
        r = r.iloc[0]
        seeds = seed_cols(r, "mean_total_reward_seed")
        a1.scatter(
            np.full(len(seeds), i) + np.linspace(-0.12, 0.12, len(seeds)),
            seeds,
            s=16,
            color=COLOR[a],
            alpha=0.55,
            lw=0,
        )
        a1.errorbar(
            i,
            r.mean_total_reward,
            yerr=[
                [r.mean_total_reward - r.mean_total_reward_ci95_low],
                [r.mean_total_reward_ci95_high - r.mean_total_reward],
            ],
            fmt=MARKER[a],
            ms=8,
            color=COLOR[a],
            mec=SURFACE,
            mew=1.5,
            capsize=4,
            elinewidth=2,
        )
        a1.annotate(
            f"{r.mean_total_reward:.1f}",
            (i, r.mean_total_reward),
            xytext=(10, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
        )
    a1.set_xticks(range(len(AGENTS)), [LABEL[a].replace(" ", "\n") for a in AGENTS])
    a1.set_ylabel("mean total reward per episode (watch time)")
    a1.set_title("F2a  Long-term engagement, N=10, k=3")
    rows = [gp[gp.comparison == c].iloc[0] for c in gp.comparison.unique()]
    rows.sort(key=lambda r: (not r.primary, r.comparison))
    for i, r in enumerate(rows):
        y = len(rows) - 1 - i
        seeds = seed_cols(r, "diff_seed")
        a2.scatter(
            seeds,
            np.full(len(seeds), y) + np.linspace(-0.12, 0.12, len(seeds)),
            s=16,
            color=INK2,
            alpha=0.5,
            lw=0,
        )
        if not pd.isna(r.get("mean_diff")):
            a2.errorbar(
                r.mean_diff,
                y,
                xerr=[[r.mean_diff - r.ci95_low], [r.ci95_high - r.mean_diff]],
                fmt="o",
                ms=7,
                color="#2a78d6" if r.primary else INK2,
                capsize=4,
                elinewidth=2,
            )
            a2.annotate(
                f"{r.mean_diff:+.2f} [{r.ci95_low:+.2f}, {r.ci95_high:+.2f}]",
                (r.ci95_high, y),
                xytext=(6, 6),
                textcoords="offset points",
                fontsize=7.5,
            )
    a2.axvline(0, color=INK2, lw=1)
    a2.set_yticks(
        range(len(rows))[::-1], [("PRIMARY\n" if r.primary else "") + r.comparison for r in rows]
    )
    a2.set_xlabel("paired difference in mean total reward (A - B)")
    a2.set_title("F2b  Paired differences (same eval users)")
    a2.margins(x=0.25)
    n = int(ag.n_seeds.max())
    save(
        fig,
        out,
        "F2_headline",
        f"F2. Primary cell (N=10, k=3), matched choice model, {n} run seeds x 2400 common-random-"
        "number eval episodes. (a) Large marker = mean over seeds of per-run mean total reward; "
        "bar = seed-bootstrap 95% CI; small dots = individual seeds. (b) Per-seed paired "
        "differences A - B (dots), their mean and seed-bootstrap 95% CI. Primary comparison: "
        "SlateQ - learned-myopic (PROTOCOL 14.3).",
        pilot,
    )


# ------------------------------------------------------------------------------------- F3, F4
def _primary_grid(d: Path) -> pd.DataFrame:
    gp = pd.read_csv(d / "gaps.csv")
    return gp[(gp.comparison == PRIMARY) & (gp.condition == "matched") & (~gp.control)]


def f3_heatmap(d: Path, out: Path, pilot: bool) -> None:
    g = _primary_grid(d)
    if g.empty:
        return
    ns, ks = sorted(g.num_candidates.unique()), sorted(g.slate_size.unique())
    mat = np.full((len(ks), len(ns)), np.nan)
    for _, r in g.iterrows():
        if not pd.isna(r.get("mean_diff")):
            mat[ks.index(r.slate_size), ns.index(r.num_candidates)] = r.mean_diff
    lim = np.nanmax(np.abs(mat)) if np.isfinite(mat).any() else 1.0
    fig, ax = plt.subplots(figsize=(1.2 * len(ns) + 2.2, 0.9 * len(ks) + 1.6))
    ax.grid(False)
    im = ax.imshow(mat, cmap=DIVERGING, vmin=-lim, vmax=lim, aspect="auto")
    for i, k in enumerate(ks):
        for j, n in enumerate(ns):
            r = g[(g.slate_size == k) & (g.num_candidates == n)]
            if k >= n:
                txt = "k >= N\n(not run)"
            elif r.empty or pd.isna(r.iloc[0].get("mean_diff")):
                txt = "missing"
                ax.add_patch(
                    plt.Rectangle(
                        (j - 0.5, i - 0.5), 1, 1, fill=False, hatch="//", color=INK2, lw=0
                    )
                )
            else:
                r = r.iloc[0]
                txt = (
                    f"{r.mean_diff:+.2f}\n[{r.ci95_low:+.2f}, {r.ci95_high:+.2f}]\n"
                    f"n={int(r.n_seeds)}"
                )
            ax.text(j, i, txt, ha="center", va="center", fontsize=7, color=INK)
    ax.set_xticks(range(len(ns)), ns)
    ax.set_yticks(range(len(ks)), ks)
    ax.set_xlabel("catalog size N (candidates per step)")
    ax.set_ylabel("slate size k")
    ax.set_title("F3  SlateQ - learned-myopic gap over (N, k)")
    cb = fig.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("mean paired gap in total reward")
    save(
        fig,
        out,
        "F3_rq2_heatmap",
        "F3. RQ2: primary gap (SlateQ - learned-myopic, mean total reward) per cell. Text: mean "
        "over seeds, seed-bootstrap 95% CI, number of seeds. Blue = SlateQ higher, red = lower, "
        "gray = no difference. Cells with k >= N are not part of the grid; the (5,5) control is "
        "reported separately.",
        pilot,
    )


def f4_lines(d: Path, out: Path, pilot: bool) -> None:
    g = _primary_grid(d).dropna(subset=["mean_diff"])
    if g.empty:
        return
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6), sharey=True)
    ks, ns = sorted(g.slate_size.unique()), sorted(g.num_candidates.unique())
    for i, k in enumerate(ks):
        s = g[g.slate_size == k].sort_values("num_candidates")
        col = ORDINAL[min(len(ORDINAL) - 1, 1 + 2 * i)]
        x = np.arange(len(s)) * 0 + s.num_candidates.to_numpy()
        a1.errorbar(
            x * (1 + 0.03 * (i - 1)),
            s.mean_diff,
            yerr=[s.mean_diff - s.ci95_low, s.ci95_high - s.mean_diff],
            marker="o",
            ms=5,
            capsize=3,
            color=col,
        )
        a1.annotate(
            f"k={k}",
            (x[-1], s.mean_diff.iloc[-1]),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
        )
    a1.set_xscale("log", base=2)
    a1.set_xticks(ns, ns)
    a1.set_xlabel("catalog size N (log scale)")
    a1.set_ylabel("SlateQ - learned-myopic\n(mean total reward)")
    a1.set_title("F4a  Gap vs catalog size")
    for i, n in enumerate(ns):
        s = g[g.num_candidates == n].sort_values("slate_size")
        col = ORDINAL[min(i, len(ORDINAL) - 1)]
        a2.errorbar(
            s.slate_size + 0.05 * (i - 2),
            s.mean_diff,
            yerr=[s.mean_diff - s.ci95_low, s.ci95_high - s.mean_diff],
            marker="o",
            ms=5,
            capsize=3,
            color=col,
        )
        a2.annotate(
            f"N={n}",
            (s.slate_size.iloc[-1], s.mean_diff.iloc[-1]),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
        )
    a2.set_xticks(ks, ks)
    a2.set_xlabel("slate size k")
    a2.set_title("F4b  Gap vs slate size")
    for ax in (a1, a2):
        ax.axhline(0, color=INK2, lw=1)
        ax.margins(x=0.15)
    save(
        fig,
        out,
        "F4_rq2_lines",
        "F4. RQ2: primary gap vs catalog size (a) and slate size (b). Points = mean over seeds; "
        "bars = seed-bootstrap 95% CI; darker = larger k (a) or larger N (b). Points are "
        "slightly offset horizontally to avoid overlap.",
        pilot,
    )


# ------------------------------------------------------------------------------------- traces
def load_traces(d: Path, condition: str = "matched") -> dict[str, list[pd.DataFrame]]:
    out: dict[str, list[pd.DataFrame]] = {}
    for a in AGENTS:
        eps = []
        for f in sorted((d / "traces").glob(f"{condition}_{a}_seed*.jsonl")):
            seed = int(f.stem.rsplit("seed", 1)[1])
            df = pd.read_json(f, lines=True)
            for e, g in df.groupby("episode"):
                g = g.sort_values("t").copy()
                g["seed"], g["ep"] = seed, e
                eps.append(g)
        if eps:
            out[a] = eps
    return out


def _clicked_quality(g: pd.DataFrame) -> np.ndarray:
    return np.array(
        [q[p] if p >= 0 else np.nan for q, p in zip(g.slate_qualities, g.clicked_pos, strict=True)]
    )


def _affinity(g: pd.DataFrame) -> np.ndarray:
    return np.array(
        [
            np.mean([u[c] for c in cl])
            for u, cl in zip(g.user_interests, g.slate_clusters, strict=True)
        ]
    )


def _binned(eps: list[pd.DataFrame], fn, width: int = 10, min_eps: int = 5):
    rows = []
    for g in eps:
        v = fn(g)
        for t, x in zip(g.t.to_numpy(), v, strict=True):
            rows.append((t // width, x))
    if not rows:
        return np.array([]), np.array([])
    df = pd.DataFrame(rows, columns=["b", "v"])
    agg = df.groupby("b").v.agg(["mean", "count"])
    alive = df.groupby("b").size()
    agg = agg[alive >= min_eps]
    return (agg.index.to_numpy() + 0.5) * width, agg["mean"].to_numpy()


def f5_trajectories(d: Path, out: Path, pilot: bool) -> None:
    tr = load_traces(d)
    if not tr:
        return
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.4))
    panels = [
        (
            "time budget remaining",
            lambda g: g.time_budget_after.to_numpy(),
            "F5a  Session time budget",
        ),
        (
            "clicked-item quality (hidden to agents)",
            _clicked_quality,
            "F5b  Quality of clicked items",
        ),
        (
            "distinct topics / slate size",
            lambda g: np.array([len(set(c)) / len(c) for c in g.slate_clusters]),
            "F5c  Slate topic diversity",
        ),
        ("user interest in shown topics", _affinity, "F5d  Interest in recommended topics"),
        (
            "mean user interest (all 20 topics)",
            lambda g: np.array([np.mean(u) for u in g.user_interests]),
            "F5e  User interest drift",
        ),
    ]
    for ax, (ylabel, fn, title) in zip(axes.flat, panels, strict=False):
        for a, eps in tr.items():
            x, y = _binned(eps, fn)
            if len(x):
                ax.plot(x, y, color=COLOR[a], marker=MARKER[a], ms=3, lw=1.6, label=LABEL[a])
        ax.set_title(title)
        ax.set_xlabel("step in session")
        ax.set_ylabel(ylabel)
    ax = axes.flat[5]
    sl = d / "session_lengths.csv"
    if sl.exists():
        s = pd.read_csv(sl)
        s = s[s.condition == "matched"]
        for a in AGENTS:
            r = s[s.agent == a].groupby("length").episodes.sum().sort_index()
            if r.empty:
                continue
            cdf = r.cumsum() / r.sum()
            ax.step(r.index, cdf, where="post", color=COLOR[a], label=LABEL[a], lw=1.6)
        ax.set_xlabel("session length (steps)")
        ax.set_ylabel("fraction of sessions <= length")
        ax.set_title("F5f  Session-length distribution")
    axes.flat[0].legend(loc="upper right")
    n_eps = sum(len(v) for v in tr.values()) // max(1, len(tr))
    fig.tight_layout()
    save(
        fig,
        out,
        "F5_trajectories",
        f"F5. Interest and session trajectories, N=10, k=3, matched model. Panels a-e: mean over "
        f"the {n_eps} traced eval episodes per agent (first 5 episodes of each seed, common "
        "random numbers), in 10-step bins; a bin is shown only while >= 5 episodes are still "
        "running, so later bins describe the longer sessions only. Quality is a hidden document "
        "property, read for plotting only. Panel f: empirical CDF of session length over all "
        "eval episodes and seeds.",
        pilot,
    )


def f6_case_study(d: Path, out: Path, pilot: bool) -> None:
    summ = json.loads((d / "summary.json").read_text("utf-8"))
    seed = summ.get("case_study_seed")
    tr = load_traces(d)
    if seed is None or not tr:
        return
    fig, (a1, a2) = plt.subplots(
        2, 1, figsize=(8.5, 5.6), sharex=True, gridspec_kw={"height_ratios": [1.3, 1]}
    )
    for a in AGENTS:
        eps = [g for g in tr.get(a, []) if g.seed.iloc[0] == seed and g.ep.iloc[0] == 0]
        if not eps:
            continue
        g = eps[0]
        a1.plot(
            g.t,
            g.time_budget_after,
            color=COLOR[a],
            lw=1.8,
            label=f"{LABEL[a]} ({len(g)} steps, reward {g.reward.sum():.1f})",
        )
        q = _clicked_quality(g)
        clicked = ~np.isnan(q)
        a2.scatter(
            g.t[clicked], q[clicked], s=10, color=COLOR[a], marker=MARKER[a], alpha=0.8, lw=0
        )
    a1.set_ylabel("time budget remaining")
    a1.set_title(f"F6  One user (run seed {seed}, eval episode 0) under each policy")
    a1.legend(loc="upper right")
    a2.axhline(0, color=INK2, lw=1)
    a2.set_ylabel("quality of clicked item")
    a2.set_xlabel("step in session")
    save(
        fig,
        out,
        "F6_case_study",
        f"F6. Case study: the same simulated user (run seed {seed}, eval episode 0; same initial "
        "state and candidates for every policy by common random numbers) under each policy. "
        "Seed chosen by the pre-registered rule PROTOCOL 14.5 (median primary gap). Top: time "
        "budget over the session (clicks on high-quality items extend it). Bottom: quality of "
        "each clicked item.",
        pilot,
    )


# ---------------------------------------------------------------------------------------- F7
def f7_rq3(d3: Path, out: Path, pilot: bool) -> None:
    if not (d3 / "gaps.csv").exists():
        return
    gp, ag = pd.read_csv(d3 / "gaps.csv"), pd.read_csv(d3 / "agents.csv")
    rungs = [r for r in RUNGS if r in set(gp.condition)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.8))
    for i, rung in enumerate(rungs):
        r = gp[(gp.condition == rung) & (gp.comparison == PRIMARY)]
        if r.empty or pd.isna(r.iloc[0].get("mean_diff")):
            continue
        r = r.iloc[0]
        seeds = seed_cols(r, "diff_seed")
        a1.scatter(
            np.full(len(seeds), i) + np.linspace(-0.1, 0.1, len(seeds)),
            seeds,
            s=14,
            color=INK2,
            alpha=0.5,
            lw=0,
        )
        a1.errorbar(
            i,
            r.mean_diff,
            yerr=[[r.mean_diff - r.ci95_low], [r.ci95_high - r.mean_diff]],
            fmt="o",
            ms=7,
            color="#2a78d6",
            capsize=4,
            elinewidth=2,
        )
        a1.annotate(
            f"{r.mean_diff:+.2f}",
            (i, r.mean_diff),
            xytext=(10, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
        )
    a1.axhline(0, color=INK2, lw=1)
    a1.set_xticks(range(len(rungs)), [RUNG_LABEL[r] for r in rungs])
    a1.set_ylabel("SlateQ - learned-myopic\n(mean total reward)")
    a1.set_title("F7a  Gap vs choice-model mismatch")
    for j, a in enumerate(AGENTS):
        xs, ys, lo, hi = [], [], [], []
        for i, rung in enumerate(rungs):
            r = ag[(ag.condition == rung) & (ag.agent == a)]
            if r.empty:
                continue
            r = r.iloc[0]
            xs.append(i + 0.12 * (j - 1.5))
            ys.append(r.mean_total_reward)
            lo.append(r.mean_total_reward - r.mean_total_reward_ci95_low)
            hi.append(r.mean_total_reward_ci95_high - r.mean_total_reward)
        a2.errorbar(
            xs,
            ys,
            yerr=[lo, hi],
            fmt=MARKER[a],
            ms=6,
            color=COLOR[a],
            capsize=3,
            ls="none",
            label=LABEL[a],
        )
    a2.set_xticks(range(len(rungs)), [RUNG_LABEL[r] for r in rungs])
    a2.set_ylabel("mean total reward per episode")
    a2.set_title("F7b  Absolute engagement per condition")
    a2.legend(loc="best")
    save(
        fig,
        out,
        "F7_rq3",
        "F7. RQ3, N=10, k=3: the user's TRUE choice model departs from the multinomial-"
        "proportional model SlateQ assumes (PROTOCOL 15.2; 'matched' reuses the RQ1 runs). "
        "(a) primary gap per condition: mean over seeds, seed-bootstrap 95% CI, dots = seeds. "
        "(b) absolute mean total reward per agent with seed-bootstrap 95% CI; reward scale "
        "differs between conditions because click rates differ.",
        pilot,
    )


# ---------------------------------------------------------------------------------------- F8
def f8_action_count(out: Path) -> None:
    ns = [5, 10, 20, 40, 80]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for i, k in enumerate((2, 3, 5)):
        y = [math.perm(n, k) for n in ns if n >= k]
        x = [n for n in ns if n >= k]
        ax.plot(x, y, marker="o", ms=5, color=ORDINAL[1 + 2 * i] if 1 + 2 * i < 5 else ORDINAL[-1])
        ax.annotate(
            f"ordered slates, k={k}",
            (x[-1], y[-1]),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
        )
    ax.plot(ns, ns, marker="s", ms=5, color="#eb6834")
    ax.annotate(
        "SlateQ: items scored per step (N)",
        (ns[-1], ns[-1]),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontsize=8,
    )
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(ns, ns)
    ax.set_xlabel("catalog size N")
    ax.set_ylabel("number of actions to evaluate (log)")
    ax.set_title("F8  Why decomposition: action count")
    ax.margins(x=0.45)
    save(
        fig,
        out,
        "F8_action_count",
        "F8. Number of ordered slates N!/(N-k)! a non-decomposed (full-slate) Q-function must "
        "evaluate per step, versus the N item values SlateQ's decomposition needs. Exact "
        "arithmetic, not a measurement; FullSlateQ itself was not run (DEVIATIONS D9).",
        False,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rq2", type=Path, default=REPO_ROOT / "results" / "rq2")
    ap.add_argument("--rq3", type=Path, default=REPO_ROOT / "results" / "rq3")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "results" / "figures")
    args = ap.parse_args()
    style()
    pilot = json.loads((args.rq2 / "summary.json").read_text("utf-8")).get("pilot", False)
    print(f"figures from {args.rq2}{' (PILOT)' if pilot else ''} -> {args.out}")
    f1_curves(args.rq2, args.out, pilot)
    f2_headline(args.rq2, args.out, pilot)
    f3_heatmap(args.rq2, args.out, pilot)
    f4_lines(args.rq2, args.out, pilot)
    f5_trajectories(args.rq2, args.out, pilot)
    f6_case_study(args.rq2, args.out, pilot)
    if (args.rq3 / "summary.json").exists():
        p3 = json.loads((args.rq3 / "summary.json").read_text("utf-8")).get("pilot", False)
        f7_rq3(args.rq3, args.out, p3)
    f8_action_count(args.out)
    lines = [
        "# Figure captions",
        "",
        "Generated by `scripts/figures.py`; error bars are defined in each caption.",
        "",
    ] + [f"- **{k}**: {v}" for k, v in CAPTIONS.items()]
    (args.out / "CAPTIONS.md").write_text("\n".join(lines) + "\n", "utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
