#!/usr/bin/env python
"""Diagnostic: why do empirical-distribution Arm B fields yield ~1/7 the
CDPE months of log-logistic fields at fixed settings?

Additive diagnostic only -- imports the package, changes nothing.
Reproduces NARR SPEI fields (full calibration, water balance = P - PET)
for timescales 1/6/12 under both distributions, validates them against
the archived scenario CSVs (masked + unmasked, theta=1.0, r=4.0), then
measures: marginal tail structure, cap/tie structure of the empirical
transform, detector pole forensics, oracle (best-centre) buffer
coherence, and pole-selection counterfactuals (random tie-break,
D-ordered tie-break, oracle pole). Also validates the log-logistic PWM
fit against a scipy MLE fit and PIT uniformity on calibration samples.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import fftconvolve
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

from cdpe_sens import io  # noqa: E402
from cdpe_sens.author_detector import buffer_mask_np, classify_month_author, detect_cdpe_author  # noqa: E402
from cdpe_sens.spei import _loglogistic_cdf, accumulate, compute_spei, thornthwaite_pet  # noqa: E402

rng = np.random.default_rng(20261005)
THR = 1.0
RAD = 4.0

cfg = json.loads((PKG_ROOT / "config" / "example_config.json").read_text())
datasets = rt._arm_b_datasets(cfg)
ds = datasets["NARR"]
lat = ds.lat.astype(float)
lon = ds.lon.astype(float)
dates = ds.dates
land, prov = mb.build_land_mask(cfg, lat, lon)
print(f"grid {len(lat)}x{len(lon)}, land cells {land.sum()} / {land.size}, "
      f"period {dates[0].date()}..{dates[-1].date()}")

pet = thornthwaite_pet(ds.tmean, ds.lat, ds.dates)

fields = {}
for ts in (1, 6, 12):
    for dist in ("loglogistic", "empirical"):
        z, dg = compute_spei(ds.precip, pet, ds.dates, ts, cal_period=None,
                             dist=dist, return_diagnostics=True)
        fields[(ts, dist)] = z
        print(f"computed ts={ts} dist={dist} "
              f"fallback={dg['loglogistic_fallback_fraction']:.3f}")

# ---------------------------------------------------------------- validation
print("\n== validation vs archived scenario CSVs (NARR, full, spei, thr=1, r=4) ==")
for run_dir, masked in (("run_armB_masked_2026-10-05", True),
                        ("run_armB_2026-10-05", False)):
    tab = pd.read_csv(PKG_ROOT / "results" / run_dir / "scenarios.csv")
    for ts in (1, 6, 12):
        for dist in ("loglogistic", "empirical"):
            z = fields[(ts, dist)]
            f = np.where(land[None], z, np.nan) if masked else z
            out = detect_cdpe_author(f, lat, lon, threshold=THR, radius_deg=RAD)
            got = int(out["cdpe"].sum())
            row = tab[(tab.dataset == "NARR") & (tab.timescale == ts)
                      & (tab.dist == dist) & (tab.cal_period == "full")
                      & (tab.water_balance == "spei") & (tab.threshold == THR)
                      & (tab.radius_deg == RAD)]
            want = int(row["n_cdpe_months"].iloc[0])
            print(f"  {'masked' if masked else 'unmasked'} ts={ts} {dist}: "
                  f"recomputed {got}, archived {want}, "
                  f"{'OK' if got == want else 'MISMATCH'}")

# ------------------------------------------------------- disk kernel helpers
CELL = 0.5
R = int(round(RAD / CELL))           # 8 cells
yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
KERNEL = ((yy ** 2 + xx ** 2) <= R * R).astype(float)   # degree-space disc


def buffer_frac_fields(field2d, thr):
    """For every centre cell: (frac of valid buffer cells <= -thr,
    frac >= +thr, na_frac of buffer). NaN where buffer has no cells."""
    valid = np.isfinite(field2d)
    dry = valid & (field2d <= -thr)
    wet = valid & (field2d >= thr)
    nv = fftconvolve(valid.astype(float), KERNEL, mode="same")
    nd = fftconvolve(dry.astype(float), KERNEL, mode="same")
    nw = fftconvolve(wet.astype(float), KERNEL, mode="same")
    tot = fftconvolve(np.ones_like(nv), KERNEL, mode="same")
    with np.errstate(invalid="ignore", divide="ignore"):
        return nd / nv, nw / nv, 1.0 - nv / tot


# ------------------------------------------------------------- part 1: marginals
print("\n== part 1: marginal structure over LAND cells (masked domain) ==")
rows = []
for ts in (1, 6, 12):
    for dist in ("loglogistic", "empirical"):
        z = np.where(land[None], fields[(ts, dist)], np.nan)
        fin = z[np.isfinite(z)]
        qs = np.quantile(fin, [0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999])
        rows.append({
            "ts": ts, "dist": dist, "sd": fin.std(),
            "q001": qs[0], "q01": qs[1], "q05": qs[2], "med": qs[3],
            "q95": qs[4], "q99": qs[5], "q999": qs[6],
            "min": fin.min(), "max": fin.max(),
            "frac<=-1.0": float((fin <= -1.0).mean()),
            "frac>=+1.0": float((fin >= 1.0).mean()),
            "frac<=-1.5": float((fin <= -1.5).mean()),
            "frac>=+1.5": float((fin >= 1.5).mean()),
        })
marg = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(marg.round(4).to_string(index=False))
print("nominal normal: P(>1.0)=0.1587, P(>1.5)=0.0668; "
      "empirical grid (n=35): 6/35=0.1714, 2/35=0.0571")

# per-month domain fraction beyond thresholds (land cells)
print("\nper-month domain fraction beyond +-1.0 over land (mean / p90 over months):")
for ts in (6,):
    for dist in ("loglogistic", "empirical"):
        z = np.where(land[None], fields[(ts, dist)], np.nan)
        fd = np.nanmean(z <= -1.0, axis=(1, 2))
        fw = np.nanmean(z >= 1.0, axis=(1, 2))
        print(f"  ts={ts} {dist}: dry {fd.mean():.3f}/{np.quantile(fd, .9):.3f}  "
              f"wet {fw.mean():.3f}/{np.quantile(fw, .9):.3f}")

# ------------------------------------------- part 2: cap saturation and ties
print("\n== part 2: cap saturation / argmin-argmax tie multiplicity (land) ==")
cap35 = norm.ppf((35 - 0.44) / (35 + 0.12))
print(f"Gringorten cap for n=35: |z|max = {cap35:.3f}")
for ts in (1, 6, 12):
    for dist in ("loglogistic", "empirical"):
        z = np.where(land[None], fields[(ts, dist)], np.nan)
        nmin_ties, nmax_ties, at_cap_lo, at_cap_hi = [], [], [], []
        for t in range(z.shape[0]):
            f = z[t]
            if not np.isfinite(f).any():
                continue
            mn, mx = np.nanmin(f), np.nanmax(f)
            nmin_ties.append(int((f == mn).sum()))
            nmax_ties.append(int((f == mx).sum()))
            at_cap_lo.append(int((f <= -cap35 + 1e-9).sum()))
            at_cap_hi.append(int((f >= cap35 - 1e-9).sum()))
        print(f"  ts={ts} {dist}: cells tied at field min: mean "
              f"{np.mean(nmin_ties):.1f} (max {np.max(nmin_ties)}); at max: "
              f"mean {np.mean(nmax_ties):.1f} (max {np.max(nmax_ties)}); "
              f"cells at/beyond +-cap35: lo {np.mean(at_cap_lo):.1f}, "
              f"hi {np.mean(at_cap_hi):.1f} per month")

# distinct z values in one representative month
z6e = np.where(land[None], fields[(6, "empirical")], np.nan)
z6l = np.where(land[None], fields[(6, "loglogistic")], np.nan)
t_demo = 200
print(f"  distinct finite z values, month {t_demo}: empirical "
      f"{len(np.unique(z6e[t_demo][np.isfinite(z6e[t_demo])]))}, loglogistic "
      f"{len(np.unique(z6l[t_demo][np.isfinite(z6l[t_demo])]))}")

# ------------------------------- part 3: detector forensics + oracle coherence
print("\n== part 3: detector forensics (masked, thr=1.0, r=4.0) ==")
for ts in (1, 6, 12):
    for dist in ("loglogistic", "empirical"):
        z = np.where(land[None], fields[(ts, dist)], np.nan)
        out = detect_cdpe_author(z, lat, lon, threshold=THR, radius_deg=RAD)
        dry_c, wet_c = out["dry_center"], out["wet_center"]
        df_, wf_ = out["drought_frac"], out["pluvial_frac"]
        dna = np.array([classify_month_author(z[t], lat, lon, THR, RAD)["dry_na_frac"]
                        for t in range(z.shape[0])])
        wna = np.array([classify_month_author(z[t], lat, lon, THR, RAD)["wet_na_frac"]
                        for t in range(z.shape[0])])
        ev = out["evaluable"]
        dry_na_fail = ev & (dna > 0.10)
        wet_na_fail = ev & (wna > 0.10)
        dry_maj_fail = ev & ~dry_na_fail & (df_ < 0.5)
        wet_maj_fail = ev & ~wet_na_fail & (wf_ < 0.5)
        dry_ok = ev & ~dry_na_fail & (df_ >= 0.5)
        wet_ok = ev & ~wet_na_fail & (wf_ >= 0.5)
        # oracle: best buffer centre per month per side (land centres, NA gate)
        o_dry, o_wet = [], []
        for t in range(z.shape[0]):
            fd, fw, na = buffer_frac_fields(z[t], THR)
            gate = (na <= 0.10) & land
            o_dry.append(np.nanmax(np.where(gate, fd, np.nan)))
            o_wet.append(np.nanmax(np.where(gate, fw, np.nan)))
        o_dry, o_wet = np.array(o_dry), np.array(o_wet)
        oracle_months = int(((o_dry >= 0.5) & (o_wet >= 0.5)).sum())
        print(f"  ts={ts} {dist}: CDPE {int(out['cdpe'].sum())} | dry ok "
              f"{int(dry_ok.sum())} (NA-gate fail {int(dry_na_fail.sum())}, "
              f"majority fail {int(dry_maj_fail.sum())}) | wet ok "
              f"{int(wet_ok.sum())} (NA-gate fail {int(wet_na_fail.sum())}, "
              f"majority fail {int(wet_maj_fail.sum())})")
        print(f"      pole lat: dry mean {np.nanmean(dry_c[:, 0]):.1f}N, "
              f"wet mean {np.nanmean(wet_c[:, 0]):.1f}N; poles in southernmost "
              f"5 rows (lat<=27.25): dry {np.mean(dry_c[:, 0] <= 27.25):.2f}, "
              f"wet {np.mean(wet_c[:, 0] <= 27.25):.2f}")
        print(f"      oracle best buffer frac: dry median {np.nanmedian(o_dry):.2f}, "
              f"wet median {np.nanmedian(o_wet):.2f}; months oracle-qualifying "
              f"both sides: {oracle_months}")

# --------------------------- part 4: pole-selection counterfactuals (ts=6)
print("\n== part 4: pole-selection counterfactuals, ts=6 masked, thr=1, r=4 ==")
from cdpe_sens.author_detector import _qualifies  # noqa: E402


def classify_custom(field2d, mode):
    f = np.where(land, field2d, np.nan)
    if not np.isfinite(f).any():
        return False
    res = {}
    for want, sgn in (("dry", -1), ("wet", +1)):
        g = np.where(np.isfinite(f), f * sgn, -np.inf)  # maximise sgn*f
        if mode == "first":
            iy, ix = np.unravel_index(int(np.argmax(g)), f.shape)
        elif mode == "random_tie":
            mx = g.max()
            cand = np.argwhere(g == mx)
            iy, ix = cand[rng.integers(len(cand))]
        elif mode == "oracle":
            fd, fw, na = buffer_frac_fields(f, THR)
            bf = fd if want == "dry" else fw
            score = np.where((na <= 0.10) & land, bf, -np.inf)
            iy, ix = np.unravel_index(int(np.argmax(score)), f.shape)
        buf = buffer_mask_np(lat, lon, float(lat[iy]), float(lon[ix]), RAD)
        ok, _, _ = _qualifies(f[buf], want, THR, 0.5, 0.10)
        res[want] = ok
    return res["dry"] and res["wet"]


for dist in ("empirical", "loglogistic"):
    z = fields[(6, dist)]
    for mode in ("first", "random_tie", "oracle"):
        n = sum(classify_custom(z[t], mode) for t in range(z.shape[0]))
        print(f"  {dist} pole mode={mode}: CDPE months {n}")

# D-ordered tie-break for empirical: among cap-tied cells pick min/max raw D
D6 = accumulate(ds.precip - pet, 6)
z = np.where(land[None], fields[(6, "empirical")], np.nan)
cnt = 0
for t in range(z.shape[0]):
    f = z[t]
    if not np.isfinite(f).any():
        continue
    oks = []
    for want, sgn in (("dry", -1), ("wet", +1)):
        g = np.where(np.isfinite(f), f * sgn, -np.inf)
        mx = g.max()
        cand = np.argwhere(g == mx)
        if len(cand) > 1:      # break tie by the underlying accumulated D
            dvals = np.array([D6[t][iy, ix] * sgn for iy, ix in cand])
            iy, ix = cand[int(np.argmax(dvals))]
        else:
            iy, ix = cand[0]
        buf = buffer_mask_np(lat, lon, float(lat[iy]), float(lon[ix]), RAD)
        ok, _, _ = _qualifies(f[buf], want, THR, 0.5, 0.10)
        oks.append(ok)
    cnt += bool(oks[0] and oks[1])
print(f"  empirical pole mode=D-ordered tie-break: CDPE months {cnt}")

# --------------------------- part 5: log-logistic fit validation (ts=6)
print("\n== part 5: log-logistic PWM fit validation on calibration samples ==")
A = accumulate(ds.precip - pet, 6)
months = dates.month.values
land_idx = np.argwhere(land)
sel = land_idx[rng.choice(len(land_idx), size=30, replace=False)]
pit_fracs = {-1.5: [], -1.0: [], 1.0: [], 1.5: []}
f_rmse, param_rows = [], []
for iy, ix in sel:
    for m in range(1, 13):
        idx = np.where(months == m)[0]
        cal = A[idx, iy, ix]
        cal = cal[np.isfinite(cal)]
        if len(cal) < 20:
            continue
        cs = np.sort(cal)
        F, ok = _loglogistic_cdf(cs, cs, np.array([len(cal)]))
        F = F[:, 0, 0]
        if not ok[0, 0]:
            continue
        zz = norm.ppf(np.clip(F, 1e-6, 1 - 1e-6))
        for th in pit_fracs:
            pit_fracs[th].append(float((zz <= th).mean()) if th < 0
                                 else float((zz >= th).mean()))
        # scipy MLE fit of 3-param log-logistic (fisk: shape=beta, scale=alpha, loc=gam)
        try:
            c, loc, scale = fisk.fit(cal)
            F_mle = fisk.cdf(cs, c, loc=loc, scale=scale)
            f_rmse.append(float(np.sqrt(np.mean((F - F_mle) ** 2))))
            param_rows.append((c, loc, scale))
        except Exception:
            pass
for th, v in pit_fracs.items():
    nom = norm.cdf(th) if th < 0 else 1 - norm.cdf(th)
    print(f"  share of CALIBRATION sample beyond {th:+.1f} under F_ll: "
          f"{np.mean(v):.3f} (nominal {nom:.3f}, n={len(v)} cell-months)")
print(f"  F_ll vs scipy-MLE F: RMSE mean {np.mean(f_rmse):.4f} "
      f"(n={len(f_rmse)} fits)")

# --------------------------- part 6: D ties in calibration samples
print("\n== part 6: ties in accumulated water-balance calibration samples ==")
for ts in (1, 6, 12):
    A_ts = accumulate(ds.precip - pet, ts)
    tie_fracs = []
    for iy, ix in sel:
        for m in (1, 4, 7, 10):
            idx = np.where(months == m)[0]
            cal = A_ts[idx, iy, ix]
            cal = cal[np.isfinite(cal)]
            tie_fracs.append(1.0 - len(np.unique(cal)) / max(1, len(cal)))
    print(f"  ts={ts}: mean tied fraction of cal sample "
          f"{np.mean(tie_fracs):.4f} over {len(tie_fracs)} cell-months")
print("\ndone.")
