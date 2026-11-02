#!/usr/bin/env python3
"""Coverage map for the nClimGrid SPEI aggregated grid (Step-2 deliverable).

Shows which 0.5-degree Arm A cells carry valid nClimGrid SPEI coverage
(CONUS land mask of the product) at 2020-01 - the mask is static across
the record (3,575 of 5,900 domain cells), against the SPEIbase grid's
4,399 valid cells over the same box. State outlines from the hazards
project's geojson, house style of the package map figures (300-dpi PNG
+ vector PDF). Deterministic; inputs read-only.

Usage: build_coverage_map.py <output_dir>
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

HERE = Path(__file__).resolve().parents[1]
AGG = HERE / "data_nclimgrid" / "agg05" / "spei01_nclimgrid_gamma_05deg.nc"
STATES = (HERE.parent / "cdpe-hazards-natural-hazards" / "code"
          / "us_states_simplified.geojson")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7,
})


def main():
    outdir = Path(sys.argv[1])
    outdir.mkdir(parents=True, exist_ok=True)
    with xr.open_dataset(AGG) as ds:
        times = [str(t)[:7] for t in ds["time"].values]
        i = times.index("2020-01")
        field = np.asarray(ds["spei"].isel(time=i).values, dtype=float)
        lat = np.asarray(ds["lat"].values, dtype=float)
        lon = np.asarray(ds["lon"].values, dtype=float)
    covered = np.isfinite(field)
    n_cov = int(covered.sum())
    assert n_cov == 3575, n_cov
    lat_e = np.concatenate([[lat[0] - 0.25], (lat[:-1] + lat[1:]) / 2,
                            [lat[-1] + 0.25]])
    lon_e = np.concatenate([[lon[0] - 0.25], (lon[:-1] + lon[1:]) / 2,
                            [lon[-1] + 0.25]])
    states = json.loads(STATES.read_text())

    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.pcolormesh(lon_e, lat_e, np.ma.masked_where(~covered, covered),
                  cmap="viridis", vmin=0, vmax=1.4, shading="auto", zorder=1)
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
    ax.set_xlim(-125, -66)
    ax.set_ylim(24, 50)
    ax.set_aspect(1 / np.cos(np.radians(37)))
    ax.set_xlabel("Longitude (degrees)")
    ax.set_ylabel("Latitude (degrees)")
    ax.set_title("nClimGrid SPEI coverage on the Arm A 0.5-degree grid: "
                 f"{n_cov} of 5,900 cells covered\n"
                 "(SPEIbase grid: 4,399 cells; mask static across the record)")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(outdir / f"coverage_map.{ext}", dpi=300)
    print(f"wrote coverage_map.png/.pdf to {outdir} (covered cells {n_cov})")


if __name__ == "__main__":
    raise SystemExit(main())
