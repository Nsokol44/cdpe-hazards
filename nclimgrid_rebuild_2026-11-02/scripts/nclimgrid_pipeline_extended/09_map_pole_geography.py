#!/usr/bin/env python3
"""Map figure (run-stage deliverable) - pole geography, EXTENDED window.

Dry-pole and wet-pole locations for the NEW extended baseline CDPE months
(SPEI-1, thr = 1.5, r = 4.0 deg; nClimGrid SPEI; Jan 1980 - Jul 2026),
from the pole locations saved by the detection run
(results/run_armA_nclimgrid_ext_2026-11-01/baseline_poles.csv).

Rendering choice (documented): two panels sharing the report-geography
figure's design (state outlines, extent, aspect, typography, viridis).
Cell shading = the number of baseline CDPE months whose pole fell in
each 0.5-degree analysis cell; the pole locations themselves are
overlaid as points at their saved coordinates. Panel (a) dry pole,
panel (b) wet pole. 300-dpi PNG + vector PDF.

The count of CDPE months with a finite pole is asserted against the
run's scenarios.csv baseline count. Deterministic; inputs read-only.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJ = Path(__file__).resolve().parents[1]
SENS = PROJ.parent.parent / "cdpe_sensitivity"
RUN = SENS / "results" / "run_armA_nclimgrid_ext_2026-11-01"
STATES = (PROJ.parent.parent / "cdpe-hazards-natural-hazards" / "code"
          / "us_states_simplified.geojson")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7,
})

LAT_C = np.round(np.arange(25.25, 50.0, 0.5), 2)   # 50 centres
LON_C = np.round(np.arange(-125.25, -66.5, 0.5), 2)  # 118 centres
LAT_E = np.arange(25.0, 50.5, 0.5)
LON_E = np.arange(-125.5, -66.0, 0.5)


def cell_counts(lats, lons):
    H, _, _ = np.histogram2d(lats, lons, bins=[LAT_E, LON_E])
    return np.ma.masked_where(H == 0, H)


def main():
    scen = pd.read_csv(RUN / "scenarios.csv")
    base = scen[(scen["index"] == "SPEI-1")
                & (scen["threshold"] == 1.5) & (scen["radius_deg"] == 4.0)]
    n_base = int(base["n_cdpe_months"].iloc[0])
    poles = pd.read_csv(RUN / "baseline_poles.csv")
    cd = poles[poles["is_cdpe"] == 1]
    assert len(cd) == n_base, (len(cd), n_base)
    for c in ("dry_lat", "dry_lon", "wet_lat", "wet_lon"):
        assert cd[c].notna().all(), c
    print(f"baseline CDPE months with poles: {len(cd)}")

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

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.3))
    panels = [(cd["dry_lat"], cd["dry_lon"], "(a) Dry pole"),
              (cd["wet_lat"], cd["wet_lon"], "(b) Wet pole")]
    vmax = max(cell_counts(la, lo).max() for la, lo, _ in panels)
    for ax, (la, lo, title) in zip(axes, panels):
        H = cell_counts(la.values, lo.values)
        m = ax.pcolormesh(LON_E, LAT_E, H, cmap="viridis", vmin=0,
                          vmax=vmax, shading="auto", zorder=1)
        ax.scatter(lo, la, s=16, facecolor="white", edgecolor="0.15",
                   linewidths=0.5, zorder=4)
        ax.set_title(title)
        draw_states(ax)
        ax.set_xlim(-125, -66)
        ax.set_ylim(24, 50)
        ax.set_aspect(1 / np.cos(np.radians(37)))
        ax.set_xlabel("Longitude (degrees)")
        cb = fig.colorbar(m, ax=ax, shrink=0.92, pad=0.02)
        cb.set_label("CDPE months with pole in cell")
    axes[0].set_ylabel("Latitude (degrees)")
    axes[1].set_yticklabels([])
    fig.suptitle("Pole locations, extended baseline CDPE months "
                 f"({n_base} months, Jan 1980–Jul 2026)", fontsize=9)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(RUN / f"fig_map_poles_extended.{ext}", dpi=300)
    print("wrote fig_map_poles_extended.png/.pdf")
    print(f"dry-pole cells used: {(cell_counts(cd['dry_lat'], cd['dry_lon']).count())}, "
          f"wet-pole cells used: {(cell_counts(cd['wet_lat'], cd['wet_lon']).count())}")


if __name__ == "__main__":
    raise SystemExit(main())
