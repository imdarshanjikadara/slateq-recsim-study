"""Phase 6b figures F9-F11 from results/phase6b (PROTOCOL 16).

    python scripts/phase6b_figures.py [--d results/phase6b] [--out results/figures]

F9   planning horizon: SlateQ minus the oracle-myopic baseline for gamma = 0 ... 0.99 (E2)
F10  clicks versus watch time per agent (E5)
F11  follow-up gaps in one view: E1, E3 and E4 primary comparisons
Uses the same style and palette as scripts/figures.py. Captions go to CAPTIONS_PHASE6B.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figures as fg  # noqa: E402  (shared style, palette and save helper)

from slateq_study.io import REPO_ROOT  # noqa: E402

plt = fg.plt
GAMMAS = ["0", "0.5", "0.9", "0.95", "0.99"]


def errbar(ax, x, r, color, label=None, marker="o"):
    """Mean with its seed-bootstrap 95% CI."""
    ax.errorbar(
        x,
        r.mean_diff,
        yerr=[[r.mean_diff - r.ci95_low], [r.ci95_high - r.mean_diff]],
        fmt=marker,
        ms=6,
        color=color,
        capsize=3,
        elinewidth=1.5,
        label=label,
    )


# ---------------------------------------------------------------------------------------- F9
def f9_horizon(gp: pd.DataFrame, out: Path) -> None:
    cells = [(10, 3), (80, 3)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, (n, k) in zip(axes, cells, strict=True):
        sub = gp[(gp.num_candidates == n) & (gp.slate_size == k)]
        xs, ys = [], []
        for i, g in enumerate(GAMMAS):
            label = (
                "E1: learned-myopic (lr 1e-3) - oracle-myopic"
                if g == "0"
                else f"E2: gamma {g} - oracle-myopic"
            )
            r = sub[sub.comparison == label]
            if r.empty or pd.isna(r.iloc[0].get("mean_diff")):
                continue
            r = r.iloc[0]
            errbar(ax, i, r, fg.COLOR["slateq"])
            seeds = fg.seed_cols(r, "diff_seed")
            ax.scatter(
                np.full(len(seeds), i) + np.linspace(-0.08, 0.08, len(seeds)),
                seeds,
                s=10,
                color=fg.INK2,
                alpha=0.45,
                lw=0,
            )
            xs.append(i)
            ys.append(r.mean_diff)
        ax.plot(xs, ys, color=fg.COLOR["slateq"], lw=1, alpha=0.6)
        ax.axhline(0, color=fg.INK2, lw=0.8)
        ax.set_xticks(range(len(GAMMAS)), [f"γ = {g}" for g in GAMMAS])
        ax.set_title(f"N = {n}, k = {k}")
        ax.set_ylabel("watch time per session,\nagent minus oracle-myopic")
    fig.suptitle("How much does planning ahead pay? (all at learning rate 1e-3)", y=1.02)
    fg.save(
        fig,
        out,
        "F9_horizon",
        "E2 (PROTOCOL 16.4). SlateQ trained with discount γ, minus the privileged oracle-myopic "
        "baseline (the best click-maximiser), in watch time per session. γ = 0 is learned-myopic "
        "at lr 1e-3 (E1); γ = 0.99 is the rq2 SlateQ run. Dots: per-seed paired differences; "
        "bars: seed-bootstrap 95% CI over 5 seeds. Panels have different y-scales.",
        False,
    )


# --------------------------------------------------------------------------------------- F10
def f10_clicks_watch(cw: pd.DataFrame, out: Path) -> None:
    panels = [("matched", 10, 3), ("matched", 80, 3), ("paper_cascade", 10, 3)]
    panels = [p for p in panels if not cw[(cw.condition == p[0])].empty]
    fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 3.6), squeeze=False)
    for ax, (cond, n, k) in zip(axes[0], panels, strict=True):
        sub = cw[(cw.condition == cond) & (cw.num_candidates == n) & (cw.slate_size == k)]
        for agent in fg.AGENTS:
            r = sub[sub.agent == agent]
            if r.empty:
                continue
            r = r.iloc[0]
            ax.errorbar(
                r.click_rate,
                r.watch_per_session,
                xerr=[
                    [r.click_rate - r.click_rate_ci95_low],
                    [r.click_rate_ci95_high - r.click_rate],
                ],
                yerr=[
                    [r.watch_per_session - r.watch_per_session_ci95_low],
                    [r.watch_per_session_ci95_high - r.watch_per_session],
                ],
                fmt=fg.MARKER[agent],
                ms=7,
                color=fg.COLOR[agent],
                capsize=2,
                label=fg.LABEL[agent],
            )
        ax.set_xlabel("click rate (clicks per recommendation)")
        ax.set_ylabel("watch time per session")
        ax.set_title(f"{cond.replace('_', ' ')}, N = {n}, k = {k}")
    axes[0][0].legend(loc="best")
    fig.suptitle("Clicks versus watch time (E5)", y=1.02)
    fg.save(
        fig,
        out,
        "F10_clicks_watch",
        "E5 (PROTOCOL 16.7). Each marker is one agent: mean over 5 seeds of the click rate "
        "(clicks / recommendation steps, pooled over 2400 evaluation sessions) and of watch time "
        "per session; bars are seed-bootstrap 95% CIs. Oracle-myopic is the best click-maximiser "
        "in the simulator. Panels have different axis ranges. Simulator only; no claim about "
        "any real platform.",
        False,
    )


# --------------------------------------------------------------------------------------- F11
def f11_followups(gp: pd.DataFrame, out: Path) -> None:
    rows = gp[gp.primary.astype(str) == "True"].copy()
    rows = rows[rows.comparison.str.match(r"E[134]:")]
    if rows.empty:
        return
    rows["name"] = rows.comparison + "  (" + rows.num_candidates.astype(str) + ", "
    rows["name"] += rows.slate_size.astype(str) + ")"
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(rows) + 1.2))
    for i, (_, r) in enumerate(rows.iterrows()):
        if pd.isna(r.get("mean_diff")):
            continue
        ax.errorbar(
            r.mean_diff,
            i,
            xerr=[[r.mean_diff - r.ci95_low], [r.ci95_high - r.mean_diff]],
            fmt="o",
            color=fg.COLOR["slateq"],
            capsize=3,
        )
        ax.annotate(
            f"{r.mean_diff:+.2f}", (r.ci95_high, i), xytext=(6, -3), textcoords="offset points"
        )
    ax.axvline(0, color=fg.INK2, lw=0.8)
    ax.set_yticks(range(len(rows)), rows.name)
    ax.invert_yaxis()
    ax.set_xlabel("SlateQ minus learned-myopic, watch time per session")
    ax.set_title("Phase 6b follow-up gaps (primary comparisons)")
    fg.save(
        fig,
        out,
        "F11_followups",
        "Primary comparisons of E1 (matched learning rates), E3 (600K steps) and E4 (the SlateQ "
        "paper's cascade): mean over 5 seeds with seed-bootstrap 95% CI. Exploratory, registered "
        "after the Phase 6 results were seen (PROTOCOL 16).",
        False,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--d", type=Path, default=REPO_ROOT / "results" / "phase6b")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "results" / "figures")
    args = ap.parse_args()
    fg.style()
    gp = pd.read_csv(args.d / "gaps.csv")
    f9_horizon(gp, args.out)
    f10_clicks_watch(pd.read_csv(args.d / "clicks_watch.csv"), args.out)
    f11_followups(gp, args.out)
    lines = ["# Figure captions (Phase 6b)", "", "Generated by `scripts/phase6b_figures.py`.", ""]
    lines += [f"- **{k}**: {v}" for k, v in fg.CAPTIONS.items()]
    (args.out / "CAPTIONS_PHASE6B.md").write_text("\n".join(lines) + "\n", "utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
