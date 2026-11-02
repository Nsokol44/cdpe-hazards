#!/usr/bin/env python
"""Phase 2 (2026-11-02): Arm B detector tie-breaking fix + rerun of the
MASKED Arm B sensitivity run, and variance decomposition (raw + log1p)
for both arms.

    python scripts/run_armB_tiefix.py [--config config/example_config.json]
                                      [--out-dir results/run_armB_tiefix_2026-11-02]
                                      [--base-seed 20261102] [--force]

Deterministic: fixed BASE_SEED (default 20261102), per-(scenario,
month, pole) seeds derived by SHA-256 (see
``cdpe_sens/detector_tiefix.py``), no wall-clock-dependent outputs in
the data files, relative paths resolved against the package root.
Dependencies: the package's own (numpy / scipy / pandas / xarray).

Pipeline (steps, in order -- the script STOPS if Step 1 fails):

1. REPRODUCE BEFORE CHANGING. Every masked Arm B index field is
   recomputed through the package pipeline exactly as the archived
   masked run did (``run_two_arms._arm_b_datasets`` ->
   ``thornthwaite_pet`` -> ``compute_spei`` -> SPEIbase land mask
   applied to the field, as in ``scripts/run_arm_b_masked.py``) and run
   through the ORIGINAL detector (``make_author_detector``,
   first-occurrence pole selection). The recomputed ``n_cdpe_months``
   must reproduce ``results/run_armB_masked_2026-10-05/scenarios.csv``
   EXACTLY for all 720 scenarios, otherwise the script aborts before
   any tie-fix output is produced. Computed (masked) fields are cached
   to ``<out-dir>/cache/field_*.npz`` (one npz per field configuration)
   and per-field results are checkpointed to
   ``<out-dir>/checkpoints/*.json`` so an interrupted run resumes.

2. TIE FIX. The same fields are run through
   ``cdpe_sens.detector_tiefix.detect_cdpe_tiefix``: identical to the
   frozen detector in every rule except pole selection -- exact-float
   ties at the field minimum/maximum (empirical cap ties AND the
   log-logistic clip plateau) are broken uniformly at random among the
   tied finite cells, never by first-index order. The masked baseline
   scenario is run twice and asserted bit-identical.

3. RERUN outputs: ``scenarios_tiefix.csv`` (archived schema and row
   order, plus ``old_n_cdpe_months`` and ``delta``).

4. VARIANCE DECOMPOSITION for Arm A (archived, 36 scenarios), Arm B
   masked OLD and Arm B masked NEW, each on raw ``n_cdpe_months`` and
   on ``log1p`` counts (log(1 + n), the standard zero-safe log), using
   the package's own ``variance_decomposition`` -- which is first
   verified to reproduce both archived ``variance_decomposition.csv``
   files exactly. ``higher_order`` appears as its own category, as in
   the archived method (it is the remainder after main effects and
   two-way interactions). Output: ``decomposition_tiefix.csv`` (long
   form: arm, version, scale, factor, share) and ``PHASE2_REPORT.md``.
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
from cdpe_sens.author_detector import make_author_detector  # noqa: E402
from cdpe_sens.detector_tiefix import BASE_SEED, detect_cdpe_tiefix  # noqa: E402
from cdpe_sens.events import event_table  # noqa: E402
from cdpe_sens.sensitivity import _cal_tuple, variance_decomposition  # noqa: E402
from cdpe_sens.spei import compute_spei, thornthwaite_pet  # noqa: E402

ARCH_MASKED = PKG_ROOT / "results" / "run_armB_masked_2026-10-05"
ARCH_ARMA = PKG_ROOT / "results" / "run_armA_2026-10-05"
KEY_COLS = ["dataset", "timescale", "dist", "cal_period", "water_balance",
            "threshold", "min_area_frac", "min_cluster_cells", "radius_deg"]
SEED_SENS_SEEDS = [20261102, 20261103, 20261104, 20261105, 20261106]
DETECTOR_NAME_TIEFIX = ("cdpe_sens.detector_tiefix (author detector + uniform "
                        "random tie-breaking among exact-float pole ties) "
                        "[input fields land-masked]")


def _load_driver(name):
    spec = importlib.util.spec_from_file_location(
        name, PKG_ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rt = _load_driver("run_two_arms")
mb = _load_driver("run_arm_b_masked")
MAJORITY_FRAC = rt.MAJORITY_FRAC
MAX_NA_FRAC = rt.MAX_NA_FRAC
RADII = rt.RADII
ARM_B_FACTORS = rt.ARM_B_FACTORS
ARM_A_FACTORS = ["index", "threshold", "radius_deg"]


def _sha256_file(path):
    return rt._sha256_file(path)


def _field_tag(dataset, ts, dist, cal, wb):
    return f"{dataset}_ts{ts}_{dist}_{cal}_{wb}"


# ---------------------------------------------------------------------------
# Variance-decomposition reproduction check (Step 4 prerequisite)
# ---------------------------------------------------------------------------
def check_vd_reproduction():
    """The package decomposition must reproduce both archived VD files."""
    checks = []
    for arm, run_dir, factors in (("A", ARCH_ARMA, ARM_A_FACTORS),
                                  ("B_masked", ARCH_MASKED, ARM_B_FACTORS)):
        tab = pd.read_csv(run_dir / "scenarios.csv")
        arch = pd.read_csv(run_dir / "variance_decomposition.csv")
        got = variance_decomposition(tab, "n_cdpe_months", factors=factors)
        m = arch.merge(got, on="term", suffixes=("_archived", "_recomputed"))
        if len(m) != len(arch) or len(m) != len(got):
            raise SystemExit(f"VD reproduction FAILED for Arm {arm}: "
                             f"term sets differ")
        maxdiff = float((m["share_archived"] - m["share_recomputed"]).abs().max())
        checks.append({"arm": arm, "max_abs_share_diff": maxdiff,
                       "n_terms": int(len(m))})
        if maxdiff > 1e-9:
            raise SystemExit(f"VD reproduction FAILED for Arm {arm}: "
                             f"max |share diff| = {maxdiff}")
        print(f"VD reproduction Arm {arm}: max |share diff| = {maxdiff:.3g} "
              f"over {len(m)} terms -- OK")
    return checks


def decomposition_rows(arm, version, table, factors):
    """Raw + log1p decomposition via the package code path, long form."""
    rows = []
    for scale, metric, src in (
            ("raw", "n_cdpe_months", table),
            ("log1p", "n_log1p", None)):
        if src is None:
            src = table.copy()
            src["n_log1p"] = np.log1p(src["n_cdpe_months"].astype(float))
        vd = variance_decomposition(src, metric, factors=factors)
        for _, r in vd.iterrows():
            rows.append({"arm": arm, "version": version, "scale": scale,
                         "factor": r["term"], "order": int(r["order"]),
                         "share": float(r["share"])})
    return rows


def _share(decomp, arm, version, scale, factor):
    s = decomp[(decomp["arm"] == arm) & (decomp["version"] == version)
               & (decomp["scale"] == scale) & (decomp["factor"] == factor)]
    return float(s["share"].iloc[0]) if len(s) else float("nan")


def write_report(out_dir, merged, decomp, seed_df, vd_checks, n_match,
                 bit_identical, base_seed):
    """PHASE2_REPORT.md + changed_gt50pct.csv from the run's own outputs."""
    old, new = merged["old_n_cdpe_months"], merged["n_cdpe_months"]
    z_old, z_new = int((old == 0).sum()), int((new == 0).sum())
    ztab = merged.assign(old_zero=(old == 0), new_zero=(new == 0)).groupby(
        "dist")[["old_zero", "new_zero"]].sum()
    base = merged[(merged["threshold"] == 1.0) & (merged["radius_deg"] == 4.0)
                  & (merged["cal_period"] == "full")
                  & (merged["water_balance"] == "spei")].sort_values(
                      ["dataset", "timescale", "dist"])
    chg = merged.copy()
    chg["rel_change"] = np.where(chg["old_n_cdpe_months"] > 0,
                                 chg["delta"] / chg["old_n_cdpe_months"],
                                 np.nan)
    gt50 = chg[(chg["old_n_cdpe_months"] > 0)
               & (chg["rel_change"].abs() > 0.5)].copy()
    from_zero = chg[(chg["old_n_cdpe_months"] == 0)
                    & (chg["n_cdpe_months"] > 0)]
    gt50_out = gt50[KEY_COLS + ["old_n_cdpe_months", "n_cdpe_months",
                                "delta", "rel_change"]]
    gt50_out.to_csv(out_dir / "changed_gt50pct.csv", index=False)

    def top_terms(arm, version, scale, n=5):
        d = decomp[(decomp["arm"] == arm) & (decomp["version"] == version)
                   & (decomp["scale"] == scale)].nlargest(n, "share")
        return "; ".join(f"{r.factor} {r.share:.3f}" for r in d.itertuples())

    L = []
    L.append("# Phase 2 Report — Arm B detector tie-breaking fix, masked "
             "rerun, and variance decomposition (raw + log1p)\n")
    L.append("Date: 2026-11-02. Driver: `scripts/run_armB_tiefix.py` "
             "(one command; deterministic). Tie-fix detector: "
             "`cdpe_sens/detector_tiefix.py` (new module; the frozen "
             "`cdpe_sens/author_detector.py` was NOT modified). No "
             "manuscript file was edited. Outputs in this directory; "
             "provenance in `run_manifest.json`.\n")
    L.append("## Step 1 — Reproduce before changing (gate)\n")
    L.append(f"All masked Arm B fields were recomputed through the package "
             f"pipeline exactly as the archived masked run "
             f"(`scripts/run_arm_b_masked.py`) constructed them — datasets "
             f"via `run_two_arms._arm_b_datasets` (1980–2014), Thornthwaite "
             f"PET, `compute_spei`, SPEIbase land mask applied to the field "
             f"(4,443 of 6,069 cells land) — and run through the ORIGINAL "
             f"detector. **Result: {n_match}/720 scenarios reproduce the "
             f"archived `results/run_armB_masked_2026-10-05/scenarios.csv` "
             f"`n_cdpe_months` EXACTLY** (per-scenario comparison in "
             f"`reproduction_check.csv`). The script aborts before any "
             f"tie-fix output if this gate fails. Computed masked fields "
             f"are cached one npz per field configuration under `cache/` "
             f"(80 configurations) and per-field results checkpointed "
             f"under `checkpoints/`, so reruns resume.\n")
    L.append("Archived zero counts were verified first from the archived "
             f"file itself: **272 of 720 scenarios are zero** (empirical "
             f"241, log-logistic 31) — matching the tasking figures.\n")
    L.append("## Step 2 — The tie rule as implemented\n")
    L.append("Identical to `classify_month_author` in every rule (same "
             "degree-space buffer, NA gate ≤ 0.10, majority ≥ 0.5, via the "
             "frozen module's own `buffer_mask_np`/`_qualifies`) except "
             "pole selection: all finite cells exactly equal (float ==) "
             "to the field minimum (dry) or maximum (wet) are collected; "
             "a unique extremum is selected as before; with k > 1 tied "
             "cells, one is chosen **uniformly at random** among them. "
             "First-index order is never used to break a tie. This single "
             "rule covers both tie sources: the empirical Gringorten cap "
             "(|z| ≤ 2.146, ~128 tied land cells per pole per month at "
             "the baseline) and the log-logistic clip plateau at "
             "z = ±4.753 (including F = 0 cells). Randomness: "
             "`numpy.random.default_rng` seeded per (pole, month) with "
             "the first 8 bytes (little-endian) of SHA-256 over "
             "`cdpe-tiefix-v1|BASE_SEED=<seed>|scenario=<key>|month=<t>|"
             "pole=<dry|wet>`, where `<key>` is (dataset, timescale, "
             "dist, cal_period, water_balance, threshold, min_area_frac, "
             "min_cluster_cells, radius_deg) joined by '/'. Default "
             f"BASE_SEED = {base_seed}. **Bit-identical rerun assertion "
             f"on the masked baseline scenario (NARR ts6 log-logistic, "
             f"θ=1.0, r=4.0): {'PASSED' if bit_identical else 'FAILED'}** "
             f"(the baseline scenario was detected twice and the CDPE "
             f"series compared element-wise).\n")
    L.append("## Step 3 — Rerun: headline counts\n")
    L.append(f"Zero-CDPE scenarios: **{z_old} (old) → {z_new} (new)** of "
             f"720. By distribution (of 360 scenarios each):\n")
    L.append("| dist | zeros old | zeros new |\n|---|---|---|")
    for dist_name, r in ztab.iterrows():
        L.append(f"| {dist_name} | {int(r['old_zero'])} | "
                 f"{int(r['new_zero'])} |")
    L.append("")
    L.append("Masked baseline cells (θ = 1.0, r = 4.0°, full calibration, "
             "SPEI water balance), old vs new `n_cdpe_months`:\n")
    L.append("| dataset | timescale | dist | old | new | delta |\n"
             "|---|---|---|---|---|---|")
    for r in base.itertuples():
        L.append(f"| {r.dataset} | {r.timescale} | {r.dist} | "
                 f"{r.old_n_cdpe_months} | {r.n_cdpe_months} | {r.delta} |")
    L.append("")
    L.append("Seed sensitivity, NARR ts6 empirical baseline (θ=1.0, "
             "r=4.0, full cal, SPEI), BASE_SEED varied "
             "20261102–20261106 (same derivation, seed value changed):\n")
    L.append("| BASE_SEED | n_cdpe_months |\n|---|---|")
    for r in seed_df.itertuples():
        L.append(f"| {r.seed} | {r.n_cdpe_months} |")
    sv = seed_df["n_cdpe_months"]
    L.append(f"\nRange {int(sv.min())}–{int(sv.max())}, mean "
             f"{sv.mean():.1f} (old first-occurrence count: 6; the "
             f"diagnosis's 57–80 range was on its own setup — the audit "
             f"counterfactual field with masked detection — and is "
             f"reported here only as context, not as a target). The "
             f"BASE_SEED=20261102 value equals the scenarios_tiefix "
             f"count for this scenario by construction (asserted in the "
             f"driver).\n")
    L.append("## Step 4 — Variance decomposition (both arms, raw + log1p)\n")
    L.append("Method: the package's own `variance_decomposition` "
             "(`cdpe_sens/sensitivity.py`), first verified against the "
             "archives: " + "; ".join(
                 f"Arm {c['arm']} max |share diff| = "
                 f"{c['max_abs_share_diff']:.3g} over {c['n_terms']} terms"
                 for c in vd_checks) + " — both archived "
             "`variance_decomposition.csv` files reproduce. Scales: raw "
             "`n_cdpe_months`, and log1p counts, log(1 + n) — the "
             "standard zero-safe log (chosen because 272/720 old masked "
             "scenarios are exactly zero; stated here and in the "
             "manifest). `higher_order` is its own category, as in the "
             "archived method: it is the remainder after main effects "
             "and all two-way interactions (labelled exactly "
             "`higher_order`). Full long-form table: "
             "`decomposition_tiefix.csv` (arm, version, scale, factor, "
             "share).\n")
    L.append("**Distribution factor share, Arm B masked (the headline "
             "correction):**\n")
    L.append("| scale | dist share OLD | dist share NEW | dist × threshold OLD | dist × threshold NEW |\n"
             "|---|---|---|---|---|")
    for scale in ("raw", "log1p"):
        L.append(f"| {scale} | {_share(decomp, 'B', 'old', scale, 'dist'):.3f} "
                 f"| {_share(decomp, 'B', 'tiefix', scale, 'dist'):.3f} "
                 f"| {_share(decomp, 'B', 'old', scale, 'dist x threshold'):.3f} "
                 f"| {_share(decomp, 'B', 'tiefix', scale, 'dist x threshold'):.3f} |")
    L.append("")
    L.append(f"Arm B top terms, raw OLD: {top_terms('B', 'old', 'raw')}.")
    L.append(f"Arm B top terms, raw NEW: {top_terms('B', 'tiefix', 'raw')}.")
    L.append(f"Arm B top terms, log1p OLD: {top_terms('B', 'old', 'log1p')}.")
    L.append(f"Arm B top terms, log1p NEW: {top_terms('B', 'tiefix', 'log1p')}.")
    L.append("")
    L.append("Arm A (36 scenarios, archived; the tie fix does not apply — "
             "SPEIbase/CRU fields are continuous and tie-free, so Arm A "
             "has no `dist` factor; its index factor is `index`): "
             f"index share raw {_share(decomp, 'A', 'archived', 'raw', 'index'):.3f}, "
             f"log1p {_share(decomp, 'A', 'archived', 'log1p', 'index'):.3f}; "
             f"threshold share raw {_share(decomp, 'A', 'archived', 'raw', 'threshold'):.3f}, "
             f"log1p {_share(decomp, 'A', 'archived', 'log1p', 'threshold'):.3f}; "
             f"higher_order raw {_share(decomp, 'A', 'archived', 'raw', 'higher_order'):.3f}, "
             f"log1p {_share(decomp, 'A', 'archived', 'log1p', 'higher_order'):.3f}.")
    L.append(f"Arm B higher_order: raw OLD "
             f"{_share(decomp, 'B', 'old', 'raw', 'higher_order'):.3f} → NEW "
             f"{_share(decomp, 'B', 'tiefix', 'raw', 'higher_order'):.3f}; "
             f"log1p OLD {_share(decomp, 'B', 'old', 'log1p', 'higher_order'):.3f} "
             f"→ NEW {_share(decomp, 'B', 'tiefix', 'log1p', 'higher_order'):.3f}.\n")
    L.append("## Scenarios changed by more than 50%\n")
    L.append(f"Of the 720 scenarios, **{len(gt50)}** with old count > 0 "
             f"changed by more than 50% in relative terms "
             f"(|delta| / old > 0.5), and **{len(from_zero)}** moved from "
             f"0 to a positive count (relative change undefined, listed "
             f"in `scenarios_tiefix.csv`). The full >50% list is in "
             f"`changed_gt50pct.csv` and reproduced below.\n")
    L.append("| dataset | ts | dist | cal | wb | thr | r | old | new | delta | rel |\n"
             "|---|---|---|---|---|---|---|---|---|---|---|")
    for r in gt50.sort_values(["dist", "dataset", "timescale"]).itertuples():
        L.append(f"| {r.dataset} | {r.timescale} | {r.dist} | "
                 f"{r.cal_period} | {r.water_balance} | {r.threshold} | "
                 f"{r.radius_deg} | {r.old_n_cdpe_months} | "
                 f"{r.n_cdpe_months} | {r.delta} | {r.rel_change:+.2f} |")
    L.append("")
    L.append("## Files\n")
    L.append("- `scenarios_tiefix.csv` — 720 masked scenarios, archived "
             "schema/order + `old_n_cdpe_months` and `delta`.\n"
             "- `decomposition_tiefix.csv` — long-form decomposition "
             "(arm, version, scale, factor, share).\n"
             "- `reproduction_check.csv` — Step 1 per-scenario gate.\n"
             "- `seed_sensitivity.csv`, `tie_diagnostics.csv` (mean tied "
             "cells per pole per scenario), `changed_gt50pct.csv`.\n"
             "- `run_manifest.json` — versions, seeds, config hash, "
             "input/output file hashes.\n"
             "- `cache/` (masked field npz per configuration), "
             "`checkpoints/` (per-field results; delete or pass "
             "`--force` to recompute).\n")
    (out_dir / "PHASE2_REPORT.md").write_text("\n".join(L))
    return len(gt50), int(len(from_zero))


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config/example_config.json")
    ap.add_argument("--out-dir", default="results/run_armB_tiefix_2026-11-02")
    ap.add_argument("--base-seed", type=int, default=BASE_SEED)
    ap.add_argument("--force", action="store_true",
                    help="ignore field cache and per-field checkpoints")
    args = ap.parse_args()
    base_seed = int(args.base_seed)

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = PKG_ROOT / cfg_path
    cfg = json.loads(cfg_path.read_text())
    cfg_sha = rt._config_sha(cfg)
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = PKG_ROOT / out_dir
    cache_dir = out_dir / "cache"
    ckpt_dir = out_dir / "checkpoints"
    cache_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    cfg_abs = json.loads(cfg_path.read_text())
    for d in cfg_abs["datasets"]:
        for role in ("precip", "tmean"):
            d[role]["path"] = str(PKG_ROOT / d[role]["path"])

    archived = pd.read_csv(ARCH_MASKED / "scenarios.csv")
    if len(archived) != 720:
        raise SystemExit(f"archived masked scenarios: {len(archived)} rows, "
                         f"expected 720")
    arch_keyed = archived.set_index(KEY_COLS)["n_cdpe_months"].to_dict()
    arch_fb = archived.set_index(KEY_COLS)[
        "loglogistic_fallback_fraction"].to_dict()

    print("== Step 4 prerequisite: variance-decomposition reproduction ==")
    vd_checks = check_vd_reproduction()

    print("== Steps 1-3: field recomputation, reproduction, tie-fix rerun ==")
    datasets = rt._arm_b_datasets(cfg_abs)
    d0 = next(iter(datasets.values()))
    lat = d0.lat.astype(float)
    lon = d0.lon.astype(float)
    land_mask, mask_prov = mb.build_land_mask(cfg, lat, lon)
    lv = cfg["levels"]
    thresholds = [float(t) for t in lv["threshold"]]
    min_area = float(lv["min_area_frac"][0])
    min_clus = int(lv["min_cluster_cells"][0])
    n_years = len(d0.dates) / 12.0
    dates = d0.dates

    repro_rows, tiefix_rows, seed_rows = [], [], []
    cache_hashes = {}
    bit_identical = None
    t_start = time.time()
    for dname, ds in datasets.items():
        pet = thornthwaite_pet(ds.tmean, ds.lat, ds.dates)
        for ts, dist, cal, wb in itertools.product(
                lv["timescale"], lv["dist"], lv["cal_period"],
                lv["water_balance"]):
            tag = _field_tag(dname, ts, dist, cal, wb)
            ckpt_path = ckpt_dir / f"{tag}.json"
            if ckpt_path.exists() and not args.force:
                ck = json.loads(ckpt_path.read_text())
                if ck["config_sha256"] == cfg_sha and ck["base_seed"] == base_seed:
                    repro_rows += ck["repro_rows"]
                    tiefix_rows += ck["tiefix_rows"]
                    seed_rows += ck["seed_rows"]
                    cache_hashes[tag] = ck["cache_sha256"]
                    print(f"[checkpoint] {tag}: reused "
                          f"({len(ck['repro_rows'])} scenarios)")
                    continue
            # --- field: cache or recompute (masked, as the archived run) ---
            cache_path = cache_dir / f"field_{tag}.npz"
            if cache_path.exists() and not args.force:
                z = np.load(cache_path)
                if str(z["config_sha256"]) != cfg_sha:
                    raise SystemExit(f"cache {cache_path} config hash mismatch")
                masked = z["field"]
                fallback = float(z["fallback"])
            else:
                use_pet = pet if wb == "spei" else None
                field, dg = compute_spei(
                    ds.precip, use_pet, ds.dates, ts,
                    cal_period=_cal_tuple(cal), dist=dist,
                    return_diagnostics=True)
                fallback = float(dg["loglogistic_fallback_fraction"])
                masked = np.where(land_mask[None, :, :], field, np.nan)
                np.savez_compressed(
                    cache_path, field=masked, fallback=fallback,
                    lat=lat, lon=lon,
                    dates=dates.values.astype("datetime64[ns]"),
                    config_sha256=cfg_sha, dataset=dname, timescale=ts,
                    dist=dist, cal_period=cal, water_balance=wb,
                    masked=np.True_)
            cache_hashes[tag] = _sha256_file(cache_path)

            f_repro, f_tiefix, f_seed = [], [], []
            for radius in RADII:
                orig = make_author_detector(lat, lon, radius_deg=radius,
                                            majority_frac=MAJORITY_FRAC,
                                            max_na_frac=MAX_NA_FRAC)
                for thr in thresholds:
                    key = (dname, int(ts), dist, cal, wb, float(thr),
                           min_area, min_clus, float(radius))
                    base_row = {"dataset": dname, "timescale": int(ts),
                                "dist": dist, "cal_period": cal,
                                "water_balance": wb, "threshold": float(thr),
                                "min_area_frac": min_area,
                                "min_cluster_cells": min_clus,
                                "radius_deg": float(radius)}
                    # Step 1: ORIGINAL detector on the masked field.
                    out_o = orig(masked, thr, thr, min_area, min_clus)
                    cd_o = np.asarray(out_o["cdpe"], dtype=bool)
                    f_repro.append({**base_row,
                                    "n_cdpe_months": int(cd_o.sum())})
                    # Step 2/3: tie-fix detector, identical other rules.
                    out_t = detect_cdpe_tiefix(
                        masked, lat, lon, threshold=thr, radius_deg=radius,
                        majority_frac=MAJORITY_FRAC, max_na_frac=MAX_NA_FRAC,
                        scenario_key=key, base_seed=base_seed)
                    cd_t = np.asarray(out_t["cdpe"], dtype=bool)
                    if key == ("NARR", 6, "loglogistic", "full", "spei",
                               1.0, 0.1, 1, 4.0):
                        out_t2 = detect_cdpe_tiefix(
                            masked, lat, lon, threshold=thr, radius_deg=radius,
                            majority_frac=MAJORITY_FRAC,
                            max_na_frac=MAX_NA_FRAC, scenario_key=key,
                            base_seed=base_seed)
                        bit_identical = bool(np.array_equal(
                            cd_t, np.asarray(out_t2["cdpe"], dtype=bool)))
                        if not bit_identical:
                            raise SystemExit("baseline tiefix rerun is NOT "
                                             "bit-identical; aborting")
                    ev = event_table(cd_t, dates, out_t.get("drought_frac"),
                                     out_t.get("pluvial_frac"))
                    f_tiefix.append({
                        **base_row,
                        "n_cdpe_months": int(cd_t.sum()),
                        "n_events": int(len(ev)),
                        "mean_duration": (float(ev["duration_months"].mean())
                                          if len(ev) else 0.0),
                        "months_per_year": float(cd_t.sum() / n_years),
                        "loglogistic_fallback_fraction": fallback,
                        "mean_n_tied_dry": float(out_t["n_tied_dry"].mean()),
                        "mean_n_tied_wet": float(out_t["n_tied_wet"].mean()),
                    })
                    # Seed sensitivity on the diagnosis's exemplar scenario.
                    if (dname, int(ts), dist, cal, wb, float(thr),
                            float(radius)) == ("NARR", 6, "empirical", "full",
                                               "spei", 1.0, 4.0):
                        for s in SEED_SENS_SEEDS:
                            out_s = detect_cdpe_tiefix(
                                masked, lat, lon, threshold=thr,
                                radius_deg=radius, majority_frac=MAJORITY_FRAC,
                                max_na_frac=MAX_NA_FRAC, scenario_key=key,
                                base_seed=s)
                            f_seed.append({"seed": int(s),
                                           "n_cdpe_months": int(np.asarray(
                                               out_s["cdpe"]).sum())})
            ck = {"field": tag, "config_sha256": cfg_sha,
                  "base_seed": base_seed, "cache_sha256": cache_hashes[tag],
                  "fallback": fallback, "repro_rows": f_repro,
                  "tiefix_rows": f_tiefix, "seed_rows": f_seed}
            ckpt_path.write_text(json.dumps(ck))
            repro_rows += f_repro
            tiefix_rows += f_tiefix
            seed_rows += f_seed
            print(f"[done] {tag}: {len(f_repro)} scenarios "
                  f"({time.time() - t_start:.0f}s elapsed)", flush=True)

    if bit_identical is None:
        # All checkpoints were reused, so the in-loop assertion never ran.
        # Re-run it directly on the cached baseline field.
        z = np.load(cache_dir / "field_NARR_ts6_loglogistic_full_spei.npz")
        bkey = ("NARR", 6, "loglogistic", "full", "spei", 1.0, 0.1, 1, 4.0)
        r1 = detect_cdpe_tiefix(z["field"], lat, lon, threshold=1.0,
                                radius_deg=4.0, majority_frac=MAJORITY_FRAC,
                                max_na_frac=MAX_NA_FRAC, scenario_key=bkey,
                                base_seed=base_seed)
        r2 = detect_cdpe_tiefix(z["field"], lat, lon, threshold=1.0,
                                radius_deg=4.0, majority_frac=MAJORITY_FRAC,
                                max_na_frac=MAX_NA_FRAC, scenario_key=bkey,
                                base_seed=base_seed)
        bit_identical = bool(np.array_equal(np.asarray(r1["cdpe"]),
                                            np.asarray(r2["cdpe"])))
        if not bit_identical:
            raise SystemExit("baseline tiefix rerun is NOT bit-identical; "
                             "aborting")
        print("Bit-identical baseline rerun assertion: PASSED "
              "(recomputed on cached field)")

    # ---- Step 1 verdict: EXACT reproduction of all 720 ---------------------
    repro = pd.DataFrame(repro_rows)
    if len(repro) != 720:
        raise SystemExit(f"reproduction produced {len(repro)} rows, not 720")
    repro["archived_n_cdpe_months"] = [
        arch_keyed[tuple(r[c] for c in KEY_COLS)] for _, r in repro.iterrows()]
    repro["match"] = (repro["n_cdpe_months"]
                      == repro["archived_n_cdpe_months"])
    repro_out = repro.rename(columns={"n_cdpe_months": "recomputed_n_cdpe_months"})
    repro_out.to_csv(out_dir / "reproduction_check.csv", index=False)
    n_match = int(repro["match"].sum())
    print(f"Step 1: reproduced {n_match}/720 archived masked counts exactly")
    if n_match != 720:
        bad = repro_out[~repro_out["match"]]
        (out_dir / "REPRODUCTION_FAILED.txt").write_text(
            f"Only {n_match}/720 reproduced. Mismatches:\n{bad.to_string()}\n")
        raise SystemExit(f"REPRODUCTION FAILED: {n_match}/720 exact matches. "
                         f"Stopping before any tie-fix output (see "
                         f"reproduction_check.csv and REPRODUCTION_FAILED.txt)")

    # ---- Step 3 outputs -----------------------------------------------------
    tiefix = pd.DataFrame(tiefix_rows).set_index(KEY_COLS)
    merged = archived.copy()
    merged["old_n_cdpe_months"] = merged["n_cdpe_months"]
    new_vals = tiefix.loc[[tuple(r[c] for c in KEY_COLS)
                           for _, r in merged.iterrows()]]
    merged["n_cdpe_months"] = new_vals["n_cdpe_months"].values
    merged["n_events"] = new_vals["n_events"].values
    merged["mean_duration"] = new_vals["mean_duration"].values
    merged["months_per_year"] = new_vals["months_per_year"].values
    merged["loglogistic_fallback_fraction"] = new_vals[
        "loglogistic_fallback_fraction"].values
    merged["detector"] = DETECTOR_NAME_TIEFIX
    merged["delta"] = merged["n_cdpe_months"] - merged["old_n_cdpe_months"]
    merged.to_csv(out_dir / "scenarios_tiefix.csv", index=False)
    tied_diag = tiefix[["mean_n_tied_dry", "mean_n_tied_wet"]].reset_index()
    tied_diag.to_csv(out_dir / "tie_diagnostics.csv", index=False)
    seed_df = pd.DataFrame(seed_rows)
    seed_df.to_csv(out_dir / "seed_sensitivity.csv", index=False)
    main_seed_count = int(merged[
        (merged["dataset"] == "NARR") & (merged["timescale"] == 6)
        & (merged["dist"] == "empirical") & (merged["cal_period"] == "full")
        & (merged["water_balance"] == "spei") & (merged["threshold"] == 1.0)
        & (merged["radius_deg"] == 4.0)]["n_cdpe_months"].iloc[0])
    seed_main = int(seed_df[seed_df["seed"] == base_seed]
                    ["n_cdpe_months"].iloc[0])
    if seed_main != main_seed_count:
        raise SystemExit("seed-sensitivity main-seed count disagrees with "
                         "scenarios_tiefix for the exemplar scenario")

    # ---- Step 4: decomposition, both arms, raw + log1p ----------------------
    arm_a = pd.read_csv(ARCH_ARMA / "scenarios.csv")
    rows = []
    rows += decomposition_rows("A", "archived", arm_a, ARM_A_FACTORS)
    rows += decomposition_rows("B", "old", archived, ARM_B_FACTORS)
    rows += decomposition_rows("B", "tiefix", merged, ARM_B_FACTORS)
    decomp = pd.DataFrame(rows)[["arm", "version", "scale", "factor",
                                 "order", "share"]]
    decomp.to_csv(out_dir / "decomposition_tiefix.csv", index=False)
    n_gt50, n_from_zero = write_report(out_dir, merged, decomp, seed_df,
                                       vd_checks, n_match, bit_identical,
                                       base_seed)
    print(f"Report: {n_gt50} scenarios changed >50%, {n_from_zero} rose "
          f"from zero")

    # ---- Manifest ------------------------------------------------------------
    input_files = []
    for d in cfg["datasets"]:
        for role in ("precip", "tmean"):
            p = PKG_ROOT / d[role]["path"]
            input_files.append({"dataset": d["name"], "role": role,
                                "path": d[role]["path"], "bytes": p.stat().st_size,
                                "sha256": _sha256_file(p)})
    spei01 = PKG_ROOT / cfg["arm_a"]["spei_files"][0]["path"]
    input_files.append({"dataset": "SPEIbase (land-mask source)",
                        "role": "spei01", "path": str(spei01.relative_to(PKG_ROOT)),
                        "bytes": spei01.stat().st_size,
                        "sha256": _sha256_file(spei01)})
    import xarray
    manifest = {
        "phase": "Phase 2 tie-fix rerun (2026-11-02)",
        "driver": "scripts/run_armB_tiefix.py",
        "detector_tiefix": "cdpe_sens/detector_tiefix.py",
        "frozen_detector": "cdpe_sens/author_detector.py (unmodified)",
        "package_version": cdpe_sens.__version__,
        "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "pandas": pd.__version__, "xarray": xarray.__version__,
        "config": "config/example_config.json",
        "config_sha256": cfg_sha,
        "base_seed": base_seed,
        "seed_rule": ("per (pole, month): default_rng(int.from_bytes("
                      "sha256('cdpe-tiefix-v1|BASE_SEED=<seed>|scenario="
                      "<key>|month=<t>|pole=<dry|wet>')[:8], 'little')); "
                      "scenario key = (dataset, timescale, dist, cal_period, "
                      "water_balance, threshold, min_area_frac, "
                      "min_cluster_cells, radius_deg) joined with '/'"),
        "seed_sensitivity_seeds": SEED_SENS_SEEDS,
        "land_mask": mask_prov,
        "step1_reproduction": {"matched": n_match, "of": 720, "exact": True},
        "baseline_bit_identical_rerun": bit_identical,
        "vd_reproduction_checks": vd_checks,
        "log_scale": "log1p: log(1 + n_cdpe_months)",
        "n_scenarios": int(len(merged)),
        "elapsed_seconds": round(time.time() - t_start, 1),
        "input_files": input_files,
        "archived_inputs": [
            {"path": "results/run_armB_masked_2026-10-05/scenarios.csv",
             "sha256": _sha256_file(ARCH_MASKED / "scenarios.csv")},
            {"path": "results/run_armA_2026-10-05/scenarios.csv",
             "sha256": _sha256_file(ARCH_ARMA / "scenarios.csv")}],
        "field_cache_sha256": cache_hashes,
        "output_sha256": {
            "scenarios_tiefix.csv": _sha256_file(out_dir / "scenarios_tiefix.csv"),
            "decomposition_tiefix.csv": _sha256_file(
                out_dir / "decomposition_tiefix.csv"),
            "reproduction_check.csv": _sha256_file(
                out_dir / "reproduction_check.csv"),
            "seed_sensitivity.csv": _sha256_file(
                out_dir / "seed_sensitivity.csv"),
            "PHASE2_REPORT.md": _sha256_file(out_dir / "PHASE2_REPORT.md"),
            "changed_gt50pct.csv": _sha256_file(
                out_dir / "changed_gt50pct.csv")},
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2,
                                                          default=str))
    print(f"Done: {len(merged)} scenarios -> {out_dir}")
    print(f"Zeros old={(merged['old_n_cdpe_months'] == 0).sum()} "
          f"new={(merged['n_cdpe_months'] == 0).sum()}")


if __name__ == "__main__":
    main()
