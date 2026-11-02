#!/usr/bin/env python3
"""Gate diagnostics for the nClimGrid rerun (Step-3 stop-rule evidence).

Runs the FROZEN author detector's per-month classifier
(cdpe_sens.author_detector.classify_month_author, untouched) at the
baseline configuration (thr 1.5, r 4.0 deg, majority 0.5, max_na 0.10)
on BOTH grids over Jan 1980 - Dec 2023:

- new: data_nclimgrid/agg05/spei{01,03,06}_nclimgrid_gamma_05deg.nc
- old: data/spei{01,03,06}.nc (SPEIbase v2.10 global files, subset to
  the same Arm A cell centres)

Per month it records the dry/wet buffer NaN fractions (the max_na gate
inputs), the dry/wet within-buffer qualifying fractions, and the domain
finite share; the summary decomposes non-CDPE months into gate failures
vs majority failures. Also reports the marginal tail mass (% of valid
cell-months beyond +/-1.5) per grid and timescale. Outputs:
<out_prefix>_per_month.csv and <out_prefix>_summary.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cdpe_sens.author_detector import classify_month_author  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LAT_C = np.round(np.arange(25.25, 50.0, 0.5), 2)
LON_C = np.round(np.arange(-125.25, -66.5, 0.5), 2)
THR, RAD = 1.5, 4.0


def load_new(ts):
    p = ROOT / "data_nclimgrid" / "agg05" / f"spei{ts:02d}_nclimgrid_gamma_05deg.nc"
    with xr.open_dataset(p) as ds:
        times = [str(t)[:7] for t in ds["time"].values]
        arr = np.asarray(ds["spei"].values, dtype=float)
        lat = np.asarray(ds["lat"].values, dtype=float)
        lon = np.asarray(ds["lon"].values, dtype=float)
    assert np.allclose(lat, LAT_C) and np.allclose(lon, LON_C)
    return times, arr


def load_old(ts):
    p = ROOT / "data" / f"spei{ts:02d}.nc"
    with xr.open_dataset(p) as ds:
        lat = np.asarray(ds["lat"].values, dtype=float)
        lon = np.asarray(ds["lon"].values, dtype=float)
        ilat = [int(np.where(np.isclose(lat, v))[0][0]) for v in (25.25, 49.75)]
        ilon = [int(np.where(np.isclose(lon, v))[0][0]) for v in (-125.25, -66.75)]
        sub = ds["spei"].isel(lat=slice(ilat[0], ilat[1] + 1),
                              lon=slice(ilon[0], ilon[1] + 1))
        times = [str(t)[:7] for t in sub["time"].values]
        arr = np.asarray(sub.values, dtype=float)
    assert arr.shape[1:] == (50, 118), arr.shape
    return times, arr


def diagnose(grid_name, times, arr, start, end):
    rows = []
    i0, i1 = times.index(start), times.index(end)
    for i in range(i0, i1 + 1):
        f = arr[i]
        r = classify_month_author(f, LAT_C, LON_C, threshold=THR,
                                  radius_deg=RAD, majority_frac=0.5,
                                  max_na_frac=0.10)
        rows.append({
            "grid": grid_name, "date": times[i],
            "finite_share": float(np.isfinite(f).mean()),
            "dry_na_frac": r["dry_na_frac"], "wet_na_frac": r["wet_na_frac"],
            "dry_frac": r["dry_frac"], "wet_frac": r["wet_frac"],
            "is_cdpe": int(r["is_event"]),
            "spei_min": r["spei_min"], "spei_max": r["spei_max"],
        })
    df = pd.DataFrame(rows)
    valid = arr[i0:i1 + 1][np.isfinite(arr[i0:i1 + 1])]
    gate_fail = (df["dry_na_frac"] > 0.10) | (df["wet_na_frac"] > 0.10)
    gate_pass = df[~gate_fail]
    maj_fail = gate_pass[(gate_pass["dry_frac"] < 0.5)
                         | (gate_pass["wet_frac"] < 0.5)]
    summ = {
        "grid": grid_name, "window": [start, end], "n_months": len(df),
        "n_cdpe": int(df["is_cdpe"].sum()),
        "finite_share_min": float(df["finite_share"].min()),
        "finite_share_median": float(df["finite_share"].median()),
        "finite_share_max": float(df["finite_share"].max()),
        "months_dry_gate_fail": int((df["dry_na_frac"] > 0.10).sum()),
        "months_wet_gate_fail": int((df["wet_na_frac"] > 0.10).sum()),
        "months_either_gate_fail": int(gate_fail.sum()),
        "months_gate_pass": int((~gate_fail).sum()),
        "of_gate_pass_majority_fail": int(len(maj_fail)),
        "of_gate_pass_dry_majority_fail": int((gate_pass["dry_frac"] < 0.5).sum()),
        "of_gate_pass_wet_majority_fail": int((gate_pass["wet_frac"] < 0.5).sum()),
        "tail_mass_le_-1.5_pct": float(100 * (valid <= -1.5).mean()),
        "tail_mass_ge_+1.5_pct": float(100 * (valid >= 1.5).mean()),
    }
    return df, summ


def main():
    out_prefix = sys.argv[1]
    frames, summaries = [], {}
    for grid_name, loader in (("new_nclimgrid_gamma", load_new),
                              ("old_speibase_v210", load_old)):
        for ts in (1, 3, 6):
            times, arr = loader(ts)
            df, summ = diagnose(grid_name, times, arr, "1980-01", "2023-12")
            df.insert(1, "index", f"SPEI-{ts}")
            frames.append(df)
            summaries[f"{grid_name}|SPEI-{ts}"] = summ
            print(grid_name, f"SPEI-{ts}", json.dumps(summ))
    # extended-window extra months on the new grid, SPEI-1 baseline
    times, arr = load_new(1)
    df, summ = diagnose("new_nclimgrid_gamma_ext", times, arr,
                        "2024-01", "2026-07")
    df.insert(1, "index", "SPEI-1")
    frames.append(df)
    summaries["new_nclimgrid_gamma_ext|SPEI-1|2024-01..2026-07"] = summ
    print("ext extra months", json.dumps(summ))
    pd.concat(frames).to_csv(f"{out_prefix}_per_month.csv", index=False)
    Path(f"{out_prefix}_summary.json").write_text(
        json.dumps(summaries, indent=1))
    print("wrote", f"{out_prefix}_per_month.csv", f"{out_prefix}_summary.json")


if __name__ == "__main__":
    raise SystemExit(main())
