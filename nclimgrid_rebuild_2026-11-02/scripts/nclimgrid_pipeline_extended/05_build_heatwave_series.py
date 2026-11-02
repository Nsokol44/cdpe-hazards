#!/usr/bin/env python3
"""Step 05 - Monthly heat-wave series from gridMET daily Tmax, 1980-2023.

DESIGN LOCK Section 4, item 3. Daily Tmax is aggregated to the paper's
0.5 degree common grid (25-50 N, 125-66 W) by cell-mean binning. Land
cells: valid on >= 99% of days in 1981-2010. A cell's threshold for a
calendar day is the exact 98th percentile of Tmax over 1981-2010 within a
31-day centred window. A heat-wave day is a day in a run of >= 3
consecutive days with Tmax strictly above the cell threshold. Monthly
metric: heat-wave cell-days / number of land cells. Each day of a
qualifying run is credited to its own calendar month.
Deterministic; relative paths.

Inputs : data/raw/gridmet/tmmx_<year>.nc, 1980-2023
Outputs: results/hazard_series_heatwave.csv,
         results/heatwave_build_log.json (strict JSON)
Intermediate: the binned daily cube is cached in data/processed/
(regenerable cache, not part of the raw archive).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, num2date

ROOT = Path(__file__).resolve().parent.parent
GRIDMET = ROOT / "data" / "raw" / "gridmet"
CACHE = ROOT / "data" / "processed" / "tmmx_binned_05deg.npy"
OUT = ROOT / "results"
YEARS = list(range(1980, 2027))  # EXTENDED run: +2024-2026 gridMET
CLIM_YEARS = list(range(1981, 2011))
LAT_EDGES = np.arange(25.0, 50.01, 0.5)   # 51 edges, 50 rows
LON_EDGES = np.arange(-125.0, -65.99, 0.5)  # 119 edges, 118 cols
NROW, NCOL = 50, 118


def build_cube() -> tuple[np.ndarray, list]:
    """Bin every day of 1980-2023 to the 0.5 degree grid (cached)."""
    if CACHE.exists():
        cube = np.load(CACHE)
        dates = [None] * cube.shape[0]
        # dates are rebuilt deterministically below if needed by caller
        return cube, dates
    # bin indices from the native coordinate arrays of the first file
    with Dataset(GRIDMET / "tmmx_1980.nc") as ds:
        lat = np.asarray(ds.variables["lat"][:])
        lon = np.asarray(ds.variables["lon"][:])
    row_bin = np.clip(np.digitize(lat, LAT_EDGES) - 1, 0, NROW - 1)
    col_bin = np.clip(np.digitize(lon, LON_EDGES) - 1, 0, NCOL - 1)
    inside_r = (lat >= 25.0) & (lat < 50.0)
    inside_c = (lon >= -125.0) & (lon < -66.0)
    rb = row_bin[inside_r]
    cb = col_bin[inside_c]
    bid = (rb[:, None] * NCOL + cb[None, :]).ravel()
    cube_list = []
    for y in YEARS:
        with Dataset(GRIDMET / f"tmmx_{y}.nc") as ds:
            var = ds.variables["air_temperature"]
            var.set_auto_scale(False)
            var.set_auto_mask(False)
            scale = float(getattr(var, "scale_factor", 1.0))
            offset = float(getattr(var, "add_offset", 0.0))
            fill = getattr(var, "_FillValue", None)
            raw = np.asarray(var[:])  # uint16, one sequential read
        for k in range(raw.shape[0]):
            day = raw[k].astype(np.float32) * scale + offset - 273.15
            if fill is not None:
                day[raw[k] == fill] = np.nan
            sub = day[np.ix_(inside_r, inside_c)]
            fin = np.isfinite(sub)
            s = np.bincount(bid[fin.ravel()], weights=sub[fin],
                            minlength=NROW * NCOL).reshape(NROW, NCOL)
            c = np.bincount(bid[fin.ravel()],
                            minlength=NROW * NCOL).reshape(NROW, NCOL)
            with np.errstate(invalid="ignore", divide="ignore"):
                cube_list.append(np.where(c > 0, s / c, np.nan)
                                 .astype(np.float32))
        del raw
        print(f"  binned {y}", flush=True)
    cube = np.stack(cube_list)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.save(CACHE, cube)
    return cube, [None] * cube.shape[0]


def all_dates() -> list:
    dates = []
    for y in YEARS:
        with Dataset(GRIDMET / f"tmmx_{y}.nc") as ds:
            dv = ds.variables["day"]
            dates.extend(num2date(dv[:], dv.units,
                                  getattr(dv, "calendar", "standard")))
    return list(dates)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cube, _ = build_cube()
    dates = all_dates()
    assert len(dates) == cube.shape[0], (len(dates), cube.shape)
    # day-of-year on a 365-day circle (Feb 29 mapped to Feb 28) so the
    # 31-day window wraps around the year boundary, per standard practice
    def doy365(d) -> int:
        dd = d.timetuple().tm_yday
        leap = (d.year % 4 == 0 and (d.year % 100 != 0 or d.year % 400 == 0))
        return dd - 1 if (leap and dd > 59) else dd

    doy = np.array([doy365(d) for d in dates])
    clim = np.array([d.year in CLIM_YEARS for d in dates])

    # land mask: valid on >= 99% of climatology days
    valid_frac = np.isfinite(cube[clim]).mean(axis=0)
    land = valid_frac >= 0.99
    n_land = int(land.sum())
    print(f"land cells: {n_land} of {land.size}", flush=True)

    # exact windowed 98th percentiles per cell and calendar day
    thresh = np.full((365, NROW, NCOL), np.nan, dtype=np.float32)
    clim_idx = np.where(clim)[0]
    clim_doy = doy[clim]
    for dd in range(1, 366):
        dist = np.abs(clim_doy - dd)
        dist = np.minimum(dist, 365 - dist)  # circular distance
        pool = cube[clim_idx[dist <= 15]]  # (nsamples, NROW, NCOL)
        with np.errstate(all="ignore"):
            thresh[dd - 1] = np.nanpercentile(pool, 98, axis=0)
    thresh[:, ~land] = np.nan

    # heat-wave days: runs of >= 3 days strictly above threshold; each day
    # credited to its own month (when a run reaches 3, credit its 3 days;
    # further days credit immediately)
    monthly: dict[str, int] = {}
    runlen = np.zeros((NROW, NCOL), dtype=np.int16)
    keys = [f"{d.year:04d}-{d.month:02d}" for d in dates]
    for k in range(len(dates)):
        above = np.isfinite(cube[k]) & (cube[k] > thresh[doy[k] - 1])
        runlen = np.where(above, runlen + 1, 0)
        just3 = runlen == 3
        if just3.any():
            n3 = int(just3[land].sum())
            monthly[keys[k]] = monthly.get(keys[k], 0) + n3
            for back in (1, 2):
                if k - back >= 0:
                    monthly[keys[k - back]] = monthly.get(keys[k - back], 0) + n3
        over = runlen > 3
        if over.any():
            monthly[keys[k]] = monthly.get(keys[k], 0) + int(over[land].sum())

    lines = ["month,heatwave_days_per_cell"]
    # EXTENDED run: emit months through the binding endpoint 2026-07
    # only. The daily cube itself uses every day the gridMET files
    # contain, so runs crossing the endpoint are credited exactly as
    # the frozen algorithm credits them.
    for y in range(1980, 2027):
        for m in range(1, 13):
            if (y, m) > (2026, 7):
                continue
            key = f"{y:04d}-{m:02d}"
            lines.append(f"{key},{monthly.get(key, 0) / n_land:.6f}")
    (OUT / "hazard_series_heatwave.csv").write_text("\n".join(lines) + "\n")
    log = {"land_cells": n_land, "grid_shape": [NROW, NCOL],
           "threshold": "exact 98th percentile, 31-day window, 1981-2010",
           "months": len(lines) - 1}
    (OUT / "heatwave_build_log.json").write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
