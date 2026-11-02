#!/usr/bin/env python
"""Part 5 fix + extras for diag_distribution.py: validate the log-logistic
PWM fit properly (the first attempt passed 1-D arrays to _loglogistic_cdf,
which expects (Nc, Y, X)); also locate empirical poles by grid row."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisk, norm

PKG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG_ROOT))
sys.path.insert(0, str(PKG_ROOT / "scripts"))
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "run_two_arms", PKG_ROOT / "scripts" / "run_two_arms.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
spec2 = importlib.util.spec_from_file_location(
    "run_arm_b_masked", PKG_ROOT / "scripts" / "run_arm_b_masked.py")
mb = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(mb)

from cdpe_sens.author_detector import detect_cdpe_author  # noqa: E402
from cdpe_sens.spei import _loglogistic_cdf, accumulate, compute_spei, thornthwaite_pet  # noqa: E402

rng = np.random.default_rng(20261005)
cfg = json.loads((PKG_ROOT / "config" / "example_config.json").read_text())
datasets = rt._arm_b_datasets(cfg)
ds = datasets["NARR"]
lat = ds.lat.astype(float)
lon = ds.lon.astype(float)
dates = ds.dates
months = dates.month.values
land, _ = mb.build_land_mask(cfg, lat, lon)
pet = thornthwaite_pet(ds.tmean, ds.lat, ds.dates)

print("== log-logistic PWM validation, ts=6, NARR calibration samples ==")
A = accumulate(ds.precip - pet, 6)
land_idx = np.argwhere(land)
sel = land_idx[rng.choice(len(land_idx), size=30, replace=False)]
shares = {-1.5: [], -1.0: [], 1.0: [], 1.5: []}
pit05, pit95, rmse_f, beta_l, n_ok = [], [], [], [], 0
for iy, ix in sel:
    for m in range(1, 13):
        idx = np.where(months == m)[0]
        cal = A[idx, iy, ix]
        cal = cal[np.isfinite(cal)]
        if len(cal) < 20:
            continue
        cs = np.sort(cal)
        F, ok = _loglogistic_cdf(cs.reshape(-1, 1, 1), cs.reshape(-1, 1, 1),
                                 np.array([[len(cal)]]))
        if not bool(ok[0, 0]):
            continue
        n_ok += 1
        F = F[:, 0, 0]
        zz = norm.ppf(np.clip(F, 1e-6, 1 - 1e-6))
        for th in shares:
            shares[th].append(float((zz <= th).mean()) if th < 0
                              else float((zz >= th).mean()))
        pit05.append(float((F < 0.05).mean()))
        pit95.append(float((F > 0.95).mean()))
        try:
            c, loc, scale = fisk.fit(cal)
            F_mle = fisk.cdf(cs, c, loc=loc, scale=scale)
            rmse_f.append(float(np.sqrt(np.mean((F - F_mle) ** 2))))
            beta_l.append(c)
        except Exception:
            pass
for th, v in shares.items():
    nom = norm.cdf(th) if th < 0 else 1 - norm.cdf(th)
    print(f"  share of cal sample beyond {th:+.1f} under F_ll: {np.mean(v):.3f} "
          f"(nominal {nom:.3f}, n={len(v)})")
print(f"  PIT: share F<0.05 {np.mean(pit05):.3f}, F>0.95 {np.mean(pit95):.3f} "
      f"(nominal 0.050 each)")
print(f"  PWM F vs scipy fisk-MLE F: RMSE mean {np.mean(rmse_f):.4f}, "
      f"max {np.max(rmse_f):.4f} (n={len(rmse_f)} fits); "
      f"fits ok in {n_ok} sampled cell-months")

print("\n== empirical pole rows, ts=6 masked (detector as run) ==")
z_emp, _ = compute_spei(ds.precip, pet, ds.dates, 6, cal_period=None,
                        dist="empirical", return_diagnostics=True)
z_ll, _ = compute_spei(ds.precip, pet, ds.dates, 6, cal_period=None,
                       dist="loglogistic", return_diagnostics=True)
for name, z in (("empirical", z_emp), ("loglogistic", z_ll)):
    f = np.where(land[None], z, np.nan)
    out = detect_cdpe_author(f, lat, lon, threshold=1.0, radius_deg=4.0)
    for side, C in (("dry", out["dry_center"]), ("wet", out["wet_center"])):
        lats = C[:, 0]
        rows = np.array([np.argmin(np.abs(lat - v)) for v in lats])
        print(f"  {name} {side}: pole in southernmost land row "
              f"{np.mean(lats <= 25.75):.2f}, in southernmost 3 rows "
              f"{np.mean(lats <= 26.75):.2f}, median pole lat "
              f"{np.nanmedian(lats):.1f}N")
print("done.")
