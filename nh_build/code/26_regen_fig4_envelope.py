#!/usr/bin/env python3
"""Step 26 - Regenerate the envelope figure (fig_h2_envelope) with the
title and legend separated.

Review fix round, 2026-11-01. Same data, panels, colours and baseline
marking as fig_envelope in the sibling hazards package
(cdpe-hazards-aas/code/07_figures.py), drawn from its results
(rate_ratios_by_config.csv, rate_ratios_summary.json). In the original,
the figure legend (bbox (0.5, 1.02)) and the left-aligned suptitle sat
at the same height under bbox_inches="tight" and collided. Here the
layout is explicit instead: the single shared legend is centred above
the panels and the suptitle above it, so title, legend and panels are
clearly separated. Saved without bbox_inches="tight" so the layout is
exactly as specified.

Rebuild 2026-11-02: the lightning (GLM) arm was dropped from the paper
on the author's direction. The results of record in the sibling package
are now the no-lightning conditioning outputs, and this figure carries
the three retained primary hazards in a single row of three panels
(the GLM panel is removed). Layout constants follow the same explicit
scheme: panels occupy the figure up to y = 0.76, the shared legend is
centred at y = 0.90, and the suptitle sits at y = 0.985.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PKG = Path(__file__).resolve().parents[1]
RES = PKG.parent / "cdpe-hazards-aas" / "results"
OUT = PKG / "figures" / "fig_h2_envelope"
OKABE = {"blue": "#0072B2", "vermillion": "#D55E00"}
LABELS = {"tornado_all": "Tornadoes (all reports)",
          "hail_ge1in": "Hail ≥ 1.00 in",
          "heatwave_days_per_cell": "Heat-wave days per cell"}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5,
                     "axes.linewidth": 0.8})


def main() -> int:
    summary = json.loads((RES / "rate_ratios_summary.json").read_text())
    by_cfg = pd.read_csv(RES / "rate_ratios_by_config.csv")
    prim = ["tornado_all", "hail_ge1in", "heatwave_days_per_cell"]
    fig, axes = plt.subplots(1, 3, figsize=(6.4, 3.4), sharex=True)
    for ax, key, lab in zip(axes.ravel(), prim, "abc"):
        sub = by_cfg[(by_cfg["hazard"] == key)
                     & (by_cfg["included_in_envelope"])
                     & (by_cfg["rr"].notna())].sort_values("rr")
        ax.plot(sub["rr"], np.arange(len(sub)), "o", ms=3.5,
                color=OKABE["blue"])
        b = summary[key]["baseline"]
        rank = int(np.sum(sub["rr"].values < b["rr"]))
        ax.plot([b["rr"]], [rank], "o", ms=6,
                color=OKABE["vermillion"], zorder=5)
        ax.axvline(1.0, color="k", linewidth=0.8, linestyle="--")
        ax.axvline(b["rr"], color=OKABE["vermillion"], linewidth=1.0,
                   label="Baseline configuration")
        ax.set_title(f"({lab}) {LABELS[key]}", loc="left", fontsize=9)
        ax.set_ylabel("Configuration (sorted)")
        ax.grid(alpha=0.25)
    for ax in axes.ravel():
        ax.set_xlabel("Rate ratio (log scale)", fontsize=10)
        ax.set_xscale("log")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.subplots_adjust(left=0.075, right=0.985, top=0.76, bottom=0.17,
                        wspace=0.24)
    fig.legend(handles, labels, loc="upper center",
               bbox_to_anchor=(0.5, 0.90), frameon=False, fontsize=9.5)
    fig.suptitle("Rate ratios across the configuration envelope",
                 x=0.02, ha="left", y=0.985, fontsize=11)
    fig.savefig(OUT.with_suffix(".png"), dpi=300)
    fig.savefig(OUT.with_suffix(".pdf"))
    plt.close(fig)
    print("wrote", OUT.with_suffix(".png"), "and .pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
