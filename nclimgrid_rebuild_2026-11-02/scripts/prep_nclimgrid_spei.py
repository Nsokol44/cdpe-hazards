#!/usr/bin/env python3
"""Prep: aggregate the NCEI NIDIS nClimGrid SPEI period-of-record files
to the Arm A detector's 0.5-degree grid, exactly the grid of the
SPEIbase Arm A run of record (run_armA_2026-10-05/run_manifest.json:
lat centres 25.25..49.75 (50), lon centres -125.25..-66.75 (118);
cell edges lat 25.0..50.0, lon -125.5..-66.5).

Aggregation: exact spherical-overlap area weighting. Each fine cell's
contribution to a target cell is weighted by the spherical area of the
overlap (dlambda * (sin(lat_top) - sin(lat_bot))); the aggregated value
is the weighted mean over fine cells with finite product values.
Target cells with no finite contributing fine cell are NaN.

Also emits, per index: product metadata (read from the source file),
the last month with any valid value in the domain subset (the product
endpoint), per-month valid-cell counts over the domain, and a
domain-coverage summary vs the SPEIbase grid (data/spei01.nc).

Deterministic; relative to the package root. No parameters are tuned:
the target grid is the Arm A grid of record.

    python3 scripts/prep_nclimgrid_spei.py --variant gamma
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, date2num

PKG = Path(__file__).resolve().parents[1]
DATA = PKG / "data_nclimgrid"

# Arm A grid of record (run_armA_2026-10-05/run_manifest.json)
LAT_C = 25.25 + 0.5 * np.arange(50)          # 25.25 .. 49.75
LON_C = -125.25 + 0.5 * np.arange(118)       # -125.25 .. -66.75
LAT_E = np.arange(25.0, 50.01, 0.5)          # 51 edges
LON_E = np.arange(-125.5, -66.49, 0.5)       # 119 edges
NROW, NCOL = 50, 118


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            h.update(blk)
    return h.hexdigest()


def axis_weights(fine_c, fine_e_lo, fine_e_hi, tgt_e):
    """For each fine cell, the list of (target index, spherical weight
    factor along this axis). Lat axis factor: sin(top)-sin(bot) of the
    overlap; lon axis factor: overlap width in radians."""
    out = []
    for i, c in enumerate(fine_c):
        lo, hi = fine_e_lo[i], fine_e_hi[i]
        j0 = np.searchsorted(tgt_e, lo, side="right") - 1
        j1 = np.searchsorted(tgt_e, hi, side="left") - 1
        for j in range(max(j0, 0), min(j1, len(tgt_e) - 2) + 1):
            o_lo, o_hi = max(lo, tgt_e[j]), min(hi, tgt_e[j + 1])
            if o_hi > o_lo:
                out.append((i, j, o_lo, o_hi))
    return out


def build_mapping(lat_f, lon_f):
    dlat = float(np.median(np.diff(lat_f)))
    dlon = float(np.median(np.diff(lon_f)))
    lat_lo, lat_hi = lat_f - dlat / 2, lat_f + dlat / 2
    lon_lo, lon_hi = lon_f - dlon / 2, lon_f + dlon / 2
    lat_pairs = axis_weights(lat_f, lat_lo, lat_hi, LAT_E)
    lon_pairs = axis_weights(lon_f, lon_lo, lon_hi, LON_E)
    # lat factor: sin(overlap top) - sin(overlap bottom)
    lat_map = {}
    for i, j, lo, hi in lat_pairs:
        lat_map.setdefault(i, []).append(
            (j, np.sin(np.radians(hi)) - np.sin(np.radians(lo))))
    lon_map = {}
    for i, j, lo, hi in lon_pairs:
        lon_map.setdefault(i, []).append((j, np.radians(hi - lo)))
    # fi indexes the FULL fine arrays as passed (len(lat) x len(lon)
    # ravelled), so callers can apply it directly to a data slice.
    fi, ti, w = [], [], []
    ncols = len(lon_f)
    for i, lats in lat_map.items():
        for tj, wl in lats:
            for j, lons in lon_map.items():
                for tk, wk in lons:
                    fi.append(i * ncols + j)
                    ti.append(tj * NCOL + tk)
                    w.append(wl * wk)
    return (np.array(fi), np.array(ti), np.array(w, dtype=np.float64))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=["gamma", "pearson"])
    args = ap.parse_args()
    outdir = DATA / "agg05"
    outdir.mkdir(parents=True, exist_ok=True)

    report = {"variant": args.variant, "indices": {}}
    mapping = None
    for ts in (1, 3, 6):
        src = DATA / f"nclimgrid-spei-{args.variant}-{ts:02d}.nc"
        ds = Dataset(src)
        gatts = {a: str(ds.getncattr(a)) for a in ds.ncattrs()}
        # identify variable: the single multi-dim data variable
        varname = None
        for vn, v in ds.variables.items():
            if v.ndim == 3:
                varname = vn
        var = ds.variables[varname]
        dims = var.dimensions
        latname = [d for d in dims if "lat" in d.lower()][0]
        lonname = [d for d in dims if "lon" in d.lower()][0]
        timename = [d for d in dims if "time" in d.lower()][0]
        lat_all = np.asarray(ds.variables[latname][:], dtype=float)
        lon_all = np.asarray(ds.variables[lonname][:], dtype=float)
        tvar = ds.variables[timename]
        from netCDF4 import num2date
        tdates = num2date(tvar[:], tvar.units,
                          getattr(tvar, "calendar", "standard"))
        months = [f"{d.year:04d}-{d.month:02d}" for d in tdates]
        fill = getattr(var, "_FillValue", None)
        vatts = {a: str(var.getncattr(a)) for a in var.ncattrs()}

        # domain subset of fine cells (generous margin around target box)
        rmask = (lat_all >= 24.0) & (lat_all <= 51.0)
        cmask = (lon_all >= -126.5) & (lon_all <= -65.5)
        ridx = np.where(rmask)[0]
        cidx = np.where(cmask)[0]
        lat_f = lat_all[ridx]
        lon_f = lon_all[cidx]
        if mapping is None:
            fi, ti, w = build_mapping(lat_f, lon_f)
            assert fi.max() < len(lat_f) * len(lon_f)
            assert ti.max() < NROW * NCOL
            mapping = (fi, ti, w)
            wtot = np.bincount(ti, weights=w, minlength=NROW * NCOL)
        fi, ti, w = mapping

        order = [dims.index(timename), dims.index(latname),
                 dims.index(lonname)]
        T = len(months)
        agg = np.full((T, NROW, NCOL), np.nan, dtype=np.float32)
        valid_per_month = np.zeros(T, dtype=int)
        chunk = 12
        for t0 in range(0, T, chunk):
            t1 = min(T, t0 + chunk)
            if order != [0, 1, 2]:
                raise SystemExit(f"unexpected dim order {dims}")
            sl = var[t0:t1, ridx[0]:ridx[-1] + 1, cidx[0]:cidx[-1] + 1]
            raw = np.ma.filled(np.ma.asarray(sl, dtype=np.float64),
                               np.nan)
            if fill is not None:
                raw = np.where(raw == float(fill), np.nan, raw)
            raw = raw[:, :, :]  # (t, r, c) on the subset
            for k in range(t1 - t0):
                x = raw[k].ravel()
                fin = np.isfinite(x)
                xf, finf = x[fi], fin[fi]   # gather at mapping entries
                s = np.bincount(ti, weights=w * np.where(finf, xf, 0.0),
                                minlength=NROW * NCOL)
                wv = np.bincount(ti, weights=w * finf,
                                 minlength=NROW * NCOL)
                with np.errstate(invalid="ignore", divide="ignore"):
                    cell = np.where(wv > 0, s / np.where(wv > 0, wv, 1),
                                    np.nan)
                agg[t0 + k] = cell.reshape(NROW, NCOL).astype(np.float32)
                valid_per_month[t0 + k] = int(np.isfinite(cell).sum())
        ds.close()

        last_valid = int(np.max(np.where(valid_per_month > 0)[0]))
        endpoint = months[last_valid]
        out = outdir / f"spei{ts:02d}_nclimgrid_{args.variant}_05deg.nc"
        nco = Dataset(out, "w", format="NETCDF4")
        nco.createDimension("time", T)
        nco.createDimension("lat", NROW)
        nco.createDimension("lon", NCOL)
        tv = nco.createVariable("time", "f8", ("time",))
        tv.units = "days since 1900-01-01 00:00:00"
        tv.calendar = "standard"
        tv[:] = date2num(
            [__import__("datetime").datetime(d.year, d.month, 16)
             for d in tdates], tv.units, tv.calendar)
        lav = nco.createVariable("lat", "f8", ("lat",))
        lav[:] = LAT_C
        lov = nco.createVariable("lon", "f8", ("lon",))
        lov[:] = LON_C
        sv = nco.createVariable("spei", "f4", ("time", "lat", "lon"),
                                fill_value=np.nan)
        sv[:] = agg
        nco.setncattr("source_file", src.name)
        nco.setncattr("source_sha256", sha256(src))
        nco.setncattr("aggregation",
                      "exact spherical-overlap area-weighted mean of "
                      "finite fine cells onto the Arm A 0.5-degree grid "
                      "(edges lat 25.0-50.0, lon -125.5--66.5)")
        nco.setncattr("product_global_attrs_json", json.dumps(gatts))
        nco.setncattr("product_variable_attrs_json", json.dumps(vatts))
        nco.close()

        report["indices"][f"SPEI-{ts}"] = {
            "source_file": src.name, "source_sha256": sha256(src),
            "source_bytes": src.stat().st_size,
            "variable": varname, "dims": list(dims),
            "global_attrs": gatts, "variable_attrs": vatts,
            "file_months": [months[0], months[-1]],
            "domain_endpoint_last_valid_month": endpoint,
            "valid_cells_first_month": int(valid_per_month[0]),
            "valid_cells_2020_01":
                int(valid_per_month[months.index("2020-01")]),
            "agg_file": out.name, "agg_sha256": sha256(out),
        }
        np.save(outdir / f"valid_counts_spei{ts:02d}.npy", valid_per_month)
        (outdir / f"months_spei{ts:02d}.json").write_text(
            json.dumps(months))
        print(f"SPEI-{ts}: endpoint {endpoint}, "
              f"valid cells 2020-01 = {valid_per_month[months.index('2020-01')]}",
              flush=True)

    # SPEIbase grid comparison: valid cells over the same box/grid
    ds = Dataset(PKG / "data" / "spei01.nc")
    sp = ds.variables["spei"]
    la = np.asarray(ds.variables["lat"][:])
    lo = np.asarray(ds.variables["lon"][:])
    ri = np.where((la >= 25.0) & (la <= 50.0))[0]
    ci = np.where((lo >= -125.5) & (lo <= -66.5))[0]
    from netCDF4 import num2date as n2d
    tt = ds.variables["time"]
    td = n2d(tt[:], tt.units, getattr(tt, "calendar", "standard"))
    mi = [f"{d.year:04d}-{d.month:02d}" for d in td].index("2020-01")
    sub = np.asarray(sp[mi, ri[0]:ri[-1] + 1, ci[0]:ci[-1] + 1],
                     dtype=np.float64)
    fv = getattr(sp, "_FillValue", None)
    if fv is not None:
        sub = np.where(sub == float(fv), np.nan, sub)
    report["speibase_grid"] = {
        "grid_shape": [len(ri), len(ci)],
        "valid_cells_2020_01": int(np.isfinite(sub).sum()),
        "total_cells": int(sub.size),
    }
    ds.close()
    (outdir / "prep_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["speibase_grid"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
