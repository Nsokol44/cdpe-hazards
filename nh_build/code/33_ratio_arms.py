#!/usr/bin/env python3
"""Phase 3, Step 33 - ratio-of-means rate ratios (frozen Step 06 estimator).

The point estimator and bootstrap are copied verbatim in construction from
the frozen conditioning code (cdpe_sensitivity/scripts/
run_conditioning_no_lightning.py, itself verbatim frozen Step 06):
  * rr_from_arrays: calendar-month-stratified ratio of means. For each
    calendar month m, w_m = (exposed months in m) / (total exposed);
    RR = [sum_m w_m * mean(values | exposed, m)] /
         [sum_m w_m * mean(values | unexposed, m)] (weights renormalised
    over calendar months present on both sides).
  * bootstrap: resample YEARS with replacement (all years of the analysis
    frame), recompute the stratified RR on the resampled month multiset,
    B = 2000, 95% CI = 2.5th/97.5th percentiles of finite replicates.
Phase 3 uses a fresh generator seeded 20261026 (the frozen seed) consumed
in the fixed documented order below, so every interval is reproducible
from this script alone. (The frozen run shared one stream across all
series x configurations, so its baseline intervals sit at different
stream positions; point estimates are stream-free and must match
exactly - the Arm A continuity check below asserts the rounded frozen
values 1.13 / 1.10 / 0.90.)

Arms (design_monthly.csv from Step 32):
  (a) aligned 52 same-month   (e) Arm A 46 same-month (continuity)
  (b) US-anchored 15 same-month
  (c) aligned 52 lagged: outcome month t+1, exposure = regime month t;
      frame = Feb 1980-Dec 2023 (527 outcome months; Jan 1980 has no
      regime month and is excluded). A month can be exposed in the
      same-month arm and an outcome in the lagged arm; the arms use
      separate design columns and are never mixed.
  (d) US-anchored 15 lagged (same frame as (c)).

Also: split-era within-era RRs (aligned same-month + lagged; eras
1980-1995 / 1996-2023 of the OUTCOME month) with the era-difference
(ratio of RRs) and its bootstrap CI (years resampled independently
within each era, ratio recomputed per replicate, same stream);
leave-the-2011-cluster-out ratios; median contrasts (year bootstrap,
seed 20261102); leave-one-exposed-month-out ratio ranges.

Deps: numpy, pandas. Deterministic given the seeds above.
"""
from pathlib import Path

import numpy as np
import pandas as pd

PKG = Path(__file__).resolve().parents[1]
OUT = PKG / "results" / "phase3_2026-11-02"
B = 2000
SEED_FROZEN = 20261026
SEED_P3 = 20261102
HAZARDS = ["tornado_all", "hail_ge1in", "heatwave_days_per_cell"]
LABELS = {"tornado_all": "Tornadoes", "hail_ge1in": "Hail >= 1 in",
          "heatwave_days_per_cell": "Heat-wave days per cell"}


def rr_from_arrays(values, cal, cdpe):
    """Frozen Step 06 stratified rate ratio (verbatim construction)."""
    ok = ~np.isnan(values)
    total_cdpe = int((cdpe & ok).sum())
    if total_cdpe == 0:
        return np.nan
    num = den = wsum = 0.0
    for m in range(1, 13):
        c = ok & cdpe & (cal == m)
        k = ok & ~cdpe & (cal == m)
        if c.sum() == 0 or k.sum() == 0:
            continue
        w = c.sum() / total_cdpe
        num += w * values[c].mean()
        den += w * values[k].mean()
        wsum += w
    if wsum == 0 or den == 0:
        return np.nan
    return (num / wsum) / (den / wsum)


def boot_rr(values, cal, yr, cdpe, years, rng):
    reps = np.empty(B)
    year_arr = np.array(years)
    for b in range(B):
        sampled = rng.choice(year_arr, size=len(year_arr), replace=True)
        idx = np.concatenate([np.where(yr == y)[0] for y in sampled])
        reps[b] = rr_from_arrays(values[idx], cal[idx], cdpe[idx])
    finite = reps[np.isfinite(reps)]
    return (float(np.percentile(finite, 2.5)),
            float(np.percentile(finite, 97.5)), int(len(finite)))


def estimate(frame, series, expcol, rng):
    values = frame[series].values.astype(float)
    cal, yr = frame["cal"].values, frame["year"].values
    cdpe = frame[expcol].values.astype(bool)
    point = rr_from_arrays(values, cal, cdpe)
    lo, hi, nf = boot_rr(values, cal, yr, cdpe,
                         sorted(frame["year"].unique()), rng)
    return {"rr": float(point), "ci_lo": lo, "ci_hi": hi,
            "n_exposed": int(cdpe.sum()), "n_months": int(len(frame)),
            "bootstrap_finite": nf}


def main() -> int:
    df = pd.read_csv(OUT / "design_monthly.csv")
    lag = df.iloc[1:].copy()  # outcome months Feb 1980..Dec 2023
    arms = [("a_same52", "Aligned 52, same-month", df, "exp_same52"),
            ("b_same15", "US-anchored 15, same-month", df, "exp_same15"),
            ("c_lag52", "Aligned 52, lagged (t+1)", lag, "exp_lag52"),
            ("d_lag15", "US-anchored 15, lagged (t+1)", lag, "exp_lag15"),
            ("e_armA46", "Arm A 46, same-month (continuity)", df,
             "exp_armA46")]
    rng = np.random.default_rng(SEED_FROZEN)
    rows = []
    for key, label, frame, col in arms:
        for h in HAZARDS:
            r = estimate(frame, h, col, rng)
            rows.append({"arm": key, "arm_label": label, "hazard": h,
                         "hazard_label": LABELS[h], **r})
    ratios = pd.DataFrame(rows)
    ratios.to_csv(OUT / "ratio_results.csv", index=False)

    # continuity check: Arm A point estimates must round to frozen values
    frozen = {"tornado_all": 1.13, "hail_ge1in": 1.10,
              "heatwave_days_per_cell": 0.90}
    for h, fv in frozen.items():
        got = ratios.loc[(ratios["arm"] == "e_armA46")
                         & (ratios["hazard"] == h), "rr"].iloc[0]
        assert round(float(got), 2) == fv, (h, got, fv)
    print("continuity OK: Arm A 46 reproduces 1.13 / 1.10 / 0.90")

    # --- split-era (aligned arms; era of the outcome month) ---
    era_rows = []
    for arm_key, frame, col in [("same52", df, "exp_same52"),
                                ("lag52", lag, "exp_lag52")]:
        for h in HAZARDS:
            per_era = {}
            for era, yrs in [("1980-1995", list(range(1980, 1996))),
                             ("1996-2023", list(range(1996, 2024)))]:
                sub = frame[frame["year"].isin(yrs)]
                r = estimate(sub, h, col, rng)
                per_era[era] = r
                era_rows.append({"arm": arm_key, "hazard": h,
                                 "hazard_label": LABELS[h], "era": era,
                                 **r})
            # era-difference: ratio of RRs, bootstrap resampling years
            # independently within each era on the same stream
            subs = {e: frame[frame["year"].isin(y)] for e, y in
                    [("1980-1995", list(range(1980, 1996))),
                     ("1996-2023", list(range(1996, 2024)))]}
            reps = []
            for _ in range(B):
                rr_e = []
                for era in ("1980-1995", "1996-2023"):
                    sub = subs[era]
                    yrs = np.array(sorted(sub["year"].unique()))
                    sampled = rng.choice(yrs, size=len(yrs), replace=True)
                    idx = np.concatenate(
                        [np.where(sub["year"].values == y)[0]
                         for y in sampled])
                    rr_e.append(rr_from_arrays(
                        sub[h].values.astype(float)[idx],
                        sub["cal"].values[idx],
                        sub[col].values.astype(bool)[idx]))
                if np.all(np.isfinite(rr_e)) and rr_e[0] > 0:
                    reps.append(rr_e[1] / rr_e[0])
            reps = np.array(reps)
            era_rows.append({
                "arm": arm_key, "hazard": h, "hazard_label": LABELS[h],
                "era": "ratio_1996-2023_over_1980-1995",
                "rr": per_era["1996-2023"]["rr"]
                      / per_era["1980-1995"]["rr"],
                "ci_lo": float(np.percentile(reps, 2.5)),
                "ci_hi": float(np.percentile(reps, 97.5)),
                "n_exposed": per_era["1996-2023"]["n_exposed"],
                "n_months": per_era["1996-2023"]["n_months"],
                "bootstrap_finite": int(len(reps))})
    pd.DataFrame(era_rows).to_csv(OUT / "split_era_results.csv",
                                  index=False)

    # --- robustness: drop the 2011 cluster ---
    rob = []
    same_drop = df[~df["month"].isin(["2011-04", "2011-05"])]
    lag_drop = lag[~lag["month"].isin(["2011-04", "2011-05"])]
    for label, frame, col in [("same52_drop2011", same_drop, "exp_same52"),
                              ("lag52_drop2011", lag_drop, "exp_lag52")]:
        for h in HAZARDS:
            r = estimate(frame, h, col, rng)
            rob.append({"variant": label, "hazard": h,
                        "hazard_label": LABELS[h], **r})
    pd.DataFrame(rob).to_csv(OUT / "robustness_ratio_2011.csv",
                             index=False)

    # --- median contrast (year bootstrap, seed 20261102) ---
    rng2 = np.random.default_rng(SEED_P3)
    med_rows = []
    for key, label, frame, col in arms[:4]:
        for h in HAZARDS:
            v = frame[h].values.astype(float)
            cd = frame[col].values.astype(bool)
            med_e = float(np.median(v[cd]))
            med_u = float(np.median(v[~cd]))
            ratio = med_e / med_u if med_u != 0 else np.nan
            yr = frame["year"].values
            years = np.array(sorted(frame["year"].unique()))
            reps = []
            for _ in range(B):
                sampled = rng2.choice(years, size=len(years),
                                      replace=True)
                idx = np.concatenate([np.where(yr == y)[0]
                                      for y in sampled])
                vv, cc = v[idx], cd[idx]
                if cc.sum() and (~cc).sum() \
                        and np.median(vv[~cc]) != 0:
                    reps.append(np.median(vv[cc])
                                / np.median(vv[~cc]))
            reps = np.array(reps)
            med_rows.append({
                "arm": key, "arm_label": label, "hazard": h,
                "hazard_label": LABELS[h], "median_exposed": med_e,
                "median_unexposed": med_u, "median_ratio": ratio,
                "diff": med_e - med_u,
                "ci_lo": float(np.percentile(reps, 2.5)),
                "ci_hi": float(np.percentile(reps, 97.5)),
                "bootstrap_finite": int(len(reps))})
    pd.DataFrame(med_rows).to_csv(OUT / "median_contrast.csv",
                                  index=False)

    # --- leave-one-exposed-month-out range (point estimator) ---
    loo_rows = []
    for key, label, frame, col in arms[:4]:
        exp_months = frame.loc[frame[col] == 1, "month"].tolist()
        for h in HAZARDS:
            vals = []
            for m in exp_months:
                f2 = frame.copy()
                f2.loc[f2["month"] == m, col] = 0
                vals.append(rr_from_arrays(
                    f2[h].values.astype(float), f2["cal"].values,
                    f2[col].values.astype(bool)))
            loo_rows.append({"arm": key, "arm_label": label,
                             "hazard": h, "hazard_label": LABELS[h],
                             "loo_min": float(np.min(vals)),
                             "loo_max": float(np.max(vals)),
                             "n_left_out": len(vals)})
    pd.DataFrame(loo_rows).to_csv(OUT / "loo_range.csv", index=False)
    print(ratios.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
