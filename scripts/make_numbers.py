"""Generate docs/NUMBERS.md and the README results block from the committed result tables.

    python scripts/make_numbers.py [--rq2 results/rq2] [--rq3 results/rq3] [--no-readme]

Every number that appears in the report, README or slides must appear here, with the file it comes
from and the command that regenerates it. Nothing is typed by hand.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

from slateq_study.io import REPO_ROOT

PRIMARY = "SlateQ - learned-myopic"
LABEL = {
    "slateq": "SlateQ",
    "learned_myopic": "learned-myopic",
    "oracle_myopic": "oracle-myopic",
    "random": "random",
}
RUNG = {
    "matched": "matched (proportional, no-click mass 1)",
    "mild_noclick3": "mild (proportional, no-click mass 3)",
    "moderate_logit": "moderate (multinomial logit)",
    "severe_cascade": "severe (proportional cascade)",
}
VERDICT = {
    "A higher": "first higher (clear)",
    "A lower": "first lower (clear)",
    "no clear difference": "no clear difference",
    "insufficient seeds": "insufficient seeds",
    "missing": "missing",
}


def f(x, d=2, sign=False):
    if x is None or pd.isna(x):
        return "n/a"
    return f"{x:+.{d}f}" if sign else f"{x:.{d}f}"


def ci(r):
    return f"[{f(r.ci95_low, sign=True)}, {f(r.ci95_high, sign=True)}]"


def seeds_list(r, prefix="diff_seed"):
    cols = sorted(
        (c for c in r.index if c.startswith(prefix) and not pd.isna(r[c])),
        key=lambda c: int(c[len(prefix) :]),
    )
    return ", ".join(f"{c[len(prefix) :]}: {f(r[c], sign=True)}" for c in cols)


# ------------------------------------------------------------------------------- Phase 6b
P6B_LABEL = {
    **LABEL,
    "lm_lr1e-3": "learned-myopic (lr 1e-3)",
    "slateq_lr2.5e-4": "SlateQ (lr 2.5e-4)",
    "slateq_g0.5": "SlateQ (gamma 0.5)",
    "slateq_g0.9": "SlateQ (gamma 0.9)",
    "slateq_g0.95": "SlateQ (gamma 0.95)",
    "slateq_2x": "SlateQ (600K steps)",
    "lm_2x": "learned-myopic (600K steps)",
}


def gap_table(rows: pd.DataFrame) -> list[str]:
    """One markdown row per comparison: cell, mean, CI, per seed, verdict."""
    out = [
        "| comparison | (N, k) | mean | 95% CI | per seed | verdict |",
        "|---|---|---|---|---|---|",
    ]
    for _, r in rows.iterrows():
        out.append(
            f"| {r.comparison} | ({r.num_candidates}, {r.slate_size}) | "
            f"{f(r.get('mean_diff'), sign=True)} | {ci(r)} | {seeds_list(r)} | "
            f"{VERDICT.get(r.verdict, r.verdict)} |"
        )
    return out


def phase6b_lines(d: Path, rel) -> list[str]:
    """NUMBERS section for PROTOCOL 16 (E1-E5). Empty if the analysis has not been run."""
    if not (d / "gaps.csv").exists():
        return []
    gp = pd.read_csv(d / "gaps.csv")
    ag = pd.read_csv(d / "agents.csv")
    summ = json.loads((d / "summary.json").read_text("utf-8"))
    L = [
        "## Phase 6b (follow-up, registered after the Phase 6 results were seen; PROTOCOL 16)",
        "",
        f"Source: `{rel(d / 'gaps.csv')}`, `{rel(d / 'agents.csv')}`, "
        f"`{rel(d / 'clicks_watch_gaps.csv')}` (`python scripts/phase6b_analyze.py`). "
        f"Phase 6b run status: {summ.get('runs')}. Tables commit: "
        f"`{(summ.get('provenance') or {}).get('git_sha')}`.",
        "Baselines are the rq2 runs of the same cells and seeds (PROTOCOL 16.1).",
        "",
    ]
    for tag, title in (
        ("E1", "E1: matched learning rates"),
        ("E2", "E2: planning horizon (all at lr 1e-3)"),
        ("E3", "E3: twice the training budget at (80, 3)"),
        ("E4", "E4: the SlateQ paper's cascade (N=10, k=3)"),
    ):
        rows = gp[gp.comparison.str.startswith(tag + ":")]
        if rows.empty:
            continue
        L += [f"### {title}", ""] + gap_table(rows) + [""]

    L += [
        "### Mean watch time per session of each agent or variant",
        "",
        "| condition | (N, k) | agent | mean | 95% CI | session length | clicked quality | seeds |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, r in ag.sort_values(["condition", "num_candidates", "agent"]).iterrows():
        lo, hi = r.get("mean_total_reward_ci95_low"), r.get("mean_total_reward_ci95_high")
        L.append(
            f"| {r.condition} | ({r.num_candidates}, {r.slate_size}) | "
            f"{P6B_LABEL.get(r.agent, r.agent)} | {f(r.get('mean_total_reward'))} | "
            f"[{f(lo)}, {f(hi)}] | {f(r.get('mean_length'), 1)} | "
            f"{f(r.get('mean_clicked_quality'), 3)} | {r.n_seeds} |"
        )
    L.append("")

    cw = d / "clicks_watch_gaps.csv"
    if cw.exists():
        e5 = pd.read_csv(cw)
        L += [
            "### E5: clicks versus watch time (rq2, rq3 and E4 runs)",
            "",
            "Click rate = clicks per recommendation step; watch time = total reward per session. "
            "Each difference is the myopic agent minus SlateQ, with the PROTOCOL 14.6 verdict.",
            "",
            "| condition | (N, k) | comparison | click rate diff [CI] | verdict | "
            "watch time diff [CI] | verdict | pattern |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for _, r in e5.iterrows():
            click = (
                f"{f(r.click_rate_diff, 4, True)} [{f(r.click_rate_ci95_low, 4, True)}, "
                f"{f(r.click_rate_ci95_high, 4, True)}]"
            )
            watch = (
                f"{f(r.watch_per_session_diff, 2, True)} "
                f"[{f(r.watch_per_session_ci95_low, 2, True)}, "
                f"{f(r.watch_per_session_ci95_high, 2, True)}]"
            )
            cond = f"{r.condition}{' (control)' if r.control else ''}"
            L.append(
                f"| {cond} | ({r.num_candidates}, {r.slate_size}) | {r.comparison} | {click} | "
                f"{r.click_rate_verdict} | {watch} | {r.watch_per_session_verdict} | {r.pattern} |"
            )
        L += ["", "Pattern counts (all cells and conditions, controls included):", ""]
        for comp, g in e5.groupby("comparison"):
            counts = g.pattern.value_counts()
            L.append(f"- {comp}: " + "; ".join(f"{k}: {v}" for k, v in counts.items()) + ".")
        L.append("")
    return L


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rq2", type=Path, default=REPO_ROOT / "results" / "rq2")
    ap.add_argument("--rq3", type=Path, default=REPO_ROOT / "results" / "rq3")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "docs" / "NUMBERS.md")
    ap.add_argument("--no-readme", action="store_true")
    args = ap.parse_args()
    rel = lambda p: Path(p).resolve().relative_to(REPO_ROOT).as_posix()  # noqa: E731

    s2 = json.loads((args.rq2 / "summary.json").read_text("utf-8"))
    pilot = bool(s2.get("pilot"))
    ag = pd.read_csv(args.rq2 / "agents.csv")
    gp = pd.read_csv(args.rq2 / "gaps.csv")
    p3 = REPO_ROOT / "results" / "phase3"
    budget = json.loads((p3 / "budget.json").read_text("utf-8"))
    tune = json.loads((p3 / "tune.json").read_text("utf-8"))

    L = [
        "# Numbers",
        "",
        "Auto-generated by `python scripts/make_numbers.py` (after `scripts/analyze.py`). Do not edit by hand.",
        "Every number in the report, README, slides and site traces back to a row here.",
        "",
    ]
    if pilot:
        L += ["> **PILOT DATA** - these tables come from a plumbing run and are NOT results.", ""]
    L += [
        f"Source commit of the tables: `{(s2.get('provenance') or {}).get('git_sha')}`. "
        f"Run status (RQ1/RQ2 sweep): {s2.get('runs')}.",
        "",
    ]

    # frozen settings
    L += [
        "## Frozen settings (PROTOCOL 12.6)",
        "",
        "| Quantity | Value | Source |",
        "|---|---|---|",
        f"| training budget (steps) | {budget['budget']} | `results/phase3/budget.json` |",
        f"| eval episodes per run | {tune['episode_recheck']['eval_episodes']} | `results/phase3/tune.json` |",
    ]
    for a, v in tune["selected"].items():
        L.append(
            f"| {LABEL[a]} learning rate / target period | {v['learning_rate']} / "
            f"{v['target_update_period']} | `results/phase3/tune.json` |"
        )
    L.append("")

    # RQ1
    src = f"`{rel(args.rq2 / 'gaps.csv')}`, `{rel(args.rq2 / 'agents.csv')}`"
    L += ["## RQ1: primary cell N=10, k=3 (matched choice model)", "", f"Source: {src}.", ""]
    cell = ag[(ag.condition == "matched") & (ag.num_candidates == 10) & (ag.slate_size == 3)]
    L += [
        "| Policy | mean total reward | 95% CI | SD over seeds | session length | clicks | "
        "clicked quality | seeds |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for a in ("slateq", "learned_myopic", "oracle_myopic", "random"):
        r = cell[cell.agent == a]
        if r.empty:
            continue
        r = r.iloc[0]
        L.append(
            f"| {LABEL[a]} | {f(r.mean_total_reward)} | [{f(r.mean_total_reward_ci95_low)}, "
            f"{f(r.mean_total_reward_ci95_high)}] | {f(r.mean_total_reward_std)} | "
            f"{f(r.mean_length, 1)} | {f(r.mean_clicks, 1)} | {f(r.mean_clicked_quality, 3)} | "
            f"{int(r.n_seeds)} |"
        )
    L.append("")
    g1 = gp[(gp.condition == "matched") & (gp.num_candidates == 10) & (gp.slate_size == 3)]
    L += [
        "| Comparison (A - B) | mean | 95% CI | SD | per seed | verdict (PROTOCOL 14.6) |",
        "|---|---|---|---|---|---|",
    ]
    for _, r in g1.sort_values("primary", ascending=False).iterrows():
        name = ("**PRIMARY** " if r.primary else "") + r.comparison
        L.append(
            f"| {name} | {f(r.get('mean_diff'), sign=True)} | {ci(r)} | {f(r.get('std_diff'))} | "
            f"{seeds_list(r)} | {VERDICT.get(r.verdict, r.verdict)} |"
        )
    L += [
        "",
        f"Case-study seed (PROTOCOL 14.5, median primary gap): **{s2.get('case_study_seed')}**.",
        "",
    ]

    # RQ2
    L += [
        "## RQ2: primary gap (SlateQ - learned-myopic) per cell",
        "",
        f"Source: `{rel(args.rq2 / 'gaps.csv')}`.",
        "",
        "| N | k | mean | 95% CI | per seed | seeds | verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    g2 = gp[(gp.condition == "matched") & (gp.comparison == PRIMARY)].sort_values(
        ["control", "num_candidates", "slate_size"]
    )
    for _, r in g2.iterrows():
        tag = " (control)" if r.control else ""
        L.append(
            f"| {r.num_candidates} | {r.slate_size}{tag} | {f(r.get('mean_diff'), sign=True)} | {ci(r)} | "
            f"{seeds_list(r)} | {int(r.n_seeds)} | {VERDICT.get(r.verdict, r.verdict)} |"
        )
    main_cells = g2[~g2.control]
    counts = main_cells.verdict.value_counts().to_dict()
    L += [
        "",
        f"Verdict counts over the {len(main_cells)} grid cells (control excluded): "
        + ", ".join(f"{VERDICT.get(k, k)}: {v}" for k, v in counts.items())
        + ".",
        "",
    ]

    # RQ2 secondary comparisons and per-agent mechanism columns (pre-registered secondary metrics)
    L += [
        "### RQ2: secondary comparisons and mechanism per cell",
        "",
        f"Source: `{rel(args.rq2 / 'gaps.csv')}`, `{rel(args.rq2 / 'agents.csv')}`. "
        "Reward / clicked quality / session length are means over seeds of per-run means.",
        "",
        "| N | k | SlateQ - oracle | LM - oracle | reward SlateQ / LM / oracle / random "
        "| clicked quality SlateQ / LM / oracle | session length SlateQ / LM / oracle |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in g2.iterrows():
        n, k, c = r.num_candidates, r.slate_size, r.control

        def gap(name, n=n, k=k, c=c):
            x = gp[
                (gp.condition == "matched")
                & (gp.num_candidates == n)
                & (gp.slate_size == k)
                & (gp.control == c)
                & (gp.comparison == name)
            ]
            if x.empty:
                return "n/a"
            x = x.iloc[0]
            return f"{f(x.mean_diff, sign=True)} ({VERDICT.get(x.verdict, x.verdict)})"

        def col(metric, agents, d, n=n, k=k, c=c):
            out = []
            for a in agents:
                x = ag[
                    (ag.condition == "matched")
                    & (ag.num_candidates == n)
                    & (ag.slate_size == k)
                    & (ag.control == c)
                    & (ag.agent == a)
                ]
                out.append(f(x.iloc[0][metric], d) if not x.empty else "n/a")
            return " / ".join(out)

        tri = ("slateq", "learned_myopic", "oracle_myopic")
        L.append(
            f"| {n} | {k}{' (control)' if c else ''} | {gap('SlateQ - oracle-myopic')} | "
            f"{gap('learned-myopic - oracle-myopic')} | "
            f"{col('mean_total_reward', (*tri, 'random'), 2)} | "
            f"{col('mean_clicked_quality', tri, 3)} | {col('mean_length', tri, 1)} |"
        )
    L.append("")

    # RQ3
    rq3_lines = []
    if (args.rq3 / "gaps.csv").exists():
        g3, a3 = pd.read_csv(args.rq3 / "gaps.csv"), pd.read_csv(args.rq3 / "agents.csv")
        L += [
            "## RQ3: misspecified choice model (N=10, k=3)",
            "",
            f"Source: `{rel(args.rq3 / 'gaps.csv')}`, `{rel(args.rq3 / 'agents.csv')}`.",
            "",
            "| Condition | SlateQ - learned-myopic | 95% CI | relative to learned-myopic | per seed | verdict |",
            "|---|---|---|---|---|---|",
        ]
        for rung in RUNG:
            r = g3[(g3.condition == rung) & (g3.comparison == PRIMARY)]
            if r.empty:
                continue
            r = r.iloc[0]
            rel_gap = "n/a" if pd.isna(r.get("relative_to_b")) else f"{100 * r.relative_to_b:+.2f}%"
            line = (
                f"| {RUNG[rung]} | {f(r.get('mean_diff'), sign=True)} | {ci(r)} | {rel_gap} | "
                f"{seeds_list(r)} | {VERDICT.get(r.verdict, r.verdict)} |"
            )
            L.append(line)
            rq3_lines.append((rung, r))
        L += ["", "| Condition | " + " | ".join(LABEL.values()) + " |", "|---|---|---|---|---|"]
        for rung in RUNG:
            vals = []
            for a in LABEL:
                r = a3[(a3.condition == rung) & (a3.agent == a)]
                vals.append(f(r.iloc[0].mean_total_reward) if not r.empty else "n/a")
            L.append(f"| {RUNG[rung]} | " + " | ".join(vals) + " |")
        L += [
            "",
            "Session length and clicked quality (mechanism), same source:",
            "",
            "| Condition | session length "
            + " / ".join(LABEL.values())
            + " | clicked quality "
            + " / ".join(LABEL.values())
            + " |",
            "|---|---|---|",
        ]
        for rung in RUNG:
            parts = []
            for metric, d in (("mean_length", 1), ("mean_clicked_quality", 3)):
                vals = []
                for a in LABEL:
                    r = a3[(a3.condition == rung) & (a3.agent == a)]
                    vals.append(f(r.iloc[0][metric], d) if not r.empty else "n/a")
                parts.append(" / ".join(vals))
            L.append(f"| {RUNG[rung]} | " + " | ".join(parts) + " |")
        L.append("")

    L += phase6b_lines(REPO_ROOT / "results" / "phase6b", rel)
    args.out.write_text("\n".join(L) + "\n", "utf-8")
    print(f"wrote {args.out}{' (PILOT)' if pilot else ''}")

    if not args.no_readme and not pilot:
        p = g1[g1.primary]
        block = [
            "_Generated by `scripts/make_numbers.py`; full tables in [docs/NUMBERS.md](docs/NUMBERS.md), "
            "figures in [results/figures](results/figures)._",
            "",
        ]
        if not p.empty:
            r = p.iloc[0]
            block.append(
                f"- **RQ1** (N=10, k=3, {int(r.n_seeds)} seeds): SlateQ - learned-myopic = "
                f"**{f(r.mean_diff, sign=True)}** watch time per session, 95% CI {ci(r)}; "
                f"{VERDICT.get(r.verdict, r.verdict)}."
            )
        block.append(
            f"- **RQ2**: over {len(main_cells)} (N, k) cells: "
            + ", ".join(f"{VERDICT.get(k, k)} in {v}" for k, v in counts.items())
            + "."
        )
        for rung, r in rq3_lines:
            block.append(
                f"- **RQ3**, {RUNG[rung]}: {f(r.mean_diff, sign=True)} {ci(r)}; "
                f"{VERDICT.get(r.verdict, r.verdict)}."
            )
        readme = REPO_ROOT / "README.md"
        text = readme.read_text("utf-8")
        text = re.sub(
            r"(<!-- RESULTS:START -->\n).*?(\n<!-- RESULTS:END -->)",
            lambda m: m.group(1) + "\n".join(block) + m.group(2),
            text,
            flags=re.S,
        )
        readme.write_text(text, "utf-8")
        print("updated README results block")
    return 0


if __name__ == "__main__":
    sys.exit(main())
