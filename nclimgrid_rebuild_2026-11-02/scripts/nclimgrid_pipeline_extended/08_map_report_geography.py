#!/usr/bin/env python3
"""Map figure (run-stage deliverable) - report geography, EXTENDED window.

Adapted from the Natural Hazards package's code/27_build_map_figure.py
(same panel logic, captions, colourblind-safe palette, typography, state
outlines, 300-dpi PNG + vector PDF), with these documented changes for the
nClimGrid rerun at the extended window (Jan 1980 - Jul 2026, 559 months):

- Inputs are this project's Storm Events files (47 yearly files,
  1980-2026) under the frozen Step-04 counting rules (domain box
  25-50 N, 125-66 W; county-centroid fallback via the Census gazetteer).
- Panel (b)'s CDPE months are the NEW extended baseline (SPEI-1,
  thr = 1.5, r = 4.0 deg) from the nClimGrid detection run
  results/run_armA_nclimgrid_ext_2026-11-01; the count is read from that
  run's scenarios.csv, not hard-coded.
- Totals are asserted against this project's Step-04 output
  (results/hazard_series_storm.csv column sums) - an independent path
  over the same files and rules.
- Panel (b)'s diverging norm is centred on the proportional expectation
  100 * n_baseline / 559 percent.

Deterministic; no randomness. Inputs are read, never modified.
"""
import gzip
import io
import json
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm, TwoSlopeNorm

PROJ = Path(__file__).resolve().parents[1]
RAW = PROJ / "data" / "raw"
SENS = PROJ.parent.parent / "cdpe_sensitivity"
RUN = SENS / "results" / "run_armA_nclimgrid_ext_2026-11-01"
STATES = (PROJ.parent.parent / "cdpe-hazards-natural-hazards" / "code"
          / "us_states_simplified.geojson")
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 25.0, 50.0, -125.0, -66.0
USECOLS = ["BEGIN_YEARMONTH", "EVENT_TYPE", "TOR_F_SCALE", "MAGNITUDE",
           "BEGIN_LAT", "BEGIN_LON", "STATE_FIPS", "CZ_FIPS"]
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7,
})


def load_centroids():
    zpath = RAW / "reference" / "gaz_counties_national.zip"
    with zipfile.ZipFile(zpath) as z:
        name = [n for n in z.namelist() if n.endswith(".txt")][0]
        with z.open(name) as f:
            df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"),
                             sep="\t", dtype={"GEOID": str})
    df.columns = [c.strip() for c in df.columns]
    return {int(g): (float(la), float(lo)) for g, la, lo in
            zip(df["GEOID"], df["INTPTLAT"], df["INTPTLONG"])}


def baseline_months():
    scen = pd.read_csv(RUN / "scenarios.csv")
    base = scen[(scen["index"] == "SPEI-1")
                & (scen["threshold"] == 1.5) & (scen["radius_deg"] == 4.0)]
    assert len(base) == 1
    n_base = int(base["n_cdpe_months"].iloc[0])
    df = pd.read_csv(RUN / "cdpe_monthly_series.csv")
    col = "SPEI-1|thr=1.5|r=4.0"
    months = {str(d)[:7] for d, v in zip(df["date"], df[col]) if int(v) == 1}
    assert len(months) == n_base, (len(months), n_base)
    return months, n_base


def main():
    centroids = load_centroids()
    cdpe, n_base = baseline_months()
    series = pd.read_csv(PROJ / "results" / "hazard_series_storm.csv")
    exp_tor = int(series["tornado_all"].sum())
    exp_hail_ge = int(series["hail_ge1in"].sum())
    exp_hail_all = int(series["hail_all"].sum())
    files = sorted((RAW / "storm_events").glob("StormEvents_details-*.csv.gz"))
    assert len(files) == 47, len(files)
    recs = []
    n_tor = n_hail_ge = n_hail_all = 0
    for path in files:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
            df = pd.read_csv(fh, usecols=USECOLS, low_memory=False)
        df = df[df["EVENT_TYPE"].isin(["Tornado", "Hail"])]
        df = df[df["BEGIN_YEARMONTH"] <= 202607]
        for r in df.itertuples(index=False):
            ym = str(int(r.BEGIN_YEARMONTH))
            key = f"{ym[:4]}-{ym[4:6]}"
            lat, lon = r.BEGIN_LAT, r.BEGIN_LON
            if not (pd.notna(lat) and pd.notna(lon)):
                fips = None
                if pd.notna(r.STATE_FIPS) and pd.notna(r.CZ_FIPS):
                    fips = int(r.STATE_FIPS) * 1000 + int(r.CZ_FIPS)
                if fips in centroids:
                    lat, lon = centroids[fips]
                else:
                    continue
            if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                continue
            if r.EVENT_TYPE == "Tornado":
                n_tor += 1
                recs.append((lat, lon, key))
            else:
                n_hail_all += 1
                if pd.notna(r.MAGNITUDE) and float(r.MAGNITUDE) >= 1.0:
                    n_hail_ge += 1
                    recs.append((lat, lon, key))
    assert n_tor == exp_tor, (n_tor, exp_tor)
    assert n_hail_ge == exp_hail_ge, (n_hail_ge, exp_hail_ge)
    assert n_hail_all == exp_hail_all, (n_hail_all, exp_hail_all)
    print(f"totals OK vs Step 04: tornado {n_tor}, hail>=1in {n_hail_ge}, "
          f"hail all {n_hail_all}; baseline months {n_base}")

    pts = pd.DataFrame(recs, columns=["lat", "lon", "month"])
    pts["clat"] = np.floor(pts["lat"]).astype(int)
    pts["clon"] = np.floor(pts["lon"]).astype(int)
    pts["cdpe"] = pts["month"].isin(cdpe)
    tot = pts.groupby(["clat", "clon"]).size().rename("total")
    inc = pts[pts["cdpe"]].groupby(["clat", "clon"]).size().rename("incdpe")
    grid = pd.concat([tot, inc], axis=1).fillna(0).reset_index()
    grid["share"] = 100.0 * grid["incdpe"] / grid["total"]

    lats = np.arange(24, 51)
    lons = np.arange(-125, -65)
    A = np.full((len(lats) - 1, len(lons) - 1), np.nan)
    B = np.full_like(A, np.nan)
    for r in grid.itertuples(index=False):
        i, j = r.clat - 24, r.clon + 125
        if 0 <= i < A.shape[0] and 0 <= j < A.shape[1]:
            A[i, j] = r.total
            if r.total >= 25:
                B[i, j] = r.share

    states = json.loads(STATES.read_text())

    def draw_states(ax):
        for feat in states["features"]:
            geom = feat["geometry"]
            polys = (geom["coordinates"] if geom["type"] == "Polygon"
                     else [p for mp in geom["coordinates"] for p in [mp]]
                     if geom["type"] == "MultiPolygon" else [])
            if geom["type"] == "MultiPolygon":
                polys = [ring for poly in geom["coordinates"] for ring in poly]
            for ring in polys:
                xs = [c[0] for c in ring]
                ys = [c[1] for c in ring]
                ax.plot(xs, ys, color="0.35", lw=0.3, zorder=3)

    n_months = 559
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.3))
    m0 = axes[0].pcolormesh(lons, lats, np.ma.masked_invalid(A),
                            cmap="viridis", norm=LogNorm(vmin=1, vmax=A[~np.isnan(A)].max()),
                            shading="auto", zorder=2)
    axes[0].set_title("(a) Reports per 1-degree cell")
    cb0 = fig.colorbar(m0, ax=axes[0], shrink=0.92, pad=0.02)
    cb0.set_label("Reports per cell")
    share_max = np.nanpercentile(B, 99)
    norm = TwoSlopeNorm(vmin=0.0, vcenter=100.0 * n_base / n_months,
                        vmax=max(share_max, 12.0))
    m1 = axes[1].pcolormesh(lons, lats, np.ma.masked_invalid(B),
                            cmap="BrBG", norm=norm, shading="auto", zorder=2)
    axes[1].set_title("(b) Share in CDPE months (%)")
    cb1 = fig.colorbar(m1, ax=axes[1], shrink=0.92, pad=0.02)
    cb1.set_label("Percent of the cell's reports")
    for ax in axes:
        draw_states(ax)
        ax.set_xlim(-125, -66)
        ax.set_ylim(24, 50)
        ax.set_aspect(1 / np.cos(np.radians(37)))
        ax.set_xlabel("Longitude (degrees)")
    axes[0].set_ylabel("Latitude (degrees)")
    axes[1].set_yticklabels([])
    fig.suptitle("Report geography, Jan 1980–Jul 2026 — nClimGrid SPEI "
                 f"baseline ({n_base} CDPE months)", fontsize=9)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(RUN / f"fig_map_geography_extended.{ext}", dpi=300)
    print("wrote fig_map_geography_extended.png/.pdf")
    print(f"cells total {np.sum(~np.isnan(A))}, share cells {np.sum(~np.isnan(B))}, "
          f"share median {np.nanmedian(B):.1f}%")


if __name__ == "__main__":
    raise SystemExit(main())
