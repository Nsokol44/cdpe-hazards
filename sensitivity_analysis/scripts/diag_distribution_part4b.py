#!/usr/bin/env python
"""Seed robustness for the random-tie-break counterfactual (diag part 4):
empirical ts=6 masked fields, 5 independent seeds."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

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

from cdpe_sens.author_detector import _qualifies, buffer_mask_np  # noqa: E402
from cdpe_sens.spei import compute_spei, thornthwaite_pet  # noqa: E402

cfg = json.loads((PKG_ROOT / "config" / "example_config.json").read_text())
ds = rt._arm_b_datasets(cfg)["NARR"]
lat = ds.lat.astype(float)
lon = ds.lon.astype(float)
land, _ = mb.build_land_mask(cfg, lat, lon)
pet = thornthwaite_pet(ds.tmean, ds.lat, ds.dates)
z, _ = compute_spei(ds.precip, pet, ds.dates, 6, cal_period=None,
                    dist="empirical", return_diagnostics=True)
z = np.where(land[None], z, np.nan)


def count_random(seed):
    rng = np.random.default_rng(seed)
    n = 0
    for t in range(z.shape[0]):
        f = z[t]
        if not np.isfinite(f).any():
            continue
        oks = []
        for want, sgn in (("dry", -1), ("wet", +1)):
            g = np.where(np.isfinite(f), f * sgn, -np.inf)
            cand = np.argwhere(g == g.max())
            iy, ix = cand[rng.integers(len(cand))]
            buf = buffer_mask_np(lat, lon, float(lat[iy]), float(lon[ix]), 4.0)
            ok, _, _ = _qualifies(f[buf], want, 1.0, 0.5, 0.10)
            oks.append(ok)
        n += bool(oks[0] and oks[1])
    return n


counts = [count_random(s) for s in (1, 7, 42, 123, 20261005)]
print("random tie-break CDPE months by seed:", counts)
print(f"mean {np.mean(counts):.1f}, range {min(counts)}-{max(counts)} "
      f"(first-occurrence as run: 6; log-logistic as run: 44)")
