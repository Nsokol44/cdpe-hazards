#!/usr/bin/env python3
"""Step 27 - Map figure (new Figure 1): report geography, 1980-2023.

Panel (a): tornado + severe-hail (>= 1.00 in) reports per 1-degree cell.
Panel (b): the share of each cell's reports that fell in the 46 baseline
CDPE months (cells with >= 25 reports; 8.7% expected under proportionality,
46 of 528 months).

Counting replicates the paper's Step 04 rules exactly (domain box
25-50 N, 125-66 W; county-centroid fallback for records without begin
coordinates, Census gazetteer). Totals are asserted against the paper:
54,607 tornado reports and 229,650 hail reports >= 1.00 in.
Baseline months: SPEI-1, theta = 1.5, r = 4 degrees, read from the
package's own archive (monthsets/cdpe_monthly_series_armA_as_used.csv);
asserted to number 46.

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

PKG = Path(__file__).resolve().parents[1]
SRC = PKG.parent / "cdpe-hazards-aas"
RAW = SRC / "data" / "raw"
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
    with zipfile.ZipFile(PKG / "archive_nh_code.zip") as z:
        with z.open("monthsets/cdpe_monthly_series_armA_as_used.csv") as f:
            df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"))
    col = "SPEI-1|thr=1.5|r=4.0"
    months = {f"{str(d)[:4]}-{str(d)[5:7]}" for d, v in
              zip(df["date"], df[col]) if int(v) == 1}
    assert len(months) == 46, f"baseline months: {len(months)}"
    return months


def main():
    centroids = load_centroids()
    cdpe = baseline_months()
    files = sorted((RAW / "storm_events").glob("StormEvents_details-*.csv.gz"))
    assert len(files) == 44
    recs = []
    n_tor = n_hail_ge = n_hail_all = 0
    for path in files:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
            df = pd.read_csv(fh, usecols=USECOLS, low_memory=False)
        df = df[df["EVENT_TYPE"].isin(["Tornado", "Hail"])]
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
    assert n_tor == 54607, n_tor
    assert n_hail_ge == 229650, n_hail_ge
    assert n_hail_all == 379430, n_hail_all
    print(f"totals OK: tornado {n_tor}, hail>=1in {n_hail_ge}, hail all {n_hail_all}")

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

    states = json.loads((PKG / "code" / "us_states_simplified.geojson")
                        .read_text())

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

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.3))
    m0 = axes[0].pcolormesh(lons, lats, np.ma.masked_invalid(A),
                            cmap="viridis", norm=LogNorm(vmin=1, vmax=A[~np.isnan(A)].max()),
                            shading="auto", zorder=2)
    axes[0].set_title("(a) Reports per 1-degree cell")
    cb0 = fig.colorbar(m0, ax=axes[0], shrink=0.92, pad=0.02)
    cb0.set_label("Reports per cell")
    share_max = np.nanpercentile(B, 99)
    norm = TwoSlopeNorm(vmin=0.0, vcenter=100.0 * 46 / 528, vmax=max(share_max, 12.0))
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
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(PKG / "figures" / f"fig_map_geography.{ext}", dpi=300)
    print("wrote figures/fig_map_geography.png/.pdf")
    print(f"cells total {np.sum(~np.isnan(A))}, share cells {np.sum(~np.isnan(B))}, "
          f"share median {np.nanmedian(B):.1f}%")


if __name__ == "__main__":
    raise SystemExit(main())
