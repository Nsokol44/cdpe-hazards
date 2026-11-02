#!/usr/bin/env python
"""Resolve the PWM-vs-MLE discrepancy from diag part 5: print both fits'
parameters and PIT behaviour on identical calibration samples."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.special import gamma as _gamma
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

from cdpe_sens.spei import _loglogistic_cdf, accumulate, thornthwaite_pet  # noqa: E402

rng = np.random.default_rng(20261005)
cfg = json.loads((PKG_ROOT / "config" / "example_config.json").read_text())
ds = rt._arm_b_datasets(cfg)["NARR"]
dates = ds.dates
months = dates.month.values
land, _ = mb.build_land_mask(cfg, ds.lat.astype(float), ds.lon.astype(float))
pet = thornthwaite_pet(ds.tmean, ds.lat, ds.dates)
A = accumulate(ds.precip - pet, 6)
land_idx = np.argwhere(land)
sel = land_idx[rng.choice(len(land_idx), size=30, replace=False)]

mle_share = {1.0: [], 1.5: []}
shown = 0
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
        F = F[:, 0, 0]
        # recover the package's fitted parameters from F at the sample:
        # refit by hand following spei.py algebra to print params
        n = len(cs)
        Fi = (np.arange(1, n + 1) - 0.35) / n
        w0 = cs.mean()
        w1 = ((1 - Fi) * cs).mean()
        w2 = ((1 - Fi) ** 2 * cs).mean()
        beta = (2 * w1 - w0) / (6 * w1 - w0 - 6 * w2)
        alpha = (w0 - 2 * w1) * beta / (_gamma(1 + 1 / beta) * _gamma(1 - 1 / beta))
        gam = w0 - alpha * _gamma(1 + 1 / beta) * _gamma(1 - 1 / beta)
        try:
            c, loc, scale = fisk.fit(cal)
        except Exception:
            continue
        F_mle = fisk.cdf(cs, c, loc=loc, scale=scale)
        z_mle = norm.ppf(np.clip(F_mle, 1e-6, 1 - 1e-6))
        mle_share[1.0].append(float((z_mle >= 1.0).mean()))
        mle_share[1.5].append(float((z_mle >= 1.5).mean()))
        if shown < 5:
            print(f"cell ({iy},{ix}) month {m}: n={n} sample range "
                  f"[{cs[0]:.1f},{cs[-1]:.1f}]")
            print(f"  PWM (package): beta={beta:.3f} alpha={alpha:.2f} gamma={gam:.2f}")
            print(f"  MLE (scipy)  : c={c:.3f} scale={scale:.2f} loc={loc:.2f} "
                  f"(loc<=min? {loc <= cs[0]})")
            print(f"  max|F_pwm - F_mle| = {np.max(np.abs(F - F_mle)):.3f}; "
                  f"F at sample median: pwm {F[n//2]:.3f} mle {F_mle[n//2]:.3f}")
            shown += 1
print(f"\nMLE PIT on cal samples: share beyond +1.0 = {np.mean(mle_share[1.0]):.3f} "
      f"(nominal 0.159), beyond +1.5 = {np.mean(mle_share[1.5]):.3f} "
      f"(nominal 0.067), n={len(mle_share[1.0])}")
print("compare package PWM PIT (part 5): beyond +1.0 = 0.193, +1.5 = 0.079")
