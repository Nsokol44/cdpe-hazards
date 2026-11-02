#!/usr/bin/env python
"""Two-arm run driver for the CDPE sensitivity analysis (locked design,
Nick, 2026-10-04; see AUTHOR_ALGORITHM.md sec. 7 and data/DATA_MANIFEST.md).

    python scripts/run_two_arms.py --config config/example_config.json --arm A
    python scripts/run_two_arms.py --config config/example_config.json --arm B
    python scripts/run_two_arms.py --config config/example_config.json --arm B --radius 4.0
    python scripts/run_two_arms.py --config config/example_config.json --arm B --combine-only

Why this exists: ``scripts/run_analysis.py`` calls ``run_sensitivity``
without a ``detector=`` argument, has no radius factor, and stamps its
manifest with the generic stand-in detector
(``cdpe_sens.events.detect_cdpe``). Running the locked design through it
would misstate provenance. This driver instead runs BOTH arms with the
author's published detector (``cdpe_sens.author_detector``):

Arm A -- author's pipeline as published, over precomputed fields
    (SPEIbase SPEI-1/3/6 + locally computed CRU SPI-1):
    3 thresholds x 3 radii per index = 27 SPEI + 9 SPI = 36 scenarios,
    majority 0.5, NA gate 0.10. Window 1980-2023: the staged SPEIbase
    release is v2.10 (CRU TS 4.08), whose record ends Dec 2023; the
    published catalogue used 1980-2024. The window actually analysed is
    recorded in every Arm A output; it is NOT presented as 1980-2024.
    The baseline scenario (SPEI-1, thr 1.5, r 4.0) is checked against
    the data-pass smoke values (46 CDPE months / 43 contiguous events
    on 1980-2023) before any other Arm A output is written.

Arm B -- computed-index factorial with the author detector:
    2 datasets x 5 timescales x 2 distributions x 2 calibration periods
    x 2 water balances x 3 thresholds x 3 radii = 720 scenarios,
    majority fixed 0.5, NA gate 0.10. ``min_area_frac`` /
    ``min_cluster_cells`` are held at the config's singleton levels
    because the runner requires those factors; the author detector
    ignores both by construction. Arm B runs per radius as restartable
    chunks (``chunks/arm_b_r<r>/`` with per-chunk manifests); the
    combined outputs are (re)built from the chunks by ``--combine-only``
    or automatically once all three chunks exist.

Primary response metric is ``n_cdpe_months`` (the author detector's
monthly classifications). ``n_events`` (contiguous-run count from
``cdpe_sens.events.event_table``) is reported alongside, labelled --
the two are never conflated. Metrics are computed per arm, never pooled.

Outputs follow the package conventions of ``scripts/run_analysis.py``
(scenarios.csv, variance_decomposition.csv, oat_agreement.csv,
dataset_agreement.csv [Arm B], baseline_bootstrap.csv, figures,
run_manifest.json) plus events.csv, agreement_vs_baseline.csv and the
monthly CDPE series, in ``results/run_armA_<date>/`` and
``results/run_armB_<date>/``. Real data only: nothing here reads or
writes synthetic data, and no SYNTHETIC stamp is ever applied.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

PKG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG_ROOT))

import cdpe_sens  # noqa: E402
from cdpe_sens import figures, io  # noqa: E402
from cdpe_sens.author_detector import detect_cdpe_author, make_author_detector  # noqa: E402
from cdpe_sens.events import event_table  # noqa: E402
from cdpe_sens.sensitivity import (FACTORS, bootstrap_rate_ci,  # noqa: E402
                                   interannual_correlation, jaccard,
                                   run_sensitivity, variance_decomposition)

# Author-detector parameters fixed by the locked design.
MAJORITY_FRAC = 0.5
MAX_NA_FRAC = 0.10
RADII = [3.0, 4.0, 5.0]
ARM_B_FACTORS = FACTORS + ["radius_deg"]

DETECTOR_NAME = "cdpe_sens.author_detector (author's published detector)"

# Arm A baseline smoke values from the data pass (data/check_arm_a.py,
# DATA_MANIFEST.md sec. 1.3): SPEI-1, thr 1.5, r 4.0, maj 0.5, NA 0.10,
# on the staged v2.10 record, window 1980-2023.
ARM_A_SMOKE = {"n_cdpe_months": 46, "n_events": 43}


def _load_run_analysis():
    spec = importlib.util.spec_from_file_location(
        "run_analysis", PKG_ROOT / "scripts" / "run_analysis.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            h.update(blk)
    return h.hexdigest()


def _config_sha(cfg):
    return hashlib.sha256(
        json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()


def _base_manifest(cfg, arm):
    return {
        "arm": arm,
        "package_version": cdpe_sens.__version__,
        "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "synthetic": False,
        "config_sha256": _config_sha(cfg),
        "detector": DETECTOR_NAME,
        "detector_params": {"majority_frac": MAJORITY_FRAC,
                            "max_na_frac": MAX_NA_FRAC,
                            "radius_deg": RADII},
        "primary_metric": "n_cdpe_months",
        "secondary_metric": ("n_events (contiguous-run count from "
                             "cdpe_sens.events.event_table; labelled, "
                             "never conflated with n_cdpe_months)"),
        "driver": "scripts/run_two_arms.py",
    }


def _jsonify(d):
    return {k: (v.item() if isinstance(v, np.generic) else v)
            for k, v in d.items()}


# ---------------------------------------------------------------------------
# Generalized agreement helpers (package FACTORS + radius for Arm B;
# index/threshold/radius for Arm A). Mirror sensitivity.oat_agreement /
# dataset_agreement semantics exactly, over an explicit factor list.
# ---------------------------------------------------------------------------
def oat_agreement_general(series, dates, levels, factors, baseline):
    """One-at-a-time agreement with a baseline scenario.

    series : dict key tuple (in `factors` order) -> bool array
    levels : dict factor -> list of levels present
    baseline : dict factor -> level for every factor in `factors`
    """
    base_key = tuple(baseline[f] for f in factors)
    base = series[base_key]
    rows = []
    for i, f in enumerate(factors):
        for lev in levels[f]:
            if lev == baseline[f]:
                continue
            key = list(base_key)
            key[i] = lev
            alt = series[tuple(key)]
            rows.append({
                "factor": f, "level": lev,
                "baseline_months": int(base.sum()), "alt_months": int(alt.sum()),
                "jaccard": jaccard(base, alt),
                "interannual_spearman": interannual_correlation(base, alt, dates),
            })
    return pd.DataFrame(rows)


def agreement_vs_baseline(table, series, dates, factors, baseline, id_cols):
    """Jaccard + interannual Spearman of EVERY scenario vs the baseline."""
    base = series[tuple(baseline[f] for f in factors)]
    rows = []
    for _, row in table.iterrows():
        key = tuple(row[f] for f in factors)
        s = series[key]
        rows.append({**{c: row[c] for c in id_cols},
                     "n_cdpe_months": int(s.sum()),
                     "jaccard_vs_baseline": jaccard(base, s),
                     "interannual_spearman_vs_baseline":
                         interannual_correlation(base, s, dates)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Arm A -- precomputed SPEIbase SPEI + CRU SPI-1 through the author detector
# ---------------------------------------------------------------------------
US_LAT = (24.81, 50.0)     # author's Study 1 loader clip (data/check_arm_a.py)
US_LON = (-125.62, -66.58)
ARM_A_WINDOW = ("1980-01-01", "2023-12-31")   # v2.10 record limit -- see docstring


def _load_arm_a_field(path, var):
    import xarray as xr
    ds = xr.open_dataset(path)
    da = ds[var]
    lat = "lat" if "lat" in da.dims else "latitude"
    lon = "lon" if "lon" in da.dims else "longitude"
    da = da.rename({lat: "lat", lon: "lon"}).sortby("lat")
    da = da.sel(lat=slice(*US_LAT), lon=slice(*US_LON))
    da = da.sel(time=slice(*ARM_A_WINDOW))
    return da, ds


def run_arm_a(cfg, out_dir):
    aa = cfg["arm_a"]
    thresholds = [float(t) for t in aa["detector"]["threshold"]]
    radii = [float(r) for r in aa["detector"]["radius_deg"]]
    if radii != RADII or float(aa["detector"]["majority_frac"]) != MAJORITY_FRAC \
            or float(aa["detector"]["max_na_frac"]) != MAX_NA_FRAC:
        raise ValueError("config arm_a detector block disagrees with the "
                         "locked design constants in this driver")

    fields = {}   # index name -> (values, lat, lon, dates, file record)
    for entry in aa["spei_files"]:
        name = f"SPEI-{entry['timescale']}"
        da, ds = _load_arm_a_field(PKG_ROOT / entry["path"], entry["var"])
        fields[name] = (np.asarray(da.values, dtype=float),
                        da.lat.values.astype(float), da.lon.values.astype(float),
                        pd.DatetimeIndex(da["time"].values),
                        {"index": name, "path": entry["path"],
                         "bytes": (PKG_ROOT / entry["path"]).stat().st_size,
                         "sha256": _sha256_file(PKG_ROOT / entry["path"])})
        ds.close()
    spi = aa["spi_file"]
    name = f"SPI-{spi['timescale']}"
    da, ds = _load_arm_a_field(PKG_ROOT / spi["path"], spi["var"])
    fields[name] = (np.asarray(da.values, dtype=float),
                    da.lat.values.astype(float), da.lon.values.astype(float),
                    pd.DatetimeIndex(da["time"].values),
                    {"index": name, "path": spi["path"],
                     "bytes": (PKG_ROOT / spi["path"]).stat().st_size,
                     "sha256": _sha256_file(PKG_ROOT / spi["path"])})
    ds.close()

    # All four fields must share the clipped grid and the analysis window.
    ref = fields["SPEI-1"]
    for nm, (vals, lat, lon, dates, _) in fields.items():
        if vals.shape != ref[0].shape or not np.array_equal(lat, ref[1]) \
                or not np.array_equal(lon, ref[2]) or not dates.equals(ref[3]):
            raise ValueError(f"Arm A field {nm} is not aligned with SPEI-1")
    dates = ref[3]
    # SPEIbase timestamps sit at mid-month; check the window by month.
    if len(dates) != 528 or (dates[0].year, dates[0].month) != (1980, 1) \
            or (dates[-1].year, dates[-1].month) != (2023, 12):
        raise ValueError(f"Arm A window is {dates[0].date()}..{dates[-1].date()} "
                         f"({len(dates)} months), expected Jan 1980..Dec 2023 (528)")
    n_years = len(dates) / 12.0

    factors = ["index", "threshold", "radius_deg"]
    rows, ev_rows, series = [], [], {}
    for nm, (vals, lat, lon, _, _) in fields.items():
        for thr in thresholds:
            for r in radii:
                out = detect_cdpe_author(vals, lat, lon, threshold=thr,
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
                        # Author-detector fractions are WITHIN-BUFFER
                        # qualifying fractions, not domain area fractions.
                        "peak_dry_within_buffer_frac": e.get("peak_drought_frac"),
                        "peak_wet_within_buffer_frac": e.get("peak_pluvial_frac"),
                    })
        print(f"Arm A: {nm} done ({len(rows)} scenarios so far)")

    table = pd.DataFrame(rows)
    baseline = {"index": "SPEI-1", "threshold": 1.5, "radius_deg": 4.0}
    brow = table[(table["index"] == baseline["index"])
                 & (table["threshold"] == baseline["threshold"])
                 & (table["radius_deg"] == baseline["radius_deg"])].iloc[0]
    smoke = {"n_cdpe_months": int(brow["n_cdpe_months"]),
             "n_events": int(brow["n_events"])}
    if smoke != ARM_A_SMOKE:
        raise SystemExit(
            f"Arm A baseline does NOT reproduce the data-pass smoke values: "
            f"got {smoke}, expected {ARM_A_SMOKE} (SPEI-1, thr=1.5, r=4.0, "
            f"window 1980-2023, SPEIbase v2.10). Stopping before writing "
            f"outputs -- diagnose the field/detector path first.")
    print(f"Arm A baseline check OK: {smoke} == smoke values {ARM_A_SMOKE}")

    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / "scenarios.csv", index=False)
    pd.DataFrame(ev_rows).to_csv(out_dir / "events.csv", index=False)

    ser_df = pd.DataFrame({"date": dates})
    for _, row in table.iterrows():
        key = (row["index"], float(row["threshold"]), float(row["radius_deg"]))
        ser_df[f"{row['index']}|thr={row['threshold']}|r={row['radius_deg']}"] = \
            series[key].astype(int)
    ser_df.to_csv(out_dir / "cdpe_monthly_series.csv", index=False)

    vd = variance_decomposition(table, "n_cdpe_months", factors=factors)
    vd.to_csv(out_dir / "variance_decomposition.csv", index=False)

    levels = {f: sorted(table[f].unique().tolist(), key=str) for f in factors}
    levels["threshold"] = thresholds
    levels["radius_deg"] = radii
    oat = oat_agreement_general(series, dates, levels, factors, baseline)
    oat.to_csv(out_dir / "oat_agreement.csv", index=False)
    agree = agreement_vs_baseline(table, series, dates, factors, baseline,
                                  ["index", "threshold", "radius_deg"])
    agree.to_csv(out_dir / "agreement_vs_baseline.csv", index=False)

    B = int(cfg.get("bootstrap", {}).get("B", 2000))
    boots = []
    for nm in ("SPEI-1", "SPI-1"):   # baseline + the index-type contrast twin
        ci = bootstrap_rate_ci(series[(nm, 1.5, 4.0)], dates, B=B)
        boots.append({"index": nm, "threshold": 1.5, "radius_deg": 4.0, **ci})
    pd.DataFrame(boots).to_csv(out_dir / "baseline_bootstrap.csv", index=False)

    figures.plot_variance_decomposition(
        vd, out_dir / "fig_variance_decomposition.png",
        title="Arm A — variance decomposition of CDPE months")
    figures.plot_oat(oat, out_dir / "fig_oat_agreement.png")
    figures.plot_count_heatmaps(
        table, out_dir / "fig_count_heatmaps.png", metric="months_per_year",
        x="threshold", y="radius_deg", facet="index")

    manifest = _base_manifest(cfg, "A")
    manifest.update({
        "period": ["1980-01", "2023-12"],
        "timestamp_note": ("Source files carry mid-month timestamps "
                           "(e.g. 1980-01-16); months covered are "
                           "Jan 1980 through Dec 2023 inclusive."),
        "window_note": ("Arm A analysed on 1980-2023, the full record of "
                        "the staged SPEIbase v2.10 release (CRU TS 4.08). "
                        "The published catalogue (52 events) used 1980-2024 "
                        "on a different release (v2.11, CRU TS 4.09, not "
                        "obtainable from this network -- DATA_MANIFEST.md "
                        "sec. 1.1). This window must not be reported as "
                        "1980-2024."),
        "n_scenarios": int(len(table)),
        "grid": {"lat": [float(ref[1][0]), float(ref[1][-1]), int(len(ref[1]))],
                 "lon": [float(ref[2][0]), float(ref[2][-1]), int(len(ref[2]))],
                 "clip": {"lat": list(US_LAT), "lon": list(US_LON)}},
        "baseline": {**baseline, "majority_frac": MAJORITY_FRAC,
                     "max_na_frac": MAX_NA_FRAC},
        "baseline_check": {
            "scenario": "SPEI-1, threshold 1.5, radius 4.0 deg, majority 0.5, "
                        "NA gate 0.10, window 1980-2023",
            "observed": smoke,
            "data_pass_smoke_values": ARM_A_SMOKE,
            "reproduced": True,
            "published": {"n_events": int(aa["baseline_scenario"]["published_events"]),
                          "window": aa["baseline_scenario"]["published_window"],
                          "note": "Published count is on 1980-2024 and a "
                                  "different SPEIbase release; the gap is "
                                  "attributed to the release/window, per "
                                  "DATA_MANIFEST.md sec. 1.3 -- not silently "
                                  "adopted."},
        },
        "speibase_release": aa["speibase_release"],
        "spi_provenance": spi["provenance"],
        "input_files": [rec for (_, _, _, _, rec) in
                        (fields[nm] for nm in ("SPEI-1", "SPEI-3", "SPEI-6", "SPI-1"))],
    })
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    print(f"Arm A: wrote {len(table)} scenarios to {out_dir}")
    return table


# ---------------------------------------------------------------------------
# Arm B -- computed-index factorial with the author detector, per-radius chunks
# ---------------------------------------------------------------------------
def _arm_b_datasets(cfg):
    ra = _load_run_analysis()
    loaded = ra.load_real_datasets(cfg)
    start, end = cfg["period"]
    return {d.name: io.restrict_period(d, start, end) for d in loaded}


def _arm_b_baseline(cfg):
    base = {"dataset": cfg["datasets"][0]["name"],
            **{**{"timescale": 6, "dist": "loglogistic", "cal_period": "full",
                  "water_balance": "spei", "threshold": 1.0,
                  "min_area_frac": 0.10, "min_cluster_cells": 1},
               **cfg.get("baseline", {})},
            "radius_deg": 4.0}
    return base


def run_arm_b_radius(cfg, out_dir, radius):
    datasets = _arm_b_datasets(cfg)
    d0 = next(iter(datasets.values()))
    detector = make_author_detector(d0.lat, d0.lon, radius_deg=radius,
                                    majority_frac=MAJORITY_FRAC,
                                    max_na_frac=MAX_NA_FRAC)
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
    cman = _base_manifest(cfg, "B")
    cman.update({
        "chunk": f"arm_b_r{radius}", "radius_deg": radius,
        "detector_callable": "cdpe_sens.author_detector.make_author_detector",
        "detector_params": {"majority_frac": MAJORITY_FRAC,
                            "max_na_frac": MAX_NA_FRAC, "radius_deg": radius},
        "period": [str(res.dates[0].date()), str(res.dates[-1].date())],
        "n_scenarios": int(len(tab)),
        "levels": {k: list(map(str, v)) for k, v in levels.items()},
        "elapsed_seconds": round(elapsed, 1),
    })
    (chunk / "chunk_manifest.json").write_text(json.dumps(cman, indent=2, default=str))
    print(f"Arm B radius {radius}: {len(tab)} scenarios in {elapsed:.1f}s -> {chunk}")
    return chunk


def combine_arm_b(cfg, out_dir):
    chunks = {}
    for r in RADII:
        chunk = out_dir / "chunks" / f"arm_b_r{r}"
        if not (chunk / "scenarios.csv").exists():
            raise SystemExit(f"Arm B chunk for radius {r} is missing ({chunk}); "
                             f"run it first: --arm B --radius {r}")
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
            # CSV round-trip turns ints into numpy types; normalize key types
            k8 = (str(k8[0]), int(k8[1]), str(k8[2]), str(k8[3]), str(k8[4]),
                  float(k8[5]), float(k8[6]), int(k8[7]))
            series[k8 + (float(r),)] = z[rec["array"]].astype(bool)
    table = pd.concat(tables, ignore_index=True)
    expected = int(np.prod([table[f].nunique() for f in ARM_B_FACTORS]))
    if len(table) != 720 or len(table) != expected:
        raise SystemExit(f"Arm B combined table has {len(table)} rows "
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
    baseline = _arm_b_baseline(cfg)
    oat = oat_agreement_general(series, dates, levels, ARM_B_FACTORS, baseline)
    oat.to_csv(out_dir / "oat_agreement.csv", index=False)
    agree = agreement_vs_baseline(table, series, dates, ARM_B_FACTORS, baseline,
                                  ARM_B_FACTORS)
    agree.to_csv(out_dir / "agreement_vs_baseline.csv", index=False)

    # Pairwise dataset agreement at the baseline settings (incl. radius 4.0).
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
    pd.DataFrame(dsa_rows).to_csv(out_dir / "dataset_agreement.csv", index=False)

    B = int(cfg.get("bootstrap", {}).get("B", 2000))
    boots = []
    for name in levels["dataset"]:
        key = tuple(name if f == "dataset" else baseline[f] for f in ARM_B_FACTORS)
        ci = bootstrap_rate_ci(series[key], dates, B=B)
        boots.append({"dataset": name, **ci})
    pd.DataFrame(boots).to_csv(out_dir / "baseline_bootstrap.csv", index=False)

    figures.plot_variance_decomposition(
        vd, out_dir / "fig_variance_decomposition.png",
        title="Arm B — variance decomposition of CDPE months")
    figures.plot_oat(oat, out_dir / "fig_oat_agreement.png")
    fixed = {k: baseline[k] for k in ("dist", "cal_period", "water_balance",
                                      "min_area_frac", "min_cluster_cells",
                                      "radius_deg")}
    figures.plot_count_heatmaps(table, out_dir / "fig_count_heatmaps.png",
                                fixed=fixed)

    manifest = _base_manifest(cfg, "B")
    manifest.update({
        "period": [str(dates[0].date()), str(dates[-1].date())],
        "n_scenarios": int(len(table)),
        "baseline": _jsonify(baseline),
        "levels": {k: [str(v) for v in vals] for k, vals in levels.items()},
        "detector_callable": "cdpe_sens.author_detector.make_author_detector",
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
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    print(f"Arm B: wrote {len(table)} scenarios to {out_dir}")
    return table


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config/example_config.json")
    ap.add_argument("--arm", choices=["A", "B", "all"], default="all")
    ap.add_argument("--radius", type=float, choices=RADII,
                    help="Arm B: run only this radius chunk")
    ap.add_argument("--combine-only", action="store_true",
                    help="Arm B: rebuild combined outputs from existing chunks")
    ap.add_argument("--out-root", default="results")
    ap.add_argument("--date", default=pd.Timestamp.now().strftime("%Y-%m-%d"),
                    help="date stamp for the run directories (YYYY-MM-DD)")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = PKG_ROOT / cfg_path
    cfg = json.loads(cfg_path.read_text())
    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = PKG_ROOT / out_root

    if args.arm in ("A", "all"):
        run_arm_a(cfg, out_root / f"run_armA_{args.date}")
    if args.arm in ("B", "all"):
        out_b = out_root / f"run_armB_{args.date}"
        if args.combine_only:
            combine_arm_b(cfg, out_b)
        elif args.radius is not None:
            run_arm_b_radius(cfg, out_b, args.radius)
            if all((out_b / "chunks" / f"arm_b_r{r}" / "scenarios.csv").exists()
                   for r in RADII):
                combine_arm_b(cfg, out_b)
        else:
            for r in RADII:
                run_arm_b_radius(cfg, out_b, r)
            combine_arm_b(cfg, out_b)


if __name__ == "__main__":
    main()
