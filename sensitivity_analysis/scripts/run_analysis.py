#!/usr/bin/env python
"""Run the CDPE sensitivity analysis from a JSON config.

    python scripts/run_analysis.py --config config/example_config.json
    python scripts/run_analysis.py --demo-synthetic --allow-synthetic   # smoke test only

Synthetic data is refused unless --allow-synthetic is given, and any output
directory produced from it contains SYNTHETIC_DO_NOT_PUBLISH.txt and is
prefixed 'SYNTHETIC_'. This guard exists because mixing simulated and real
evidence in one manuscript is an easy, serious mistake.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cdpe_sens
from cdpe_sens import figures, io
from cdpe_sens.sensitivity import (DEFAULT_LEVELS, FACTORS, bootstrap_rate_ci,
                                   dataset_agreement, oat_agreement, run_sensitivity,
                                   variance_decomposition)
from cdpe_sens.synthetic import make_synthetic_dataset

DEFAULT_BASELINE = {"timescale": 6, "dist": "loglogistic", "cal_period": "full",
                    "water_balance": "spei", "threshold": 1.0, "min_area_frac": 0.10,
                    "min_cluster_cells": 1}


def load_real_datasets(cfg):
    g = cfg["common_grid"]
    tgt_lat = np.arange(g["lat"][0], g["lat"][1] + 1e-9, g["lat"][2])
    tgt_lon = np.arange(g["lon"][0], g["lon"][1] + 1e-9, g["lon"][2])
    loaded = []
    for d in cfg["datasets"]:
        p, plat, plon, pdates = io.open_monthly_field(
            d["precip"]["path"], d["precip"]["var"], d["precip"].get("lat", "lat"),
            d["precip"].get("lon", "lon"), d["precip"].get("time", "time"))
        t, tlat, tlon, tdates = io.open_monthly_field(
            d["tmean"]["path"], d["tmean"]["var"], d["tmean"].get("lat", "lat"),
            d["tmean"].get("lon", "lon"), d["tmean"].get("time", "time"))
        if not pdates.equals(tdates):
            raise ValueError(f"{d['name']}: precip and temperature time axes differ")
        p = io.to_mm_per_month(p, pdates, d["precip"]["units"])
        t = io.to_celsius(t, d["tmean"]["units"])
        p = io.regrid(p, plat, plon, tgt_lat, tgt_lon)
        t = io.regrid(t, tlat, tlon, tgt_lat, tgt_lon)
        loaded.append(io.MonthlyDataset(d["name"], p, t, tgt_lat, tgt_lon, pdates))
    return loaded


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--demo-synthetic", action="store_true")
    ap.add_argument("--allow-synthetic", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    if args.demo_synthetic:
        cfg = {"output_dir": "outputs/demo", "levels": {
            "timescale": [3, 6], "dist": ["loglogistic", "empirical"],
            "water_balance": ["spei", "spi"], "threshold": [0.8, 1.0],
            "min_area_frac": [0.05, 0.10], "min_cluster_cells": [1, 5]},
            "baseline": {**DEFAULT_BASELINE}, "bootstrap": {"B": 500}}
        loaded = [make_synthetic_dataset("synA", seed=1), make_synthetic_dataset("synB", seed=2)]
    else:
        if not args.config:
            ap.error("--config required unless --demo-synthetic")
        cfg = json.loads(Path(args.config).read_text())
        loaded = load_real_datasets(cfg)

    synthetic = any(d.is_synthetic for d in loaded)
    if synthetic and not args.allow_synthetic:
        sys.exit("Refusing to run on synthetic data without --allow-synthetic.")

    start, end = (cfg.get("period") or [None, None])
    if start is None:
        start, end = io.common_period(loaded)
    datasets = {d.name: io.restrict_period(d, start, end) for d in loaded}

    out_dir = Path(args.out or cfg.get("output_dir", "outputs/run"))
    if synthetic:
        out_dir = out_dir.with_name("SYNTHETIC_" + out_dir.name)
    out_dir.mkdir(parents=True, exist_ok=True)
    if synthetic:
        (out_dir / "SYNTHETIC_DO_NOT_PUBLISH.txt").write_text(
            "These outputs were generated from random synthetic data to test the code.\n"
            "They contain no scientific information and must not appear in any manuscript.\n")

    levels = cfg.get("levels", {})
    res = run_sensitivity(datasets, levels, verbose=True)
    baseline = {"dataset": list(datasets)[0], **{**DEFAULT_BASELINE, **cfg.get("baseline", {})}}
    for f in FACTORS:
        if baseline[f] not in res.levels[f]:
            raise ValueError(f"baseline {f}={baseline[f]!r} not in levels {res.levels[f]}")

    res.table.to_csv(out_dir / "scenarios.csv", index=False)
    vd = variance_decomposition(res.table, "n_cdpe_months")
    vd.to_csv(out_dir / "variance_decomposition.csv", index=False)
    oat = oat_agreement(res, baseline)
    oat.to_csv(out_dir / "oat_agreement.csv", index=False)
    dsa = dataset_agreement(res, baseline) if len(datasets) > 1 else pd.DataFrame()
    dsa.to_csv(out_dir / "dataset_agreement.csv", index=False)

    B = cfg.get("bootstrap", {}).get("B", 2000)
    boots = []
    for name in datasets:
        key = tuple(name if f == "dataset" else baseline[f] for f in FACTORS)
        ci = bootstrap_rate_ci(res.series[key], res.dates, B=B)
        boots.append({"dataset": name, **ci})
    pd.DataFrame(boots).to_csv(out_dir / "baseline_bootstrap.csv", index=False)

    figures.plot_variance_decomposition(vd, out_dir / "fig_variance_decomposition.png")
    figures.plot_oat(oat, out_dir / "fig_oat_agreement.png")
    fixed = {k: baseline[k] for k in ("dist", "cal_period", "water_balance",
                                      "min_area_frac", "min_cluster_cells")}
    figures.plot_count_heatmaps(res.table, out_dir / "fig_count_heatmaps.png", fixed=fixed)

    manifest = {
        "package_version": cdpe_sens.__version__, "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__, "pandas": pd.__version__,
        "period": [str(pd.Timestamp(start).date()), str(pd.Timestamp(end).date())],
        "n_scenarios": int(len(res.table)), "synthetic": synthetic,
        "config_sha256": hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str)
                                        .encode()).hexdigest(),
        "baseline": {k: (v if not isinstance(v, np.generic) else v.item())
                     for k, v in baseline.items()},
        "detector": "cdpe_sens.events.detect_cdpe (generic stand-in)",
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    print(f"Wrote {len(res.table)} scenarios to {out_dir}")


if __name__ == "__main__":
    main()
