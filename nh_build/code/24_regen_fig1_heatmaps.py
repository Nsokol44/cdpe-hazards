#!/usr/bin/env python3
"""Step 24 - Regenerate Figure 1 (fig_s1_count_heatmaps) publication-ready.

Review fix round, 2026-11-01. The original was drawn by
cdpe_sens.figures.plot_count_heatmaps (sibling project cdpe_sensitivity,
called from scripts/run_two_arms.py) at figsize (16.8, 3.6) for four
panels. Embedded in the manuscript at 6.0 in wide, its axis and colorbar
text rendered at roughly 3.5 pt and the y-axis and colorbar carried the
raw variable names radius_deg and months_per_year.

This script reproduces the same figure from the same results table
(results/run_armA_2026-10-05/scenarios.csv, months_per_year by
threshold and radius, faceted by index, viridis, shared scale 0 to the
table maximum) at document width with publication labels and legible
fonts: "Detection threshold", "Buffer radius (degrees)", colorbar
"CDPE months per year". Data, panel order, colormap and scale are
unchanged. Deterministic: reads a fixed CSV, no randomness.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PKG = Path(__file__).resolve().parents[1]
SRC = (PKG.parent / "cdpe_sensitivity" / "results"
       / "run_armA_2026-10-05" / "scenarios.csv")
OUT = PKG / "figures" / "fig_s1_count_heatmaps"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5,
                     "axes.linewidth": 0.8})


def main() -> int:
    table = pd.read_csv(SRC)
    levels = list(table["index"].unique())
    vmax = float(table["months_per_year"].max())
    fig, axes = plt.subplots(1, len(levels), figsize=(6.8, 2.3),
                             squeeze=False, layout="constrained")
    im = None
    for ax, lev in zip(axes[0], levels):
        piv = table[table["index"] == lev].pivot_table(
            index="radius_deg", columns="threshold",
            values="months_per_year", aggfunc="mean")
        im = ax.imshow(piv.values, origin="lower", aspect="auto",
                       vmin=0, vmax=vmax, cmap="viridis")
        ax.set_xticks(range(len(piv.columns)),
                      [str(c) for c in piv.columns], fontsize=9)
        ax.set_yticks(range(len(piv.index)),
                      [f"{c:g}" for c in piv.index], fontsize=9)
        ax.set_title(str(lev), fontsize=10.5, fontweight="bold")
    axes[0][0].set_ylabel("Buffer radius (degrees)", fontsize=10)
    # One shared x-axis label for the row (per-panel labels overlap at
    # this width, since all four panels share the threshold axis).
    fig.supxlabel("Detection threshold", fontsize=10)
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(),
                        label="CDPE months per year")
    cbar.ax.tick_params(labelsize=9)
    cbar.set_label("CDPE months per year", fontsize=10)
    # Saved without bbox_inches="tight": the constrained layout already
    # reserves room for the shared axis label, and a fixed canvas keeps
    # the label clear of the tick labels.
    fig.savefig(OUT.with_suffix(".png"), dpi=300)
    fig.savefig(OUT.with_suffix(".pdf"))
    plt.close(fig)
    print("wrote", OUT.with_suffix(".png"), "and .pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
