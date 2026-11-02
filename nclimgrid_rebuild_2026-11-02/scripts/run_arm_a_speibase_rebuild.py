#!/usr/bin/env python3
"""SPEIbase rebuild runs (2026-11-02): Workstreams A + B.

B -- SPEIbase detection with pole locations. The FROZEN author detector
(cdpe_sens.author_detector.detect_cdpe_author, untouched) on the
unmasked SPEIbase v2.10 SPEI-1/3/6 fields (data/spei{01,03,06}.nc subset
to the Arm A cell centres), locked Arm A configuration -- thresholds
{1.0, 1.5, 2.0} x radii {3.0, 4.0, 5.0} deg, majority 0.5, NA gate 0.10 --
over Jan 1980 - Dec 2023 (27 scenarios), saving per-month dry/wet pole
locations for EVERY scenario. The resulting month sets are verified
against results/run_armA_2026-10-05/ (run of record) before anything
downstream may use them: verification.json records per-scenario
equality; baselines must match exactly (Jaccard 1.000).

A -- Masked control (the decisive decomposition). The SAME SPEIbase
fields with the nClimGrid run's 0.5-degree valid-cell mask applied on
top (cells invalid in the aggregated nClimGrid product -- a static mask
of 3,575 cells, verified identical across timescales -- set to NaN;
values elsewhere unchanged), same frozen detector, same window, 27
scenarios, plus the baseline gate decomposition in the delta report's
section-3 format for both the A and B grids.

Outputs:
    results/run_armA_speibase_rebuild_2026-11-02/
        B_speibase_full/      scenarios.csv, events.csv,
                              cdpe_monthly_series.csv,
                              poles_by_scenario.csv, baseline_poles.csv,
                              gate_diagnostics_summary.json,
                              gate_diagnostics_per_month.csv,
                              run_manifest.json
        A_speibase_masked/    (same set)
        verification.json

    python3 scripts/run_arm_a_speibase_rebuild.py
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import xarray as xr

PKG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG_ROOT))

import cdpe_sens  # noqa: E402
from cdpe_sens.author_detector import classify_month_author, detect_cdpe_author  # noqa: E402
from cdpe_sens.events import event_table  # noqa: E402

MAJORITY_FRAC = 0.5
MAX_NA_FRAC = 0.10
RADII = [3.0, 4.0, 5.0]
THRESHOLDS = [1.0, 1.5, 2.0]
DETECTOR_NAME = "cdpe_sens.author_detector (author's published detector)"
BASELINE = {"index": "SPEI-1", "threshold": 1.5, "radius_deg": 4.0}
START, END = "1980-01", "2023-12"
LAT_C = np.round(np.arange(25.25, 50.0, 0.5), 2)
LON_C = np.round(np.arange(-125.25, -66.5, 0.5), 2)
OUT_ROOT = PKG_ROOT / "results" / "run_armA_speibase_rebuild_2026-11-02"
RECORD = PKG_ROOT / "results" / "run_armA_2026-10-05"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            h.update(blk)
    return h.hexdigest()


def load_speibase(ts: int):
    """SPEIbase v2.10 field subset to the Arm A centres, windowed.

    Mirrors scripts/gate_diagnostics.py load_old (the loader the delta
    report's section-3 diagnostics used to reproduce the run of record),
    with an explicit sortby('lat') so field rows and LAT_C are
    consistent by construction.
    """
    p = PKG_ROOT / "data" / f"spei{ts:02d}.nc"
    with xr.open_dataset(p) as ds:
        da = ds["spei"].sortby("lat")
        lat = np.asarray(da["lat"].values, dtype=float)
        lon = np.asarray(da["lon"].values, dtype=float)
        ilat = [int(np.where(np.isclose(lat, v))[0][0]) for v in (25.25, 49.75)]
        ilon = [int(np.where(np.isclose(lon, v))[0][0]) for v in (-125.25, -66.75)]
        sub = da.isel(lat=slice(ilat[0], ilat[1] + 1),
                      lon=slice(ilon[0], ilon[1] + 1))
        months = pd.PeriodIndex(
            [f"{d.year:04d}-{d.month:02d}"
             for d in pd.DatetimeIndex(sub["time"].values)], freq="M")
        keep = (months >= pd.Period(START, "M")) & (months <= pd.Period(END, "M"))
        arr = np.asarray(sub.isel(time=np.where(keep)[0]).values, dtype=float)
        dates = pd.DatetimeIndex(sub["time"].values)[keep]
        la = np.asarray(sub["lat"].values, dtype=float)
        lo = np.asarray(sub["lon"].values, dtype=float)
    assert arr.shape[1:] == (50, 118), arr.shape
    assert np.allclose(la, LAT_C) and np.allclose(lo, LON_C)
    assert len(dates) == 528
    return arr, dates


def load_nclimgrid_mask() -> np.ndarray:
    """Static valid-cell mask of the aggregated nClimGrid product.

    Verified here: finite-always over the window == finite-ever, count
    3,575, identical for SPEI-1/3/6.
    """
    masks = []
    for ts in (1, 3, 6):
        p = PKG_ROOT / "data_nclimgrid" / "agg05" / f"spei{ts:02d}_nclimgrid_gamma_05deg.nc"
        with xr.open_dataset(p) as ds:
            arr = np.asarray(ds["spei"].values, dtype=float)
            times = [str(t)[:7] for t in ds["time"].values]
        i0, i1 = times.index(START), times.index(END)
        win = arr[i0:i1 + 1]
        m_all = np.isfinite(win).all(axis=0)
        m_any = np.isfinite(win).any(axis=0)
        assert np.array_equal(m_all, m_any), f"mask not static, SPEI-{ts}"
        masks.append(m_all)
    assert np.array_equal(masks[0], masks[1]) and np.array_equal(masks[0], masks[2])
    assert int(masks[0].sum()) == 3575, int(masks[0].sum())
    return masks[0]


def gate_table(fields: dict, dates) -> tuple[pd.DataFrame, dict]:
    """Baseline gate decomposition in the delta report section-3 format."""
    rows, summ = [], {}
    for nm, arr in fields.items():
        for i in range(arr.shape[0]):
            f = arr[i]
            r = classify_month_author(f, LAT_C, LON_C, threshold=1.5,
                                      radius_deg=4.0, majority_frac=0.5,
                                      max_na_frac=0.10)
            rows.append({
                "index": nm, "date": dates[i],
                "finite_share": float(np.isfinite(f).mean()),
                "dry_na_frac": r["dry_na_frac"], "wet_na_frac": r["wet_na_frac"],
                "dry_frac": r["dry_frac"], "wet_frac": r["wet_frac"],
                "is_cdpe": int(r["is_event"]),
            })
        df = pd.DataFrame([x for x in rows if x["index"] == nm])
        gate_fail = (df["dry_na_frac"] > 0.10) | (df["wet_na_frac"] > 0.10)
        gp = df[~gate_fail]
        maj_fail = gp[(gp["dry_frac"] < 0.5) | (gp["wet_frac"] < 0.5)]
        summ[nm] = {
            "domain_finite_share": float(df["finite_share"].mean()),
            "months_failing_gate_either_pole": int(gate_fail.sum()),
            "gate_passing_months": int((~gate_fail).sum()),
            "of_gate_passers_failing_majority": int(len(maj_fail)),
            "cdpe_months": int(df["is_cdpe"].sum()),
        }
    return pd.DataFrame(rows), summ


def run_grid(fields: dict, dates, out_dir: Path, label: str) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)
    n_years = len(dates) / 12.0
    rows, ev_rows, pole_rows, series = [], [], [], {}
    for nm, vals in fields.items():
        for thr in THRESHOLDS:
            for r in RADII:
                out = detect_cdpe_author(vals, LAT_C, LON_C, threshold=thr,
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
                for t in range(len(dates)):
                    pole_rows.append({
                        "index": nm, "threshold": thr, "radius_deg": r,
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
        print(f"{label} {nm} done", flush=True)
    table = pd.DataFrame(rows)
    table.to_csv(out_dir / "scenarios.csv", index=False)
    pd.DataFrame(ev_rows).to_csv(out_dir / "events.csv", index=False)
    poles = pd.DataFrame(pole_rows)
    poles.to_csv(out_dir / "poles_by_scenario.csv", index=False)
    base = poles[(poles["index"] == BASELINE["index"])
                 & (poles["threshold"] == BASELINE["threshold"])
                 & (poles["radius_deg"] == BASELINE["radius_deg"])]
    base.drop(columns=["index", "threshold", "radius_deg"]).to_csv(
        out_dir / "baseline_poles.csv", index=False)
    ser_df = pd.DataFrame({"date": dates})
    for _, row in table.iterrows():
        key = (row["index"], float(row["threshold"]), float(row["radius_deg"]))
        ser_df[f"{row['index']}|thr={row['threshold']}|r={row['radius_deg']}"] = \
            series[key].astype(int)
    ser_df.to_csv(out_dir / "cdpe_monthly_series.csv", index=False)
    gdf, gsumm = gate_table(fields, dates)
    gdf.to_csv(out_dir / "gate_diagnostics_per_month.csv", index=False)
    (out_dir / "gate_diagnostics_summary.json").write_text(
        json.dumps(gsumm, indent=1))
    return table


def manifest(label: str, extra: dict) -> dict:
    return {
        "run": label,
        "package_version": cdpe_sens.__version__,
        "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "synthetic": False,
        "detector": DETECTOR_NAME,
        "detector_params": {"majority_frac": MAJORITY_FRAC,
                            "max_na_frac": MAX_NA_FRAC,
                            "radius_deg": RADII, "threshold": THRESHOLDS},
        "period": [START, END],
        "n_scenarios": 27,
        "grid": {"lat": [25.25, 49.75, 50], "lon": [-125.25, -66.75, 118]},
        "baseline": {**BASELINE, "majority_frac": MAJORITY_FRAC,
                     "max_na_frac": MAX_NA_FRAC},
        "input_files": [
            {"index": f"SPEI-{ts}", "path": f"data/spei{ts:02d}.nc",
             "sha256": sha256_file(PKG_ROOT / "data" / f"spei{ts:02d}.nc")}
            for ts in (1, 3, 6)],
        **extra,
    }


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    fields, dates = {}, None
    for ts in (1, 3, 6):
        arr, dates = load_speibase(ts)
        fields[f"SPEI-{ts}"] = arr
    mask = load_nclimgrid_mask()
    print(f"mask: {int(mask.sum())} valid cells of {mask.size}", flush=True)

    # ---- Workstream B: unmasked SPEIbase, poles saved ----------------
    b_dir = OUT_ROOT / "B_speibase_full"
    b_table = run_grid(fields, dates, b_dir, "B")
    (b_dir / "run_manifest.json").write_text(json.dumps(manifest(
        "B_speibase_full",
        {"note": "Frozen detector on unmasked SPEIbase v2.10; pole "
                 "locations saved for every scenario."}), indent=2, default=str))

    # ---- Verification vs run of record -------------------------------
    rec = pd.read_csv(RECORD / "cdpe_monthly_series.csv", parse_dates=["date"])
    rec["period"] = rec["date"].dt.to_period("M")
    rec = rec.set_index("period").sort_index()
    mine = pd.read_csv(b_dir / "cdpe_monthly_series.csv", parse_dates=["date"])
    mine["period"] = mine["date"].dt.to_period("M")
    mine = mine.set_index("period").sort_index()
    ver = {"all_scenarios_equal": True, "scenarios": {}}
    for _, row in b_table.iterrows():
        col = f"{row['index']}|thr={row['threshold']}|r={row['radius_deg']}"
        a = mine.loc[rec.index, col].astype(int).values
        b = rec[col].astype(int).values
        eq = bool(np.array_equal(a, b))
        inter = int((a & b).sum())
        union = int((a | b).sum())
        ver["scenarios"][col] = {
            "n_rebuild": int(a.sum()), "n_record": int(b.sum()),
            "equal": eq,
            "jaccard": (inter / union) if union else 1.0,
            "months_rebuild": [str(p) for p in rec.index[a == 1]],
        }
        ver["all_scenarios_equal"] &= eq
    ver["baselines"] = {
        ts: ver["scenarios"][f"{ts}|thr=1.5|r=4.0"]
        for ts in ("SPEI-1", "SPEI-3", "SPEI-6")}
    (OUT_ROOT / "verification.json").write_text(json.dumps(ver, indent=1))
    print("VERIFICATION all_scenarios_equal:", ver["all_scenarios_equal"],
          "| baselines:", {k: v["n_rebuild"] for k, v in ver["baselines"].items()},
          flush=True)

    # ---- Workstream A: SPEIbase values under the CONUS mask ----------
    masked = {nm: np.where(mask[None, :, :], arr, np.nan)
              for nm, arr in fields.items()}
    a_dir = OUT_ROOT / "A_speibase_masked"
    run_grid(masked, dates, a_dir, "A")
    (a_dir / "run_manifest.json").write_text(json.dumps(manifest(
        "A_speibase_masked",
        {"note": "Masked control: SPEIbase v2.10 values with the "
                 "nClimGrid product's static 0.5-degree valid-cell mask "
                 "(3,575 of 5,900 cells) applied on top; masked cells "
                 "set to NaN, values elsewhere unchanged.",
         "mask_source": "data_nclimgrid/agg05/spei{01,03,06}_nclimgrid_gamma_05deg.nc "
                        "(finite mask, static across the window, identical "
                        "across timescales)",
         "mask_valid_cells": int(mask.sum())}), indent=2, default=str))
    brow = pd.read_csv(a_dir / "scenarios.csv")
    for ts in ("SPEI-1", "SPEI-3", "SPEI-6"):
        r = brow[(brow["index"] == ts) & (brow["threshold"] == 1.5)
                 & (brow["radius_deg"] == 4.0)].iloc[0]
        print(f"A baseline {ts}: {int(r['n_cdpe_months'])} months", flush=True)
    print("done ->", OUT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
