#!/usr/bin/env python3
"""Step 07b - Regenerate Figure 2 (fig_s2_variance) with the title inside
the frame.

Figure 2 was carried into this package from the companion sensitivity
package (papers-finish/cdpe_sensitivity), where
cdpe_sens.figures.plot_variance_decomposition drew it from
results/run_armB_masked_2026-10-05/variance_decomposition.csv under the
title "Arm B (land-masked) - variance decomposition of CDPE months"
(the title separator is an em dash in the original). That function saved
without bbox_inches="tight", so the centred title, wider than the axes,
was clipped at the right edge of the PNG ("...of CDPE month").

This script reproduces the original plot exactly (same data, same
top-12 terms, same bar colour, same axis label and limits rule, same
title text) with one layout-only change: the figure is saved with
bbox_inches="tight", so the canvas expands to contain the full title.
No data, panel, or value changes.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT.parent / "cdpe_sensitivity" / "results"
       / "run_armB_masked_2026-10-05" / "variance_decomposition.csv")
OUT = ROOT / "figures" / "fig_s2_variance.png"
TITLE = "Arm B (land-masked) \u2014 variance decomposition of CDPE months"


def main() -> int:
    vd = pd.read_csv(SRC)
    d = vd.head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 0.4 * len(d) + 1.2))
    ax.barh(d["term"], d["share"], color="#3b6e8f")
    ax.set_xlabel("Share of variance in CDPE months")
    ax.set_xlim(0, max(0.05, float(d["share"].max()) * 1.1))
    ax.set_title(TITLE)
    fig.tight_layout()
    fig.savefig(OUT, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
