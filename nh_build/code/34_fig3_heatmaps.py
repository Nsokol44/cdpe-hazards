"""Figure 3 (rebuilt 2026-11-02): Arm A CDPE-month counts by detection
threshold and buffer radius, faceted by index, with the count printed in
every cell and the baseline operating point (theta = 1.5, r = 4 deg)
outlined. Counts (not months per year), fixing the caption/colorbar
mismatch the figures review flagged.

Source: cdpe_sensitivity/results/run_armA_2026-10-05/scenarios.csv
(staged SPEIbase v2.10 release; the catalog of record on v2.11 returns 52
months at the outlined SPEI-1 operating point — see the caption).
Opaque white background, 6.85 in wide, 300-dpi PNG + vector PDF.
Run: python3 code/34_fig3_heatmaps.py
Outputs: figures/fig_s1_count_heatmaps.{png,pdf} (replaces the old files).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

WS = Path.home() / "workspace"
NH = WS / "papers-finish" / "cdpe-hazards-natural-hazards"
SRC = (WS / "papers-finish" / "cdpe_sensitivity" / "results"
       / "run_armA_2026-10-05" / "scenarios.csv")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5,
                     "axes.linewidth": 0.8})


def main() -> None:
    table = pd.read_csv(SRC)
    levels = ["SPEI-1", "SPEI-3", "SPEI-6", "SPI-1"]
    vmax = float(table["n_cdpe_months"].max())
    fig, axes = plt.subplots(1, 4, figsize=(6.85, 2.6),
                             layout="constrained")
    im = None
    for ax, lev in zip(axes, levels):
        piv = table[table["index"] == lev].pivot_table(
            index="radius_deg", columns="threshold",
            values="n_cdpe_months", aggfunc="first")
        vals = piv.values.astype(float)
        im = ax.imshow(vals, origin="lower", aspect="auto",
                       vmin=0, vmax=vmax, cmap="viridis")
        ax.set_xticks(range(len(piv.columns)),
                      [f"{c:g}" for c in piv.columns])
        ax.set_yticks(range(len(piv.index)),
                      [f"{i:g}" for i in piv.index])
        ax.set_title(lev, fontsize=10)
        ax.set_xlabel("Detection threshold")
        # print the count in each cell; text colour by luminance
        norm = vals / vmax if vmax > 0 else vals
        for i in range(vals.shape[0]):
            for j in range(vals.shape[1]):
                ax.text(j, i, f"{int(vals[i, j])}", ha="center",
                        va="center", fontsize=8.5,
                        color="white" if norm[i, j] < 0.55 else "black")
        # outline the baseline operating point theta=1.5, r=4
        j = list(piv.columns).index(1.5)
        i = list(piv.index).index(4.0)
        ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                               edgecolor="#d55e00", linewidth=2.2,
                               zorder=5))
    axes[0].set_ylabel("Buffer radius (degrees)")
    for ax in axes[1:]:
        ax.set_yticklabels([])
    cb = fig.colorbar(im, ax=axes, shrink=0.92, pad=0.015)
    cb.set_label("CDPE months, 1980 to 2023")
    fig.suptitle("CDPE months by threshold and radius in Arm A "
                 "(staged release)", fontsize=10.5)
    for ext in ("png", "pdf"):
        kw = dict(facecolor="white")
        if ext == "png":
            kw["dpi"] = 300
        fig.savefig(NH / "figures" / f"fig_s1_count_heatmaps.{ext}", **kw)
    from PIL import Image
    p = NH / "figures" / "fig_s1_count_heatmaps.png"
    im2 = Image.open(p)
    if im2.mode != "RGB":
        bg = Image.new("RGB", im2.size, "white")
        bg.paste(im2, mask=im2.split()[-1] if im2.mode == "RGBA" else None)
        bg.save(p)
    print("saved figures/fig_s1_count_heatmaps.png/.pdf; vmax =", vmax)


if __name__ == "__main__":
    main()
