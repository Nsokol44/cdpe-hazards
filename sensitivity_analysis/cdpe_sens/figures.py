"""Publication-style figures for the sensitivity analysis (matplotlib only)."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_variance_decomposition(vd, path, top=12, title=None):
    d = vd.head(top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 0.4 * len(d) + 1.2))
    ax.barh(d["term"], d["share"], color="#3b6e8f")
    ax.set_xlabel("Share of variance in CDPE months")
    ax.set_xlim(0, max(0.05, float(d["share"].max()) * 1.1))
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_count_heatmaps(table, path, metric="months_per_year", x="timescale",
                        y="threshold", facet="dataset", fixed=None):
    """One heatmap per facet level; `fixed` pins the remaining factors."""
    t = table
    for k, v in (fixed or {}).items():
        t = t[t[k] == v]
    levels = list(t[facet].unique())
    fig, axes = plt.subplots(1, len(levels), figsize=(4.2 * len(levels), 3.6), squeeze=False)
    vmax = float(t[metric].max()) if len(t) else 1.0
    for ax, lev in zip(axes[0], levels):
        piv = t[t[facet] == lev].pivot_table(index=y, columns=x, values=metric, aggfunc="mean")
        im = ax.imshow(piv.values, origin="lower", aspect="auto", vmin=0, vmax=vmax,
                       cmap="viridis")
        ax.set_xticks(range(len(piv.columns)), [str(c) for c in piv.columns])
        ax.set_yticks(range(len(piv.index)), [str(c) for c in piv.index])
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title(str(lev))
    fig.colorbar(im, ax=axes.ravel().tolist(), label=metric)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_oat(oat, path):
    d = oat.copy()
    d["label"] = d["factor"] + "=" + d["level"].astype(str)
    d = d.iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 0.28 * len(d) + 1.2))
    ax.barh(d["label"], d["jaccard"], color="#8f5a3b")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Jaccard agreement of CDPE months with baseline")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
