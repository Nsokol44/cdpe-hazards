#!/usr/bin/env python3
"""Arm A detection on the nClimGrid SPEI fields (author-directed data
substitution, 2026-11-01): the author's published detector
(cdpe_sens.author_detector.detect_cdpe_author) with the locked Arm A
configuration of record -- thresholds {1.0, 1.5, 2.0} x radii
{3.0, 4.0, 5.0} deg, majority 0.5, NA gate 0.10 -- over the aggregated
0.5-degree fields in data_nclimgrid/agg05/. 27 scenarios (SPEI-1/3/6;
no SPI arm exists under this product). Detector code and parameters
are untouched; only the input data and the window are new.

Outputs mirror results/run_armA_2026-10-05/: scenarios.csv, events.csv,
cdpe_monthly_series.csv, plus baseline_poles.csv (per-month dry/wet
pole locations and diagnostics for the baseline configuration),
monthly_grid_diagnostics.csv (per-month finite-cell share of the
analysis grid, for the NA-gate diagnostics), and run_manifest.json.

    python3 scripts/run_arm_a_nclimgrid.py \
        --start 1980-01 --end 2023-12 \
        --out results/run_armA_nclimgrid_2026-11-01
    python3 scripts/run_arm_a_nclimgrid.py \
        --start 1980-01 --end 2026-08 \
        --out results/run_armA_nclimgrid_ext_2026-11-01
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

PKG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG_ROOT))

import cdpe_sens  # noqa: E402
from cdpe_sens.author_detector import detect_cdpe_author  # noqa: E402
from cdpe_sens.events import event_table  # noqa: E402
from cdpe_sens.sensitivity import jaccard  # noqa: E402

MAJORITY_FRAC = 0.5
MAX_NA_FRAC = 0.10
RADII = [3.0, 4.0, 5.0]
THRESHOLDS = [1.0, 1.5, 2.0]
DETECTOR_NAME = "cdpe_sens.author_detector (author's published detector)"
BASELINE = {"index": "SPEI-1", "threshold": 1.5, "radius_deg": 4.0}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            h.update(blk)
    return h.hexdigest()


def load_field(path: Path, start: str, end: str):
    import xarray as xr
    ds = xr.open_dataset(path)
    da = ds["spei"].sortby("lat")
    months = pd.PeriodIndex(
        [f"{d.year:04d}-{d.month:02d}"
         for d in pd.DatetimeIndex(da["time"].values)], freq="M")
    keep = (months >= pd.Period(start, "M")) & (months <= pd.Period(end, "M"))
    da = da.isel(time=np.where(keep)[0])
    dates = pd.DatetimeIndex(da["time"].values)
    vals = np.asarray(da.values, dtype=float)
    ds.close()
    return vals, da.lat.values.astype(float), da.lon.values.astype(float), dates


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="gamma")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out_dir = PKG_ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    agg = PKG_ROOT / "data_nclimgrid" / "agg05"

    fields, inputs = {}, []
    for ts in (1, 3, 6):
        p = agg / f"spei{ts:02d}_nclimgrid_{args.variant}_05deg.nc"
        vals, lat, lon, dates = load_field(p, args.start, args.end)
        fields[f"SPEI-{ts}"] = (vals, lat, lon, dates)
        inputs.append({"index": f"SPEI-{ts}", "path": str(p.relative_to(PKG_ROOT)),
                       "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    ref = fields["SPEI-1"]
    for nm, (vals, la, lo, da) in fields.items():
        assert vals.shape == ref[0].shape and np.array_equal(la, ref[1]) \
            and np.array_equal(lo, ref[2]) and da.equals(ref[3]), nm
    dates = ref[3]
    n_years = len(dates) / 12.0

    rows, ev_rows, series = [], [], {}
    poles_rows = []
    diag_rows = []
    for nm, (vals, la, lo, _) in fields.items():
        finite_share = np.isfinite(vals).mean(axis=(1, 2))
        for thr in THRESHOLDS:
            for r in RADII:
                out = detect_cdpe_author(vals, la, lo, threshold=thr,
                                         radius_deg=r,
                                         majority_frac=MAJORITY_FRAC,
                                         max_na_frac=MAX_NA_FRAC)
                cd = np.asarray(out["cdpe"], dtype=bool)
                ev = event_table(cd, dates, out.get("drought_frac"),
                                 out.get("pluvial_frac"))
                series[(nm, thr, r)] = cd
                rows.append({
                    "index": nm, "threshold": thr, "radius_deg": r,
                    "detector": DETECTOR_NAME,
                    "majority_frac": MAJORITY_FRAC, "max_na_frac": MAX_NA_FRAC,
                    "n_cdpe_months": int(cd.sum()),
                    "n_events": int(len(ev)),
                    "mean_duration": float(ev["duration_months"].mean()) if len(ev) else 0.0,
                    "months_per_year": float(cd.sum() / n_years),
                })
                for _, e in ev.iterrows():
                    ev_rows.append({
                        "index": nm, "threshold": thr, "radius_deg": r,
                        "start": e["start"], "end": e["end"],
                        "duration_months": int(e["duration_months"]),
                        "peak_dry_within_buffer_frac": e.get("peak_drought_frac"),
                        "peak_wet_within_buffer_frac": e.get("peak_pluvial_frac"),
                    })
                if (nm, thr, r) == (BASELINE["index"], BASELINE["threshold"],
                                    BASELINE["radius_deg"]):
                    for t in range(len(dates)):
                        poles_rows.append({
                            "date": dates[t], "is_cdpe": int(cd[t]),
                            "dry_lat": out["dry_center"][t][0],
                            "dry_lon": out["dry_center"][t][1],
                            "wet_lat": out["wet_center"][t][0],
                            "wet_lon": out["wet_center"][t][1],
                            "dry_frac": out["drought_frac"][t],
                            "wet_frac": out["pluvial_frac"][t],
                            "spei_min": out["spei_min"][t],
                            "spei_max": out["spei_max"][t],
                        })
        for t in range(len(dates)):
            diag_rows.append({"index": nm, "date": dates[t],
                              "finite_share_of_grid": float(finite_share[t])})
        print(f"{nm} done ({len(rows)} scenarios)", flush=True)

    table = pd.DataFrame(rows)
    table.to_csv(out_dir / "scenarios.csv", index=False)
    pd.DataFrame(ev_rows).to_csv(out_dir / "events.csv", index=False)
    pd.DataFrame(poles_rows).to_csv(out_dir / "baseline_poles.csv", index=False)
    pd.DataFrame(diag_rows).to_csv(out_dir / "monthly_grid_diagnostics.csv",
                                  index=False)
    ser_df = pd.DataFrame({"date": dates})
    for _, row in table.iterrows():
        key = (row["index"], float(row["threshold"]), float(row["radius_deg"]))
        ser_df[f"{row['index']}|thr={row['threshold']}|r={row['radius_deg']}"] = \
            series[key].astype(int)
    ser_df.to_csv(out_dir / "cdpe_monthly_series.csv", index=False)

    prep = json.loads((agg / "prep_report.json").read_text())
    manifest = {
        "arm": "A (nClimGrid SPEI substitution, author-directed 2026-11-01)",
        "package_version": cdpe_sens.__version__,
        "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "synthetic": False,
        "detector": DETECTOR_NAME,
        "detector_params": {"majority_frac": MAJORITY_FRAC,
                            "max_na_frac": MAX_NA_FRAC,
                            "radius_deg": RADII,
                            "threshold": THRESHOLDS},
        "primary_metric": "n_cdpe_months",
        "secondary_metric": ("n_events (contiguous-run count from "
                             "cdpe_sens.events.event_table; labelled, "
                             "never conflated with n_cdpe_months)"),
        "driver": "scripts/run_arm_a_nclimgrid.py",
        "period": [args.start, args.end],
        "n_scenarios": int(len(table)),
        "grid": {"lat": [float(ref[1][0]), float(ref[1][-1]), int(len(ref[1]))],
                 "lon": [float(ref[2][0]), float(ref[2][-1]), int(len(ref[2]))]},
        "baseline": {**BASELINE, "majority_frac": MAJORITY_FRAC,
                     "max_na_frac": MAX_NA_FRAC},
        "product": prep,
        "input_files": inputs,
        "note": ("SPEI source is the NCEI NIDIS nClimGrid gridded SPEI "
                 "(period-of-record netCDF), aggregated to the Arm A "
                 "0.5-degree grid by scripts/prep_nclimgrid_spei.py. "
                 "No SPI arm exists under this product."),
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2,
                                                         default=str))
    brow = table[(table["index"] == "SPEI-1") & (table["threshold"] == 1.5)
                 & (table["radius_deg"] == 4.0)].iloc[0]
    print(f"baseline SPEI-1 thr1.5 r4.0: {int(brow['n_cdpe_months'])} months, "
          f"{int(brow['n_events'])} events -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
