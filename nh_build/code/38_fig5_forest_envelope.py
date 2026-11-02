"""Figure 5 (rebuilt 2026-11-02): ONE forest plot merging the old
Figures 5 and 6. Each panel is a primary hazard; rows are the aligned
catalog headline (52 months) and the US-anchored subset (15 months) on
top, then every included Arm A envelope configuration (23), sorted by
rate ratio, labelled by index, threshold and radius, with the Arm A
baseline configuration (SPEI-1, theta = 1.5, r = 4) highlighted. Log
axis with full ticks; vertical line at 1. Points and intervals are the
papers' frozen stratified rate ratios with whole-year bootstrap
intervals (hazards rate_ratios_by_config.csv; headline rows from
results/phase3_2026-11-02/ratio_results.csv).

Opaque white background, 6.85 in wide, 300-dpi PNG + vector PDF.
Run: python3 code/38_fig5_forest_envelope.py
Outputs: figures/fig_forest_envelope.{png,pdf} (new file; the old
fig_h1_forest / fig_h2_envelope renders are superseded).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WS = Path.home() / "workspace"
NH = WS / "papers-finish" / "cdpe-hazards-natural-hazards"
CFG = WS / "papers-finish" / "cdpe-hazards-aas" / "results" \
    / "rate_ratios_by_config.csv"
HEAD = NH / "results" / "phase3_2026-11-02" / "ratio_results.csv"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.linewidth": 0.8})
HAZARDS = [("tornado_all", "(a) Tornadoes"),
           ("hail_ge1in", "(b) Severe hail (>= 1 in)"),
           ("heatwave_days_per_cell", "(c) Heat-wave days per cell")]
BASELINE = "SPEI-1|thr=1.5|r=4.0"


def cfg_label(cfg: str) -> str:
    idx, thr, r = cfg.split("|")
    return f"{idx}, theta = {float(thr.split('=')[1]):g}, " \
           f"r = {float(r.split('=')[1]):g} deg"


def main() -> None:
    cfg = pd.read_csv(CFG)
    head = pd.read_csv(HEAD)
    fig, axes = plt.subplots(3, 1, figsize=(6.85, 10.6),
                             layout="constrained", sharex=True)
    for ax, (haz, title) in zip(axes, HAZARDS):
        rows = []  # (label, rr, lo, hi, kind)
        for arm, lab in (("a_same52", "Aligned catalog (52 months)"),
                         ("b_same15", "US-anchored subset (15 months)")):
            h = head[(head["arm"] == arm) & (head["hazard"] == haz)]
            assert len(h) == 1
            h = h.iloc[0]
            rows.append((lab, h["rr"], h["ci_lo"], h["ci_hi"], "headline"))
        sub = cfg[(cfg["hazard"] == haz) & (cfg["included_in_envelope"])]
        assert len(sub) == 23, (haz, len(sub))
        sub = sub.sort_values("rr")
        for _, r in sub.iterrows():
            kind = "baseline" if r["config"] == BASELINE else "config"
            rows.append((cfg_label(r["config"]), r["rr"], r["ci_lo"],
                         r["ci_hi"], kind))
        rows = rows[::-1]  # headline on top after flip
        y = np.arange(len(rows))
        for yi, (lab, rr, lo, hi, kind) in zip(y, rows):
            if kind == "headline":
                color, ms, fw = "#d55e00", 7, "bold"
                ax.plot([lo, hi], [yi, yi], color=color, lw=1.6, zorder=4)
                ax.plot(rr, yi, marker="D", color=color, ms=6, zorder=5)
            elif kind == "baseline":
                color, ms, fw = "#0072b2", 6, "bold"
                ax.plot([lo, hi], [yi, yi], color=color, lw=1.4, zorder=4)
                ax.plot(rr, yi, marker="o", color=color, ms=5.5, zorder=5)
            else:
                color, ms, fw = "0.35", 5, "normal"
                ax.plot([lo, hi], [yi, yi], color="0.55", lw=1.0, zorder=3)
                ax.plot(rr, yi, marker="o", color=color, ms=4.5, zorder=4)
            ax.text(0.995, yi, f"{rr:.2f} ({lo:.2f} to {hi:.2f})",
                    transform=ax.get_yaxis_transform(),
                    va="center", ha="right", fontsize=7.6, color="0.15",
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.88, pad=0.6), zorder=6)
        ax.axhline(len(rows) - 2.5, color="0.75", lw=0.8)
        ax.axvline(1.0, color="0.25", lw=0.9, ls="--")
        ax.set_yticks(y, [r[0] for r in rows], fontsize=8)
        for tick, (_, _, _, _, kind) in zip(ax.get_yticklabels(), rows):
            if kind in ("headline", "baseline"):
                tick.set_fontweight("bold")
        ax.set_title(title, fontsize=10.5, loc="left")
        ax.set_xscale("log")
        ax.set_xlim(0.3, 5.4)
        ax.set_xticks([0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0])
        ax.get_xaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(
                lambda v, _: f"{v:g}"))
        ax.get_xaxis().set_minor_formatter(
            matplotlib.ticker.NullFormatter())
        ax.grid(axis="x", color="0.9", lw=0.6, zorder=0)
    axes[2].set_xlabel("Rate ratio, CDPE months vs calendar-matched "
                       "non-CDPE months (log scale)")
    fig.suptitle("Hazard rate ratios: headline catalogs and the Arm A "
                 "definition envelope", fontsize=11)
    for ext in ("png", "pdf"):
        kw = dict(facecolor="white")
        if ext == "png":
            kw["dpi"] = 300
        fig.savefig(NH / "figures" / f"fig_forest_envelope.{ext}", **kw)
    from PIL import Image
    p = NH / "figures" / "fig_forest_envelope.png"
    im = Image.open(p)
    if im.mode != "RGB":
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
        bg.save(p)
    print("saved figures/fig_forest_envelope.png/.pdf")


if __name__ == "__main__":
    main()
