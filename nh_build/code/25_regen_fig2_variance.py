#!/usr/bin/env python3
"""Step 25 - Regenerate Figure 2 (fig_s2_variance) with publication
labels.

Review fix round, 2026-11-01. Same data, same top-12 terms, same bar
colour, same axis label and limits rule as the sibling regeneration
(cdpe-hazards-aas/code/07b_regen_fig_s2.py), which drew from
cdpe_sensitivity/results/run_armB_masked_2026-10-05/
variance_decomposition.csv. Two changes, both directed by the review:
(1) the raw variable names on the bar axis (dist, higher_order,
radius_deg, water_balance x threshold, and the rest) are replaced with
publication labels; (2) the in-figure title's separator is a colon
where the original used an em dash, per the author's standing rule of
zero em dashes in submitted papers. No data or values change.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PKG = Path(__file__).resolve().parents[1]
SRC = (PKG.parent / "cdpe_sensitivity" / "results"
       / "run_armB_masked_2026-10-05" / "variance_decomposition.csv")
OUT = PKG / "figures" / "fig_s2_variance"
TITLE = "Arm B (land-masked): variance decomposition of CDPE months"

LABELS = {
    "threshold": "Detection threshold",
    "dist": "Fitting distribution",
    "dist x threshold": "Fitting distribution × detection threshold",
    "higher_order": "Higher-order interactions",
    "radius_deg": "Buffer radius",
    "threshold x radius_deg": "Detection threshold × buffer radius",
    "dist x radius_deg": "Fitting distribution × buffer radius",
    "water_balance x threshold": "Water balance × detection threshold",
    "dist x water_balance": "Fitting distribution × water balance",
    "dataset x threshold": "Dataset × detection threshold",
    "dataset": "Dataset",
    "timescale": "Timescale",
}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5,
                     "axes.linewidth": 0.8})


def main() -> int:
    vd = pd.read_csv(SRC)
    d = vd.head(12).iloc[::-1].copy()
    d["label"] = d["term"].map(LABELS)
    assert d["label"].notna().all(), "unmapped term in variance table"
    fig, ax = plt.subplots(figsize=(6.6, 5.6))
    ax.barh(d["label"], d["share"], color="#3b6e8f")
    ax.set_xlabel("Share of variance in CDPE months", fontsize=10.5)
    ax.set_xlim(0, max(0.05, float(d["share"].max()) * 1.1))
    ax.set_title(TITLE, fontsize=11)
    ax.tick_params(axis="y", labelsize=9.5)
    ax.tick_params(axis="x", labelsize=9.5)
    fig.tight_layout()
    fig.savefig(OUT.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT.with_suffix(".png"), "and .pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
