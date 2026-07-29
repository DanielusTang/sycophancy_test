#!/usr/bin/env python3
"""Render Panel B of the introduction teaser figure (`fig:teaser`).

Twenty real runs drawn from the naturalistic false-presupposition corpus, each a
horizontal ribbon of 25 cells shaded by position strength, sorted by collapse turn,
with the five-turn horizon of prior protocols cut through as a vertical rule.

The point of the panel: most of the collapse markers sit to the *right* of that rule,
and even the runs that never collapse are mottled with low scores throughout.

Companion to writing/paperbanana_fig0_teaser_prompt.md (§6, composite path).

    python3 writing/make_fig0_panelB.py            # -> writing/fig0_panelB.pdf
    python3 writing/make_fig0_panelB.py --png      # also write a PNG preview
"""

import argparse
import glob
import json
import os
import random
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(REPO, "false_presuppositions", "outputs", "naturalistic", "sonnet_5")
TARGETS = [
    "deepseek_v4_pro",
    "gemini_3.1_pro",
    "gpt_5.6_terra",
    "olmo3_7b_base",
    "olmo3_7b_instruct",
    "olmo3_7b_think",
    "sonnet_5",
]

MAX_TURNS = 25
HORIZON = 5          # the five-turn cap used by prior multi-turn protocols
SEED = 7             # reproduces the row set documented in the prompt file
N_EARLY, N_LATE, N_HELD = 6, 10, 4

# Muted academic palette. Strength 1-4 is a single sequential ramp (pale = eroding,
# dark = holding); collapse gets the one accent colour in the figure.
COLLAPSE = "#c0392b"
RAMP = ["#dfe6ec", "#a9bed2", "#6d8ead", "#31556f"]   # s = 1, 2, 3, 4
BLANK = "#ffffff"                                      # run already over


def load_run(path):
    """Return (outcome, collapsed_at_turn, {turn: strength}) or None if unreadable."""
    result, strengths = None, {}
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                kind = rec.get("type")
                if kind == "result":
                    result = rec
                elif kind == "turn" and (rec.get("turn") or 0) >= 1:
                    # turn 0 is the unscored baseline; it never enters the ribbon
                    strengths[rec["turn"]] = rec.get("position_strength")
    except (OSError, json.JSONDecodeError):
        return None
    if result is None:
        return "incomplete", None, strengths
    collapsed_at = result.get("collapsed_at_turn") if result.get("outcome") == "collapsed" else None
    return result.get("outcome"), collapsed_at, strengths


def collect():
    """All runs, including incomplete ones.

    An incomplete run has no `result` record and so no verdict. It still counts as a
    run that did not collapse -- the standing convention is that a long run without a
    verdict is held, not excluded, since dropping it would silently inflate the
    collapse rate.
    """
    runs, n_incomplete = [], 0
    for target in TARGETS:
        pattern = os.path.join(CORPUS, target, "**", "*.jsonl")
        for path in sorted(glob.glob(pattern, recursive=True)):
            loaded = load_run(path)
            if loaded is None:
                continue
            outcome, collapsed_at, strengths = loaded
            if outcome == "incomplete":
                n_incomplete += 1
                continue  # counted in the stats, kept out of the drawn sample
            runs.append(
                {
                    "target": target,
                    "file": os.path.basename(path),
                    "outcome": outcome,
                    "collapsed_at": collapsed_at,
                    "strengths": strengths,
                }
            )
    return runs, n_incomplete


def sample_rows(runs, n_incomplete):
    early = [r for r in runs if r["collapsed_at"] and r["collapsed_at"] <= HORIZON]
    late = [r for r in runs if r["collapsed_at"] and r["collapsed_at"] > HORIZON]
    held = [r for r in runs if not r["collapsed_at"]]

    if len(early) < N_EARLY or len(late) < N_LATE or len(held) < N_HELD:
        sys.exit(
            f"corpus too small to sample: early={len(early)} late={len(late)} held={len(held)}"
        )

    rng = random.Random(SEED)
    rows = rng.sample(early, N_EARLY) + rng.sample(late, N_LATE) + rng.sample(held, N_HELD)
    rows.sort(key=lambda r: (r["collapsed_at"] or MAX_TURNS + 1))

    # Fail loudly if the corpus shifts under us rather than silently redrawing.
    n_early = sum(1 for r in rows if r["collapsed_at"] and r["collapsed_at"] <= HORIZON)
    n_late = sum(1 for r in rows if r["collapsed_at"] and r["collapsed_at"] > HORIZON)
    n_held = sum(1 for r in rows if not r["collapsed_at"])
    assert (n_early, n_late, n_held) == (N_EARLY, N_LATE, N_HELD), (n_early, n_late, n_held)
    for r in rows:
        if r["collapsed_at"]:
            assert r["strengths"].get(r["collapsed_at"]) == 0, (
                f"{r['file']}: collapse turn {r['collapsed_at']} is not strength 0"
            )
    # Incomplete runs join the never-collapsed bucket and the corpus total.
    return rows, (len(runs) + n_incomplete, len(early), len(late), len(held) + n_incomplete)


def build_grid(rows):
    """-1 = run over (blank), 0 = collapse, 1..4 = position strength."""
    grid = np.full((len(rows), MAX_TURNS), -1.0)
    for i, run in enumerate(rows):
        end = run["collapsed_at"] or MAX_TURNS
        for t in range(1, end + 1):
            s = run["strengths"].get(t)
            if s is not None:
                grid[i, t - 1] = s
    return grid


def render(rows, grid, stats, out_pdf, also_png):
    total, n_early_all, n_late_all, n_held_all = stats
    surviving = total - n_early_all

    mpl.rcParams.update({"font.family": "sans-serif", "font.size": 8})

    cmap = ListedColormap([BLANK, COLLAPSE] + RAMP)
    norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5], cmap.N)

    fig, ax = plt.subplots(figsize=(9.0, 3.4))
    ax.pcolormesh(
        np.arange(MAX_TURNS + 1) + 0.5,
        np.arange(len(rows) + 1),
        grid,
        cmap=cmap,
        norm=norm,
        edgecolors="white",
        linewidth=0.6,
    )
    ax.invert_yaxis()

    # The five-turn horizon: the strongest line in the panel, matching Panel A.
    ax.axvline(HORIZON + 0.5, color="#111111", linewidth=2.4, zorder=5)

    ax.set_xlim(0.5, MAX_TURNS + 0.5)
    ax.set_xticks([1, 5, 10, 15, 20, 25])
    ax.set_xlabel("turn $t$", labelpad=2)
    ax.set_yticks(np.arange(len(rows)) + 0.5)
    ax.set_yticklabels([r["target"] for r in rows], fontsize=6)
    ax.tick_params(axis="y", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Right-edge annotation: what a five-turn instrument would have concluded.
    for i, run in enumerate(rows):
        if run["collapsed_at"] and run["collapsed_at"] <= HORIZON:
            note, colour = "caught by 5 turns", "#555555"
        elif run["collapsed_at"]:
            note, colour = f"MISSED — collapses t={run['collapsed_at']}", COLLAPSE
        else:
            note, colour = "held, but eroding", "#555555"
        ax.text(MAX_TURNS + 1.0, i + 0.5, note, va="center", ha="left",
                fontsize=6, color=colour)

    # Brackets sit below the tick labels, in axes-fraction coordinates so they never
    # collide with them. Data x -> fraction: (x - 0.5) / MAX_TURNS.
    def frac(x):
        return (x - 0.5) / MAX_TURNS

    for x0, x1, label, colour in [
        (frac(0.5), frac(HORIZON + 0.5), "prior work sees only this", "#555555"),
        (frac(HORIZON + 0.5), frac(MAX_TURNS + 0.5), "invisible to a five-turn budget", "#111111"),
    ]:
        y = -0.22
        ax.plot([x0, x1], [y, y], transform=ax.transAxes, color=colour,
                linewidth=0.9, clip_on=False)
        for xe in (x0, x1):
            ax.plot([xe, xe], [y, y + 0.022], transform=ax.transAxes, color=colour,
                    linewidth=0.9, clip_on=False)
        ax.text((x0 + x1) / 2, y - 0.055, label, transform=ax.transAxes,
                ha="center", va="top", fontsize=7, color=colour)

    ax.text(
        HORIZON + 0.8, -0.35, "five-turn horizon of prior protocols",
        fontsize=7, color="#111111", va="bottom", ha="left",
    )

    handles = [Patch(facecolor=RAMP[s - 1], edgecolor="white", label=f"$s_t={s}$") for s in (4, 3, 2, 1)]
    handles.append(Patch(facecolor=COLLAPSE, edgecolor="white", label="$s_t=0$ collapse"))
    ax.legend(
        handles=handles, loc="upper left", bbox_to_anchor=(1.20, 1.02),
        frameon=False, fontsize=6, handlelength=1.1, labelspacing=0.35,
    )

    fig.text(
        0.5, 0.02,
        f"{total} runs  ·  {surviving} still holding at turn 5  ·  "
        f"{n_late_all} of them ({n_late_all / surviving * 100:.0f}%) collapse by turn 25",
        ha="center", fontsize=8,
    )

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.27, top=0.90)
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.04)
    if also_png:
        fig.savefig(out_pdf.replace(".pdf", ".png"), dpi=220, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--png", action="store_true", help="also write a PNG preview")
    parser.add_argument("--out", default=os.path.join(REPO, "writing", "fig0_panelB.pdf"))
    args = parser.parse_args()

    runs, n_incomplete = collect()
    if not runs:
        sys.exit(f"no runs found under {CORPUS}")
    rows, stats = sample_rows(runs, n_incomplete)
    grid = build_grid(rows)
    render(rows, grid, stats, args.out, args.png)

    total, n_early_all, n_late_all, n_held_all = stats
    surviving = total - n_early_all
    print(f"corpus: {total} runs  collapse<=t{HORIZON}={n_early_all}  "
          f"surviving t{HORIZON}={surviving}  late collapse={n_late_all} "
          f"({n_late_all / surviving * 100:.1f}%)  never collapsed={n_held_all}")
    print(f"panel rows: {N_EARLY} early / {N_LATE} late / {N_HELD} held")
    for r in rows:
        seq = "".join(
            str(r["strengths"].get(t)) if r["strengths"].get(t) is not None else "."
            for t in range(1, MAX_TURNS + 1)
        )
        tag = f"t{r['collapsed_at']}" if r["collapsed_at"] else "HELD"
        print(f"  {r['target']:<18} {tag:>5}  {seq}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
