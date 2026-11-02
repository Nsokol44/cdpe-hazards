#!/usr/bin/env python3
"""Step 07 - Hazards-arm figures (Nick's figure standard).

Colourblind-safe Okabe-Ito palette; one shared legend above multi-panel
figures; panel labels; axis units; 300-dpi PNG + vector PDF.
Fig H1: forest plot of baseline rate ratios with bootstrap intervals and
        configuration-envelope bands.
Fig H2: envelope dot strips per primary hazard (one panel each, shared
        legend above).
Fig H3: monthly hazard series with baseline CDPE months shaded (panels,
        shared legend above).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = ROOT / "figures"
OKABE = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73",
         "vermillion": "#D55E00", "purple": "#CC79A7", "sky": "#56B4E9",
         "grey": "#666666"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.linewidth": 0.8})
LABELS = {"tornado_all": "Tornadoes (all reports)",
          "tornado_ef1plus": "Tornadoes (F/EF1+)",
          "tornado_ef2plus": "Tornadoes (F/EF2+)",
          "hail_ge1in": "Hail ≥ 1.00 in",
          "hail_all": "Hail (all reports)",
          "heatwave_days_per_cell": "Heat-wave days per cell",
          "glm_flash_box": "Lightning (GLM sampled flashes, 2018-2023)"}


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def fig_forest(summary, by_cfg):
    order = ["tornado_all", "tornado_ef1plus", "tornado_ef2plus",
             "hail_ge1in", "hail_all", "heatwave_days_per_cell",
             "glm_flash_box"]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ys = np.arange(len(order))[::-1]
    for y, key in zip(ys, order):
        s = summary[key]
        b, env = s["baseline"], s["envelope"]
        if b["rr"] is None:
            continue
        if env["rr_min"] is not None:
            ax.barh(y, env["rr_max"] - env["rr_min"], left=env["rr_min"],
                    height=0.52, color=OKABE["sky"], alpha=0.45,
                    label="Configuration envelope" if y == ys[0] else None)
        ax.errorbar(b["rr"], y,
                    xerr=[[b["rr"] - b["ci_lo"]], [b["ci_hi"] - b["rr"]]],
                    fmt="o", color=OKABE["vermillion"], ecolor=OKABE["grey"],
                    elinewidth=1.2, capsize=3, markersize=5,
                    label="Baseline RR (95% bootstrap CI)" if y == ys[0] else None)
    ax.axvline(1.0, color="k", linewidth=0.9, linestyle="--")
    ax.set_yticks(ys, [LABELS[k] for k in order])
    ax.set_xscale("log")
    ax.set_xlabel("Rate ratio: CDPE months vs calendar-matched non-CDPE months (log scale)")
    ax.set_title("Hazard occurrence in CDPE months: baseline estimates and envelopes",
                 loc="left", fontsize=10, pad=24)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2,
              frameon=False)
    ax.grid(axis="x", alpha=0.25)
    save(fig, "fig_h1_forest")


def fig_envelope(by_cfg, summary):
    prim = ["tornado_all", "hail_ge1in", "heatwave_days_per_cell",
            "glm_flash_box"]
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.2), sharex=True)
    for ax, key, lab in zip(axes.ravel(), prim, "abcd"):
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
        ax.set_title(f"({lab}) {LABELS[key]}", loc="left", fontsize=9.5)
        ax.set_ylabel("Configuration (sorted)")
        ax.grid(alpha=0.25)
    for ax in axes[1]:
        ax.set_xlabel("Rate ratio (log scale)")
    for ax in axes.ravel():
        ax.set_xscale("log")
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center",
               bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.suptitle("Rate ratios across the configuration envelope",
                 x=0.02, ha="left", fontsize=10)
    save(fig, "fig_h2_envelope")


def fig_series(monthly, summary):
    fig, axes = plt.subplots(4, 1, figsize=(7.2, 7.2), sharex=True)
    panels = [("tornado_all", "Reports (count)", "a"),
              ("hail_ge1in", "Reports (count)", "b"),
              ("heatwave_days_per_cell", "Days per cell", "c"),
              ("glm_flash_box", "Flashes (count, sampled)", "d")]
    months = pd.to_datetime(monthly["month"])
    cdpe = monthly["cdpe_baseline"].values.astype(bool)
    for ax, (col, ylab, lab) in zip(axes, panels):
        sub = monthly[monthly[col].notna()]
        m = pd.to_datetime(sub["month"])
        ax.plot(m, sub[col], color=OKABE["blue"], linewidth=0.7)
        labelled = False
        for mm, is_c in zip(months, cdpe):
            if not is_c:
                continue
            if col == "glm_flash_box" and mm < pd.Timestamp("2018-01-01"):
                continue  # lightning panel shades only its own window
            ax.axvspan(mm, mm + pd.Timedelta(days=30),
                       color=OKABE["orange"], alpha=0.35,
                       label="Baseline CDPE month" if not labelled else None)
            labelled = True
        ax.set_ylabel(ylab, fontsize=8.5)
        ax.set_title(f"({lab}) {LABELS[col]}", loc="left", fontsize=9.5)
        ax.grid(alpha=0.25)
    axes[-1].set_xlabel("Month")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center",
               bbox_to_anchor=(0.5, 1.01), frameon=False)
    fig.suptitle("Monthly hazard series and baseline CDPE regime months",
                 x=0.01, ha="left", fontsize=10)
    save(fig, "fig_h3_series")


def main() -> int:
    summary = json.loads((RES / "rate_ratios_summary.json").read_text())
    by_cfg = pd.read_csv(RES / "rate_ratios_by_config.csv")
    monthly = pd.read_csv(RES / "monthly_series_all.csv")
    fig_forest(summary, by_cfg)
    fig_envelope(by_cfg, summary)
    fig_series(monthly, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
