"""Figure 2 (rebuilt 2026-11-02): pole locations of the 52 aligned-catalog
CDPE months (companion Study-1 catalogue, SPEIbase v2.11, SPEI-1,
theta = 1.5, r = 4 deg), one dot per pole-month coloured by season.

Design per the adopted figures review: no colourbar, no cell shading
(the old double encoding is dropped); the area outside the CONUS is
shaded; the share of poles outside the CONUS is printed on each panel;
one shared legend above the panels. Opaque white background, 6.85 in
wide (Springer full width), 300-dpi PNG + vector PDF.

Inputs: results/alignment_2026-11-02/pole_classification.csv (rows
set == companion_v211); Natural Earth admin-1 via the na_basemap code in
cdpe_sensitivity/scripts/build_rebuild_maps.py.
Run: python3 code/33_fig2_poles_aligned.py
Outputs: figures/fig_map_poles.{png,pdf} (replaces the old Figure 2 files).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WS = Path.home() / "workspace"
NH = WS / "papers-finish" / "cdpe-hazards-natural-hazards"
SENS_SCRIPTS = WS / "papers-finish" / "cdpe_sensitivity" / "scripts"
sys.path.insert(0, str(SENS_SCRIPTS))
sys.path.insert(0, str(WS / "papers-finish" / "cdpe_sensitivity"))
from build_rebuild_maps import na_basemap  # noqa: E402

POLES = NH / "results" / "alignment_2026-11-02" / "pole_classification.csv"
SEASONS = ["DJF", "MAM", "JJA", "SON"]
SEASON_COLORS = {"DJF": "#0072B2", "MAM": "#009E73",
                 "JJA": "#E69F00", "SON": "#CC79A7"}


def season_of(month_str: str) -> str:
    m = int(month_str[5:7])
    return "DJF" if m in (12, 1, 2) else "MAM" if m in (3, 4, 5) \
        else "JJA" if m in (6, 7, 8) else "SON"


def main() -> None:
    df = pd.read_csv(POLES)
    df = df[df["set"] == "companion_v211"].copy()
    assert len(df) == 52, len(df)
    df["season"] = [season_of(m) for m in df["month"]]

    units, countries = na_basemap()
    fig, axes = plt.subplots(1, 2, figsize=(6.85, 4.3))
    handles = {}
    for ax, pole, title in ((axes[0], "dry", "(a) Dry poles"),
                            (axes[1], "wet", "(b) Wet poles")):
        # Shade the area outside the CONUS: ocean and non-US land in grey,
        # CONUS land white, so the unshaded region is the United States.
        ax.set_facecolor("#c9c9c9")
        countries.plot(ax=ax, facecolor="#bdbdbd", edgecolor="none",
                       zorder=1)
        countries.loc[["United States of America"]].plot(
            ax=ax, facecolor="white", edgecolor="none", zorder=2)
        units.boundary.plot(ax=ax, color="0.55", linewidth=0.28, zorder=3)
        countries.boundary.plot(ax=ax, color="0.25", linewidth=0.55,
                                zorder=3)
        ax.set_aspect(1 / np.cos(np.radians(37)))
        sub = df
        for s in SEASONS:
            ss = sub[sub["season"] == s]
            h = ax.scatter(ss[f"{pole}_lon"], ss[f"{pole}_lat"], s=30,
                           c=SEASON_COLORS[s], edgecolors="black",
                           linewidths=0.5, zorder=6, label=s)
            handles[s] = h
        outside = float((df[f"{pole}_region"] != "CONUS").mean())
        ax.set_title(title, fontsize=10)
        ax.text(0.97, 0.03, f"{outside:.0%} of {pole} poles fall\noutside the CONUS",
                transform=ax.transAxes, fontsize=8, ha="right", va="bottom",
                bbox=dict(facecolor="white", edgecolor="0.6", alpha=0.92,
                          boxstyle="round,pad=0.3"))
        ax.set_xlabel("Longitude (degrees)")
        ax.set_xlim(-125.6, -65.4)
        ax.set_ylim(23.9, 50.9)
    axes[0].set_ylabel("Latitude (degrees)")
    axes[1].set_ylabel("")
    fig.subplots_adjust(top=0.76, bottom=0.17, left=0.07, right=0.985,
                        wspace=0.14)
    fig.legend([handles[s] for s in SEASONS], SEASONS,
               loc="upper center", ncol=4, frameon=False, fontsize=9,
               bbox_to_anchor=(0.5, 0.90), title="Season of the CDPE month",
               title_fontsize=9)
    fig.suptitle("Pole locations of the 52 CDPE months in the aligned catalog,\n"
                 "Jan 1980 to Dec 2023", fontsize=10.5, y=0.985)
    for ext in ("png", "pdf"):
        kw = dict(facecolor="white")
        if ext == "png":
            kw["dpi"] = 300
        fig.savefig(NH / "figures" / f"fig_map_poles.{ext}", **kw)
    # Springer wants opaque figures: flatten the PNG onto white (RGB).
    from PIL import Image
    p = NH / "figures" / "fig_map_poles.png"
    im = Image.open(p)
    if im.mode != "RGB":
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
        bg.save(p)
        print("flattened PNG to RGB:", bg.size)
    print("saved figures/fig_map_poles.png/.pdf")
    for pole in ("dry", "wet"):
        print(pole, "outside share:",
              float((df[f"{pole}_region"] != "CONUS").mean()))


if __name__ == "__main__":
    main()
