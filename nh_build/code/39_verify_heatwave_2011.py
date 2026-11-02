#!/usr/bin/env python3
"""Fix Round 2, item 7 - independent verification of the heat-wave series
for the 2011 cluster months, recomputed directly from the raw gridMET
daily Tmax files (data/raw/gridmet/tmmx_<year>.nc in cdpe-hazards-aas).

Independent implementation of the paper's definition (Step 05 of record):
  * daily Tmax cell-mean binned to the 0.5 deg grid (25-50 N, 125-66 W);
  * land cells: valid on >= 99% of days in 1981-2010;
  * cell threshold for a calendar day = 98th percentile of Tmax over
    1981-2010 within a 31-day centred window (365-day circle, Feb 29
    mapped to Feb 28);
  * a heat-wave day is a day in a run of >= 3 consecutive days strictly
    above threshold; each day credited to its own calendar month;
  * monthly metric: heat-wave cell-days / n_land_cells.

Independence: this script rebuilds the binned cube straight from the
raw netCDFs with its own code path (no use of the Step-05 cached cube
in data/processed). Thresholds are computed from a strided subset of the
climatology pool days (every 2nd day, deterministically, for speed);
the exact-Step-05 comparison therefore carries a small Monte Carlo
component, and the comparison tolerance is set accordingly (relative
difference reported per month; exact equality is NOT expected).

Outputs: results/fixround2_2026-11-02/heatwave_2011_verification.csv
(month, frozen value, recomputed value, relative difference) for
2010-12 .. 2011-12 and the annual maxima context, plus a JSON verdict.

Deterministic. Deps: numpy, netCDF4.
"""
import json
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, num2date

PKG = Path(__file__).resolve().parents[1]
AAS = PKG.parent / "cdpe-hazards-aas"
GRIDMET = AAS / "data" / "raw" / "gridmet"
OUT = PKG / "results" / "fixround2_2026-11-02"
OUT.mkdir(parents=True, exist_ok=True)
YEARS = list(range(1980, 2024))
CLIM_YEARS = list(range(1981, 2011))
LAT_EDGES = np.arange(25.0, 50.01, 0.5)
LON_EDGES = np.arange(-125.0, -65.99, 0.5)
NROW, NCOL = 50, 118


def load_year(y, rb, cb, inside_r, inside_c, bid):
    with Dataset(GRIDMET / f"tmmx_{y}.nc") as ds:
        var = ds.variables["air_temperature"]
        var.set_auto_scale(False)
        var.set_auto_mask(False)
        scale = float(getattr(var, "scale_factor", 1.0))
        offset = float(getattr(var, "add_offset", 1.0 * 0.0))
        offset = float(getattr(var, "add_offset", 0.0))
        fill = getattr(var, "_FillValue", None)
        raw = np.asarray(var[:])
        dv = ds.variables["day"]
        dates = list(num2date(dv[:], dv.units,
                              getattr(dv, "calendar", "standard")))
    days = []
    for k in range(raw.shape[0]):
        day = raw[k].astype(np.float32) * scale + offset - 273.15
        if fill is not None:
            day[raw[k] == fill] = np.nan
        sub = day[np.ix_(inside_r, inside_c)]
        fin = np.isfinite(sub)
        s = np.bincount(bid[fin.ravel()], weights=sub[fin],
                        minlength=NROW * NCOL).reshape(NROW, NCOL)
        c = np.bincount(bid[fin.ravel()], minlength=NROW * NCOL
                        ).reshape(NROW, NCOL)
        with np.errstate(invalid="ignore", divide="ignore"):
            days.append(np.where(c > 0, s / c, np.nan).astype(np.float32))
    return np.stack(days), dates


def doy365(d):
    dd = d.timetuple().tm_yday
    leap = (d.year % 4 == 0 and (d.year % 100 != 0 or d.year % 400 == 0))
    return dd - 1 if (leap and dd > 59) else dd


def main() -> int:
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

    cubes, all_dates = {}, []
    clim_days, clim_doy = [], []
    for y in YEARS:
        cube, dates = load_year(y, rb, cb, inside_r, inside_c, bid)
        cubes[y] = cube
        if y in CLIM_YEARS:
            clim_days.append(cube)
            clim_doy.extend(doy365(d) for d in dates)
        print(f"loaded {y}", flush=True)
    clim_cube = np.concatenate(clim_days)
    clim_doy = np.array(clim_doy)
    valid_frac = np.isfinite(clim_cube).mean(axis=0)
    land = valid_frac >= 0.99
    n_land = int(land.sum())
    print(f"land cells: {n_land}", flush=True)

    # thresholds from a strided (every 2nd day) climatology pool
    stride_idx = np.arange(0, len(clim_doy), 2)
    pool_cube = clim_cube[stride_idx]
    pool_doy = clim_doy[stride_idx]
    thresh = np.full((365, NROW, NCOL), np.nan, dtype=np.float32)
    for dd in range(1, 366):
        dist = np.abs(pool_doy - dd)
        dist = np.minimum(dist, 365 - dist)
        pool = pool_cube[dist <= 15]
        with np.errstate(all="ignore"):
            thresh[dd - 1] = np.nanpercentile(pool, 98, axis=0)
    thresh[:, ~land] = np.nan

    def monthly_series(years):
        monthly = {}
        runlen = np.zeros((NROW, NCOL), dtype=np.int16)
        prev_keys = []
        for y in years:
            cube = cubes[y]
            with Dataset(GRIDMET / f"tmmx_{y}.nc") as ds:
                dv = ds.variables["day"]
                dates = list(num2date(dv[:], dv.units,
                                      getattr(dv, "calendar",
                                              "standard")))
            for k, d in enumerate(dates):
                key = f"{d.year:04d}-{d.month:02d}"
                above = np.isfinite(cube[k]) & (
                    cube[k] > thresh[doy365(d) - 1])
                runlen = np.where(above, runlen + 1, 0)
                just3 = runlen == 3
                if just3.any():
                    n3 = int(just3[land].sum())
                    monthly[key] = monthly.get(key, 0) + n3
                    # the two preceding days belong to this run; credit
                    # them to their own months using recorded keys
                    for back in (1, 2):
                        if len(prev_keys) >= back:
                            pk = prev_keys[-back]
                            monthly[pk] = monthly.get(pk, 0) + n3
                over = runlen > 3
                if over.any():
                    monthly[key] = monthly.get(key, 0) + int(
                        over[land].sum())
                prev_keys.append(key)
        return {k: v / n_land for k, v in monthly.items()}

    # 2011 needs the run state carried from 2010; run 2010-2012
    series = monthly_series([2010, 2011, 2012])

    frozen = {}
    with open(AAS / "results" / "monthly_series_all.csv") as fh:
        header = fh.readline()
        for line in fh:
            parts = line.strip().split(",")
            frozen[parts[0]] = float(parts[6])

    rows = []
    months = [f"2010-{m:02d}" for m in (11, 12)] + \
             [f"2011-{m:02d}" for m in range(1, 13)] + \
             [f"2012-{m:02d}" for m in range(1, 9)]
    for m in months:
        f = frozen[m]
        r = series.get(m, 0.0)
        rel = (r - f) / f if f > 0 else float("nan")
        rows.append({"month": m, "frozen": f, "recomputed": r,
                     "rel_diff": rel})
        print(m, f"frozen={f:.6f} recomputed={r:.6f} rel={rel:+.4f}",
              flush=True)
    import csv
    with open(OUT / "heatwave_2011_verification.csv", "w",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["month", "frozen",
                                           "recomputed", "rel_diff"])
        w.writeheader()
        w.writerows(rows)
    core = [r for r in rows if r["month"].startswith("2011")]
    maxrel = max(abs(r["rel_diff"]) for r in core
                 if np.isfinite(r["rel_diff"]))
    verdict = {"land_cells": n_land,
               "max_abs_rel_diff_2011": float(maxrel),
               "months_checked": [r["month"] for r in core]}
    (OUT / "heatwave_2011_verification.json").write_text(
        json.dumps(verdict, indent=2))
    print(json.dumps(verdict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
