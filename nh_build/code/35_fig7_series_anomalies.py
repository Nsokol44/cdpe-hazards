"""Figure 6 (rebuilt 2026-11-02; was Figure 7): monthly hazard series as
anomalies from the calendar-month mean, 1980 to 2023, with the 52 aligned
CDPE months shaded. Anomalies replace the raw series (whose hail panel
is dominated by the 1996-98 reporting step) per the figures review; the
step and the April-May 2011 outbreak cluster are annotated.

Series of record: monthly_series_all.csv (asserted totals: 54,607
tornadoes; 229,650 hail >= 1 in; 379,430 hail overall). CDPE shading from
results/alignment_2026-11-02/aligned_month_sets.csv (companion set).
Opaque white background, 6.85 in wide, 300-dpi PNG + vector PDF.
Run: python3 code/35_fig7_series_anomalies.py
Outputs: figures/fig_h3_series.{png,pdf} (replaces the old files).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WS = Path.home() / "workspace"
NH = WS / "papers-finish" / "cdpe-hazards-natural-hazards"
SERIES = WS / "papers-finish" / "cdpe-hazards-aas" / "results" \
    / "monthly_series_all.csv"
ALIGNED = NH / "results" / "alignment_2026-11-02" / "aligned_month_sets.csv"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5,
                     "axes.linewidth": 0.8})
SHADE = "#0072b2"


def main() -> None:
    s = pd.read_csv(SERIES, parse_dates=["month"])
    assert len(s) == 528
    assert int(s["tornado_all"].sum()) == 54607
    assert int(s["hail_ge1in"].sum()) == 229650
    assert int(s["hail_all"].sum()) == 379430
    al = pd.read_csv(ALIGNED)
    cdpe = sorted(al.loc[al["in_companion_v211"], "month"])
    assert len(cdpe) == 52
    cdpe_dates = pd.to_datetime([m + "-01" for m in cdpe])

    panels = [
        ("tornado_all", "(a) Tornado reports, monthly anomaly", "Reports"),
        ("hail_ge1in", "(b) Severe-hail reports (>= 1 in), monthly anomaly",
         "Reports"),
        ("heatwave_days_per_cell",
         "(c) Heat-wave days per cell, monthly anomaly", "Days per cell"),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(6.85, 4.9), sharex=True,
                             layout="constrained")
    for ax, (col, title, ylab) in zip(axes, panels):
        clim = s.groupby("cal")[col].transform("mean")
        anom = s[col] - clim
        ax.plot(s["month"], anom, color="0.25", linewidth=0.7)
        ax.axhline(0, color="0.55", linewidth=0.7)
        for d in cdpe_dates:
            ax.axvspan(d, d + pd.DateOffset(months=1), color=SHADE,
                       alpha=0.16, linewidth=0)
        ax.set_title(title, fontsize=10, loc="left")
        ax.set_ylabel(ylab)
    axes[0].annotate("April-May 2011\noutbreak cluster",
                     xy=(pd.Timestamp("2011-04-01"), 240),
                     xytext=(pd.Timestamp("2002-06-01"), 300),
                     fontsize=8.5,
                     arrowprops=dict(arrowstyle="->", lw=0.8))
    axes[1].annotate("reporting step,\n1996 to 1998",
                     xy=(pd.Timestamp("1997-01-01"), 320),
                     xytext=(pd.Timestamp("1984-06-01"), 430),
                     fontsize=8.5,
                     arrowprops=dict(arrowstyle="->", lw=0.8))
    axes[2].set_xlabel("Month")
    fig.suptitle("Monthly hazard anomalies with the 52 aligned CDPE "
                 "months shaded", fontsize=10.5)
    for ext in ("png", "pdf"):
        kw = dict(facecolor="white")
        if ext == "png":
            kw["dpi"] = 300
        fig.savefig(NH / "figures" / f"fig_h3_series.{ext}", **kw)
    from PIL import Image
    p = NH / "figures" / "fig_h3_series.png"
    im = Image.open(p)
    if im.mode != "RGB":
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
        bg.save(p)
    print("saved figures/fig_h3_series.png/.pdf")


if __name__ == "__main__":
    main()
