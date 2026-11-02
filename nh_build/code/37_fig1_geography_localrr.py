"""Figure 1 (rebuilt 2026-11-02): report geography + calendar-matched
local rate ratio. Panel (a) is unchanged in construction: tornado and
severe-hail (>= 1 in) reports per 1-degree cell, 1980 to 2023, log
scale. Panel (b) REPLACES the old CDPE-month share map (which was not
calendar-matched and read as a regional effect): for each cell, the
ratio of the report rate in the 52 aligned CDPE months to the rate in
calendar-matched non-CDPE months, computed as a standardized ratio:
RR = C1 / E, E = sum over strata s of C0_s * (n1_s / n0_s), where the
strata are calendar month x era (1980-1995 / 1996-2023). The era
stratification is essential: CDPE months skew early (46% in the first
era) while reporting grew across the record, so calendar matching
alone biases local ratios downward where reporting grew fastest. C1
is the cell's reports in CDPE months; C0_s its reports in non-CDPE
months of stratum s; n1_s / n0_s the numbers of CDPE / non-CDPE months
in s. The interval is the Poisson (SMR) interval log RR +/- 1.96 /
sqrt(C1); cells whose interval excludes 1 and with C1 >= 10 are
stippled. Cells with at least 25 total reports are shown; cells with
reports but no CDPE-month reports are grey.

Inputs: results/phase3_2026-11-02/monthly_cell_counts.csv (per-cell
monthly counts rebuilt from raw Storm Events, totals asserted:
54,607 tornadoes, 229,650 hail >= 1 in) and
results/alignment_2026-11-02/aligned_month_sets.csv.
Opaque white background, 6.85 in wide, 300-dpi PNG + vector PDF.
Run: python3 code/37_fig1_geography_localrr.py
Outputs: figures/fig_map_geography.{png,pdf} (replaces the old files).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

WS = Path.home() / "workspace"
NH = WS / "papers-finish" / "cdpe-hazards-natural-hazards"
sys.path.insert(0, str(WS / "papers-finish" / "cdpe_sensitivity" / "scripts"))
from build_rebuild_maps import draw_na_land  # noqa: E402

CELLS = NH / "results" / "phase3_2026-11-02" / "monthly_cell_counts.csv"
ALIGNED = NH / "results" / "alignment_2026-11-02" / "aligned_month_sets.csv"


def main() -> None:
    c = pd.read_csv(CELLS)
    c["reports"] = c["tornado"] + c["hail_ge1in"]
    assert int(c["tornado"].sum()) == 54607
    assert int(c["hail_ge1in"].sum()) == 229650
    al = pd.read_csv(ALIGNED)
    cdpe = set(al.loc[al["in_companion_v211"], "month"])
    assert len(cdpe) == 52
    c["is_cdpe"] = c["month"].isin(cdpe)
    c["cal"] = c["month"].str[5:7].astype(int)

    # strata: calendar month x era (era boundary = the paper's split)
    c["era"] = (c["month"].str[:4].astype(int) > 1995).astype(int)
    all_months = [f"{y}-{m:02d}" for y in range(1980, 2024)
                  for m in range(1, 13)]
    import collections
    n1 = collections.Counter()
    n0 = collections.Counter()
    for mstr in all_months:
        key = (int(mstr[5:7]), int(int(mstr[:4]) > 1995))
        if mstr in cdpe:
            n1[key] += 1
        else:
            n0[key] += 1

    tot = c.groupby(["clat", "clon"])["reports"].sum().rename("total")
    c1 = (c[c["is_cdpe"]].groupby(["clat", "clon"])["reports"].sum()
          .rename("c1"))
    # expected counts under control rates, calendar-standardized
    ctrl = c[~c["is_cdpe"]].copy()
    ctrl["w"] = [n1[(m, e)] / n0[(m, e)]
                 for m, e in zip(ctrl["cal"], ctrl["era"])]
    ctrl["exp_contrib"] = ctrl["reports"] * ctrl["w"]
    expc = ctrl.groupby(["clat", "clon"])["exp_contrib"].sum().rename("exp")
    df = pd.concat([tot, c1, expc], axis=1).fillna(
        {"c1": 0, "exp": 0}).reset_index()
    df = df[df["total"] >= 25].copy()
    df["rr"] = np.where((df["c1"] > 0) & (df["exp"] > 0),
                        df["c1"] / df["exp"], np.nan)
    se = np.where(df["c1"] > 0, 1.96 / np.sqrt(df["c1"]), np.nan)
    df["lo"] = df["rr"] * np.exp(-se)
    df["hi"] = df["rr"] * np.exp(se)
    df["sig"] = ((df["lo"] > 1) | (df["hi"] < 1)) & (df["c1"] >= 10)
    print(f"cells shown: {len(df)}; stippled (interval excludes 1): "
          f"{int(df['sig'].sum())} "
          f"(above 1: {int((df['lo'] > 1).sum())}, "
          f"below 1: {int((df['hi'] < 1).sum())}); "
          f"cells with no CDPE-month reports: "
          f"{int((df['c1'] == 0).sum())}")

    # grids for pcolormesh (cell centres are integer degrees in the file)
    def grid(frame, value):
        piv = frame.pivot_table(index="clat", columns="clon",
                                values=value, aggfunc="first")
        lats = piv.index.values.astype(float)
        lons = piv.columns.values.astype(float)
        xe = np.concatenate([[lons[0] - 0.5], (lons[:-1] + lons[1:]) / 2,
                             [lons[-1] + 0.5]])
        ye = np.concatenate([[lats[0] - 0.5], (lats[:-1] + lats[1:]) / 2,
                             [lats[-1] + 0.5]])
        return xe, ye, piv.values

    tot_all = c.groupby(["clat", "clon"])["reports"].sum().rename("v")
    tot_all = tot_all[tot_all > 0].reset_index()
    print("density cells (all period, >0):", len(tot_all))

    fig, axes = plt.subplots(1, 2, figsize=(6.85, 3.6))
    # (a) density
    ax = axes[0]
    draw_na_land(ax)
    xe, ye, v = grid(tot_all, "v")
    im = ax.pcolormesh(xe, ye, np.ma.masked_invalid(v), cmap="viridis",
                       norm=matplotlib.colors.LogNorm(vmin=1,
                                                      vmax=np.nanmax(v)),
                       shading="flat", zorder=4)
    cb = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cb.set_label("Reports per 1-degree cell")
    ax.set_title("(a) Tornado and severe-hail reports,\n1980 to 2023",
                 fontsize=10)
    ax.set_xlabel("Longitude (degrees)")
    ax.set_ylabel("Latitude (degrees)")
    ax.set_xlim(-125.6, -65.4)
    ax.set_ylim(23.9, 50.9)
    # (b) local rate ratio
    ax = axes[1]
    draw_na_land(ax)
    xe, ye, v = grid(df, "rr")
    norm = TwoSlopeNorm(vmin=0.4, vcenter=1.0, vmax=2.5)
    im = ax.pcolormesh(xe, ye, np.ma.masked_invalid(v), cmap="RdBu_r",
                       norm=norm, shading="flat", zorder=4)
    grey = df[df["c1"] == 0]
    ax.scatter(grey["clon"], grey["clat"], s=14, marker="s",
               color="0.75", linewidths=0, zorder=5)
    sig = df[df["sig"]]
    ax.scatter(sig["clon"], sig["clat"], s=9, marker=".", color="black",
               linewidths=0, zorder=6)
    cb = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02,
                      ticks=[0.5, 0.75, 1.0, 1.5, 2.0, 2.5])
    cb.set_label("Local rate ratio, CDPE vs matched months")
    ax.set_title("(b) Calendar- and era-matched local rate ratio\n"
                 "(dots: interval excludes 1)", fontsize=10)
    ax.set_xlabel("Longitude (degrees)")
    ax.set_ylabel("")
    ax.set_yticklabels([])
    ax.set_xlim(-125.6, -65.4)
    ax.set_ylim(23.9, 50.9)
    fig.suptitle("Where the reports are, and where CDPE months carry "
                 "more of them", fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    for ext in ("png", "pdf"):
        kw = dict(facecolor="white")
        if ext == "png":
            kw["dpi"] = 300
        fig.savefig(NH / "figures" / f"fig_map_geography.{ext}", **kw)
    from PIL import Image
    p = NH / "figures" / "fig_map_geography.png"
    im2 = Image.open(p)
    if im2.mode != "RGB":
        bg = Image.new("RGB", im2.size, "white")
        bg.paste(im2, mask=im2.split()[-1] if im2.mode == "RGBA" else None)
        bg.save(p)
    print("saved figures/fig_map_geography.png/.pdf")


if __name__ == "__main__":
    main()
