"""Figure 4 (rebuilt 2026-11-02): variance shares of CDPE frequency for
BOTH arms on the log-count scale, from the Phase-2 corrected
decomposition (cdpe_sensitivity/results/run_armB_tiefix_2026-11-02/
decomposition_tiefix.csv): Arm A as archived, Arm B with the seeded
tie-break fix. Main effects get distinct colours; two-way interactions
are grey; higher-order interactions are their own category. Shares are
exact closed shares of a complete balanced enumeration, so no sampling
uncertainty attaches to them (stated in the caption).

Terms shown: every main effect, every two-way interaction with share
>= 0.004, higher-order interactions, and one lumped bar for the
remaining two-way interactions so each panel sums to the full total.
Opaque white background, 6.85 in wide, 300-dpi PNG + vector PDF.
Run: python3 code/36_fig4_variance.py
Outputs: figures/fig_s2_variance.{png,pdf} (replaces the old files).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

WS = Path.home() / "workspace"
NH = WS / "papers-finish" / "cdpe-hazards-natural-hazards"
SRC = (WS / "papers-finish" / "cdpe_sensitivity" / "results"
       / "run_armB_tiefix_2026-11-02" / "decomposition_tiefix.csv")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5,
                     "axes.linewidth": 0.8})
FACTOR_COLORS = {
    "threshold": "#0072B2", "radius_deg": "#E69F00", "index": "#009E73",
    "dataset": "#CC79A7", "timescale": "#56B4E9", "dist": "#D55E00",
    "cal_period": "#7B3294", "water_balance": "#A6761D",
}
LABELS = {"radius_deg": "radius", "dist": "fitting distribution",
          "cal_period": "calibration period",
          "water_balance": "water balance",
          "higher_order": "higher-order interactions"}


def panel_terms(df, arm, version):
    g = df[(df["arm"] == arm) & (df["version"] == version)
           & (df["scale"] == "log1p")]
    rows = []  # (label, share, color)
    lump = 0.0
    for _, r in g.iterrows():
        f, share, order = r["factor"], float(r["share"]), int(r["order"])
        if order == 1:
            rows.append((LABELS.get(f, f), share, FACTOR_COLORS[f]))
        elif f == "higher_order":
            rows.append((LABELS["higher_order"], share, "0.35"))
        elif share >= 0.004:
            lab = " x ".join(LABELS.get(p.strip(), p.strip())
                             for p in f.split(" x "))
            rows.append((lab, share, "0.72"))
        else:
            lump += share
    if lump > 0:
        rows.append(("remaining two-way interactions", lump, "0.85"))
    rows.sort(key=lambda t: t[1])
    return rows


def main() -> None:
    df = pd.read_csv(SRC)
    fig, axes = plt.subplots(2, 1, figsize=(6.85, 5.4),
                             layout="constrained")
    for ax, (arm, version, title) in zip(
            axes,
            [("A", "archived", "(a) Arm A (36 scenarios)"),
             ("B", "tiefix", "(b) Arm B, tie-fixed (720 scenarios)")]):
        rows = panel_terms(df, arm, version)
        labels = [r[0] for r in rows]
        vals = [r[1] for r in rows]
        colors = [r[2] for r in rows]
        ax.barh(range(len(rows)), vals, color=colors,
                edgecolor="0.3", linewidth=0.4)
        ax.set_yticks(range(len(rows)), labels, fontsize=8.5)
        ax.set_title(title, fontsize=10)
        ax.set_xlim(0, 0.92)
        for i, v in enumerate(vals):
            ax.text(v + 0.015, i, f"{v:.3f}" if v < 0.01 else f"{v:.2f}",
                    va="center", fontsize=8.5)
    axes[1].set_xlabel("Share of variance in log(1 + CDPE months)")
    fig.suptitle("What governs CDPE frequency: variance shares on the "
                 "log-count scale", fontsize=10.5)
    for ext in ("png", "pdf"):
        kw = dict(facecolor="white")
        if ext == "png":
            kw["dpi"] = 300
        fig.savefig(NH / "figures" / f"fig_s2_variance.{ext}", **kw)
    from PIL import Image
    p = NH / "figures" / "fig_s2_variance.png"
    im = Image.open(p)
    if im.mode != "RGB":
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
        bg.save(p)
    print("saved figures/fig_s2_variance.png/.pdf")


if __name__ == "__main__":
    main()
