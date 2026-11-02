#!/usr/bin/env python
"""Arm B rerun with a SPEIbase land mask applied to the input fields.

    python scripts/run_arm_b_masked.py [--config config/example_config.json]
                                       [--radius 4.0] [--combine-only]

Commissioned 2026-10-05 after the pole-location audit
(AUDIT_FINDINGS.md, Item 2): in the original Arm B run
(results/run_armB_2026-10-05) the reanalysis fields carry values over
water, and 58.9% (NARR ts6) / 70.0% (ERA5 ts6) of baseline CDPE months
have a dry or wet pole over water. This driver reruns the identical
720-scenario Arm B factorial with ONE change: before detection, every
computed index field has its water cells set to NaN, so the analysis
reproduces Arm A's semantics (SPEIbase is land-only: ocean cells are
fill, poles can only fall on land, and buffer NaN fractions include
masked cells exactly as coastal Arm A buffers include ocean NaNs).

The detector is NOT modified: masking is applied by a thin wrapper
around ``cdpe_sens.author_detector.make_author_detector``, and the
factorial itself runs through the same
``cdpe_sens.sensitivity.run_sensitivity`` machinery and the same
chunk/combine output code paths as ``scripts/run_two_arms.py`` (the
original driver is not edited). The unmasked run directory is left
untouched and is retained as the archived sensitivity comparison.

Land mask construction (identical to AUDIT_FINDINGS.md Item 2):
  * Source: SPEIbase v2.10 ``data/spei01.nc`` on the Arm A clip grid
    (author's loader clip, lat 24.81-50.0 / lon -125.62..-66.58 ->
    cell centres 25.25..49.75 N, -125.25..-66.75 W, 50 x 118).
  * A SPEIbase cell is LAND iff it carries a finite value in at least
    one month of Jan 1980..Dec 2023 (SPEIbase is a land-only product;
    ocean cells are fill in every month). 4,399 of 5,900 cells are
    land; 5 coastal/fit-failure cells are finite in some but not all
    months and count as land under this rule.
  * The Arm B common grid (25-50 N, -125..-66 W at 0.5 deg, 51 x 119)
    is offset 0.25 deg from the SPEIbase grid, so each Arm B cell
    takes the land/water class of its NEAREST SPEIbase cell (offset
    <= 0.25 deg per axis; ties resolve to the first cell, matching
    numpy argmin, exactly as in the audit). 4,443 of 6,069 Arm B
    cells are land (73.2%). The mask is global land inside the box
    (Canadian/Mexican land cells count as land), as in Arm A.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

PKG_ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(PKG_ROOT))

from cdpe_sens import figures  # noqa: E402
from cdpe_sens.author_detector import make_author_detector  # noqa: E402
from cdpe_sens.events import event_table  # noqa: E402
from cdpe_sens.sensitivity import (bootstrap_rate_ci,  # noqa: E402
                                   interannual_correlation, jaccard,
                                   run_sensitivity, variance_decomposition)


def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "run_two_arms", PKG_ROOT / "scripts" / "run_two_arms.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rt = _load_driver()
MAJORITY_FRAC = rt.MAJORITY_FRAC
MAX_NA_FRAC = rt.MAX_NA_FRAC
RADII = rt.RADII
ARM_B_FACTORS = rt.ARM_B_FACTORS
DETECTOR_NAME = rt.DETECTOR_NAME + " [input fields land-masked; detector unchanged]"


# ---------------------------------------------------------------------------
# Land mask (AUDIT_FINDINGS.md Item 2 construction, replicated exactly)
# ---------------------------------------------------------------------------
def build_land_mask(cfg, ref_lat, ref_lon):
    """Return (land_mask bool (Y, X) on the Arm B grid, provenance dict)."""
    import xarray as xr
    spei_rel = cfg["arm_a"]["spei_files"][0]["path"]     # data/spei01.nc
    spei_path = PKG_ROOT / spei_rel
    ds = xr.open_dataset(spei_path)
    da = ds["spei"].sortby("lat").sel(lat=slice(*rt.US_LAT),
                                      lon=slice(*rt.US_LON))
    win = da.sel(time=slice(*rt.ARM_A_WINDOW))
    mlat = win.lat.values.astype(float)
    mlon = win.lon.values.astype(float)
    finite_any = np.isfinite(np.asarray(win.values, dtype=float)).any(axis=0)
    finite_all = np.isfinite(np.asarray(win.values, dtype=float)).all(axis=0)
    ds.close()

    # Nearest SPEIbase cell per Arm B cell -- the audit's classify step,
    # including its argmin first-occurrence tie behaviour.
    land = np.empty((len(ref_lat), len(ref_lon)), dtype=bool)
    for iy, la in enumerate(ref_lat):
        jy = int(np.argmin(np.abs(mlat - float(la))))
        for ix, lo in enumerate(ref_lon):
            jx = int(np.argmin(np.abs(mlon - float(lo))))
            land[iy, ix] = bool(finite_any[jy, jx])

    prov = {
        "applied": True,
        "application": ("Water cells set to NaN in every computed index "
                        "field before detection; cdpe_sens.author_detector "
                        "itself unmodified. Reproduces Arm A semantics "
                        "(SPEIbase ocean cells are fill/NaN)."),
        "source_product": ("SPEIbase v2.10 spei01.nc (land-only product; "
                            "ocean cells are fill in every month)"),
        "source_file": spei_rel,
        "source_file_sha256": rt._sha256_file(spei_path),
        "speibase_release": cfg["arm_a"]["speibase_release"],
        "clip": {"lat": list(rt.US_LAT), "lon": list(rt.US_LON)},
        "window": list(rt.ARM_A_WINDOW),
        "land_rule": ("SPEIbase cell is land iff finite in >= 1 month of "
                      "the window (audit AUDIT_FINDINGS.md Item 2)"),
        "speibase_grid_land_cells": int(finite_any.sum()),
        "speibase_grid_total_cells": int(finite_any.size),
        "speibase_cells_finite_all_months": int(finite_all.sum()),
        "speibase_cells_finite_some_months": int((finite_any & ~finite_all).sum()),
        "transfer_to_arm_b_grid": ("nearest SPEIbase cell per Arm B cell "
                                   "(grids offset 0.25 deg; numpy argmin "
                                   "first-occurrence ties, as in the audit)"),
        "arm_b_grid_land_cells": int(land.sum()),
        "arm_b_grid_total_cells": int(land.size),
        "arm_b_grid_land_fraction": float(land.mean()),
        "scope_note": ("Mask is global land inside the bounding box "
                       "(Canadian/Mexican land cells are land), matching "
                       "Arm A; it is not a US-only mask."),
    }
    return land, prov


def make_masked_detector(lat, lon, land_mask, radius_deg):
    """Author detector with the land mask applied to its input field."""
    base = make_author_detector(lat, lon, radius_deg=radius_deg,
                                majority_frac=MAJORITY_FRAC,
                                max_na_frac=MAX_NA_FRAC)
    land = np.asarray(land_mask, dtype=bool)

    def _detector(spei, drought_thr, pluvial_thr, min_area_frac,
                  min_cluster_cells):
        masked = np.where(land[None, :, :], np.asarray(spei, dtype=float),
                          np.nan)
        return base(masked, drought_thr, pluvial_thr, min_area_frac,
                    min_cluster_cells)

    return _detector


# ---------------------------------------------------------------------------
# Chunk run + combine (mirrors run_two_arms, plus mask provenance)
# ---------------------------------------------------------------------------
def run_radius(cfg, cfg_abs, out_dir, radius, land_mask, mask_prov):
    datasets = rt._arm_b_datasets(cfg_abs)
    d0 = next(iter(datasets.values()))
    if not (np.array_equal(d0.lat.astype(float),
                           np.arange(25.0, 50.0 + 1e-9, 0.5))
            and d0.precip.shape[1:] == land_mask.shape):
        raise ValueError("Arm B grid does not match the land-mask grid")
    detector = make_masked_detector(d0.lat, d0.lon, land_mask, radius)
    levels = cfg["levels"]
    t0 = time.time()
    res = run_sensitivity(datasets, levels, detector=detector, verbose=True)
    elapsed = time.time() - t0

    chunk = out_dir / "chunks" / f"arm_b_r{radius}"
    chunk.mkdir(parents=True, exist_ok=True)
    tab = res.table.copy()
    tab["radius_deg"] = radius
    tab["detector"] = DETECTOR_NAME
    tab["majority_frac"] = MAJORITY_FRAC
    tab["max_na_frac"] = MAX_NA_FRAC
    tab.to_csv(chunk / "scenarios.csv", index=False)

    keys = [tuple(k) for k in res.series.keys()]
    np.savez_compressed(chunk / "series.npz",
                        dates=res.dates.values.astype("datetime64[ns]"),
                        **{f"s{i}": res.series[k].astype(np.int8)
                           for i, k in enumerate(keys)})
    (chunk / "series_keys.json").write_text(json.dumps(
        [{"key": list(k), "array": f"s{i}"} for i, k in enumerate(keys)]))
    cman = rt._base_manifest(cfg, "B")
    cman.update({
        "chunk": f"arm_b_r{radius}", "radius_deg": radius,
        "driver": "scripts/run_arm_b_masked.py",
        "detector": DETECTOR_NAME,
        "detector_callable": "cdpe_sens.author_detector.make_author_detector "
                             "(wrapped: land mask applied to input field)",
        "detector_params": {"majority_frac": MAJORITY_FRAC,
                            "max_na_frac": MAX_NA_FRAC, "radius_deg": radius},
        "land_mask": mask_prov,
        "period": [str(res.dates[0].date()), str(res.dates[-1].date())],
        "n_scenarios": int(len(tab)),
        "levels": {k: list(map(str, v)) for k, v in levels.items()},
        "elapsed_seconds": round(elapsed, 1),
    })
    (chunk / "chunk_manifest.json").write_text(
        json.dumps(cman, indent=2, default=str))
    print(f"Masked Arm B radius {radius}: {len(tab)} scenarios in "
          f"{elapsed:.1f}s -> {chunk}")
    return chunk


def combine(cfg, out_dir, mask_prov):
    chunks = {}
    for r in RADII:
        chunk = out_dir / "chunks" / f"arm_b_r{r}"
        if not (chunk / "scenarios.csv").exists():
            raise SystemExit(f"Masked Arm B chunk for radius {r} is missing "
                             f"({chunk}); run it first: --radius {r}")
        chunks[r] = chunk

    tables, series = [], {}
    dates = None
    for r, chunk in chunks.items():
        tab = pd.read_csv(chunk / "scenarios.csv")
        tables.append(tab)
        z = np.load(chunk / "series.npz")
        keys = json.loads((chunk / "series_keys.json").read_text())
        cdates = pd.DatetimeIndex(z["dates"])
        if dates is None:
            dates = cdates
        elif not cdates.equals(dates):
            raise ValueError(f"chunk r={r} time axis differs from other chunks")
        for rec in keys:
            k8 = tuple(rec["key"])
            k8 = (str(k8[0]), int(k8[1]), str(k8[2]), str(k8[3]), str(k8[4]),
                  float(k8[5]), float(k8[6]), int(k8[7]))
            series[k8 + (float(r),)] = z[rec["array"]].astype(bool)
    table = pd.concat(tables, ignore_index=True)
    expected = int(np.prod([table[f].nunique() for f in ARM_B_FACTORS]))
    if len(table) != 720 or len(table) != expected:
        raise SystemExit(f"Masked Arm B combined table has {len(table)} rows "
                         f"(expected 720, balanced-factorial product {expected})")

    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / "scenarios.csv", index=False)

    ev_rows = []
    for _, row in table.iterrows():
        key = tuple(row[f] for f in ARM_B_FACTORS)
        key = (str(key[0]), int(key[1]), str(key[2]), str(key[3]), str(key[4]),
               float(key[5]), float(key[6]), int(key[7]), float(key[8]))
        ev = event_table(series[key], dates)
        for _, e in ev.iterrows():
            ev_rows.append({**{f: row[f] for f in ARM_B_FACTORS},
                            "start": e["start"], "end": e["end"],
                            "duration_months": int(e["duration_months"])})
    pd.DataFrame(ev_rows).to_csv(out_dir / "events.csv", index=False)

    vd = variance_decomposition(table, "n_cdpe_months", factors=ARM_B_FACTORS)
    vd.to_csv(out_dir / "variance_decomposition.csv", index=False)

    levels = {f: list(table[f].unique()) for f in ARM_B_FACTORS}
    baseline = rt._arm_b_baseline(cfg)
    oat = rt.oat_agreement_general(series, dates, levels, ARM_B_FACTORS,
                                   baseline)
    oat.to_csv(out_dir / "oat_agreement.csv", index=False)
    agree = rt.agreement_vs_baseline(table, series, dates, ARM_B_FACTORS,
                                     baseline, ARM_B_FACTORS)
    agree.to_csv(out_dir / "agreement_vs_baseline.csv", index=False)

    dsa_rows = []
    for a, b in itertools.combinations(levels["dataset"], 2):
        ka = tuple(a if f == "dataset" else baseline[f] for f in ARM_B_FACTORS)
        kb = tuple(b if f == "dataset" else baseline[f] for f in ARM_B_FACTORS)
        sa, sb = series[ka], series[kb]
        dsa_rows.append({"dataset_a": a, "dataset_b": b,
                         "months_a": int(sa.sum()), "months_b": int(sb.sum()),
                         "jaccard": jaccard(sa, sb),
                         "interannual_spearman":
                             interannual_correlation(sa, sb, dates)})
    pd.DataFrame(dsa_rows).to_csv(out_dir / "dataset_agreement.csv",
                                  index=False)

    B = int(cfg.get("bootstrap", {}).get("B", 2000))
    boots = []
    for name in levels["dataset"]:
        key = tuple(name if f == "dataset" else baseline[f] for f in ARM_B_FACTORS)
        ci = bootstrap_rate_ci(series[key], dates, B=B)
        boots.append({"dataset": name, **ci})
    pd.DataFrame(boots).to_csv(out_dir / "baseline_bootstrap.csv", index=False)

    figures.plot_variance_decomposition(
        vd, out_dir / "fig_variance_decomposition.png",
        title="Arm B (land-masked) — variance decomposition of CDPE months")
    figures.plot_oat(oat, out_dir / "fig_oat_agreement.png")
    fixed = {k: baseline[k] for k in ("dist", "cal_period", "water_balance",
                                      "min_area_frac", "min_cluster_cells",
                                      "radius_deg")}
    figures.plot_count_heatmaps(table, out_dir / "fig_count_heatmaps.png",
                                fixed=fixed)

    manifest = rt._base_manifest(cfg, "B")
    manifest.update({
        "period": [str(dates[0].date()), str(dates[-1].date())],
        "n_scenarios": int(len(table)),
        "baseline": rt._jsonify(baseline),
        "levels": {k: [str(v) for v in vals] for k, vals in levels.items()},
        "driver": "scripts/run_arm_b_masked.py",
        "detector": DETECTOR_NAME,
        "detector_callable": "cdpe_sens.author_detector.make_author_detector "
                             "(wrapped: land mask applied to input field)",
        "land_mask": mask_prov,
        "land_mask_note": ("LAND MASK APPLIED: every computed index field "
                           "had water cells set to NaN before detection "
                           "(SPEIbase finite-value mask; see 'land_mask'). "
                           "The author detector code is unchanged. This run "
                           "supersedes results/run_armB_2026-10-05 as the "
                           "primary Arm B analysis; the unmasked run is "
                           "retained unchanged as a sensitivity comparison."),
        "comparison_run": "results/run_armB_2026-10-05 (unmasked)",
        "note": ("min_area_frac and min_cluster_cells are singletons in the "
                 "config because run_sensitivity requires the factors; the "
                 "author detector ignores both by construction, so they "
                 "carry zero variance share by design, not by estimation."),
        "chunks": {f"r{r}": json.loads(
            (chunks[r] / "chunk_manifest.json").read_text())["elapsed_seconds"]
            for r in RADII},
        "input_files": [{"dataset": d["name"], "role": role,
                         "path": d[role]["path"],
                         "bytes": (PKG_ROOT / d[role]["path"]).stat().st_size}
                        for d in cfg["datasets"] for role in ("precip", "tmean")],
    })
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str))
    print(f"Masked Arm B: wrote {len(table)} scenarios to {out_dir}")
    return table


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config/example_config.json")
    ap.add_argument("--radius", type=float, choices=RADII,
                    help="run only this radius chunk")
    ap.add_argument("--combine-only", action="store_true")
    ap.add_argument("--out-dir", default="results/run_armB_masked_2026-10-05")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = PKG_ROOT / cfg_path
    cfg = json.loads(cfg_path.read_text())
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = PKG_ROOT / out_dir

    # Pristine cfg drives manifests/config hash (identical to the unmasked
    # run: sha 19ad4cc0...); a path-absolutized copy drives data loading.
    cfg_abs = json.loads(cfg_path.read_text())
    for d in cfg_abs["datasets"]:
        for role in ("precip", "tmean"):
            d[role]["path"] = str(PKG_ROOT / d[role]["path"])

    datasets = rt._arm_b_datasets(cfg_abs)
    d0 = next(iter(datasets.values()))
    land_mask, mask_prov = build_land_mask(cfg, d0.lat.astype(float),
                                           d0.lon.astype(float))
    print(f"Land mask: {mask_prov['arm_b_grid_land_cells']} of "
          f"{mask_prov['arm_b_grid_total_cells']} Arm B cells are land "
          f"({100 * mask_prov['arm_b_grid_land_fraction']:.1f}%)")

    if not args.combine_only:
        radii = [args.radius] if args.radius is not None else RADII
        for r in radii:
            run_radius(cfg, cfg_abs, out_dir, r, land_mask, mask_prov)
    if args.combine_only or args.radius is None or all(
            (out_dir / "chunks" / f"arm_b_r{r}" / "scenarios.csv").exists()
            for r in RADII):
        combine(cfg, out_dir, mask_prov)


if __name__ == "__main__":
    main()
