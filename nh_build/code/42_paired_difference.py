#!/usr/bin/env python3
"""Fix Round 2, item 5 - paired same-month vs lagged difference.

The manuscript's Discussion reads the lagged arm's movement toward 1
as "the pattern reverse causation predicts", but the same-month and
lagged intervals overlap, so the attenuation itself needs an interval.
This script computes the PAIRED difference: a month-paired bootstrap
over outcome months. Both arms are refit on the SAME resample, so the
difference distribution is paired by construction.

Frame: design_monthly.csv restricted to outcome months Feb 1980 to
Dec 2023 (527 months; Jan 1980 has no antecedent month). For outcome
month t, exp_same52 is the same-month exposure and exp_lag52 is the
antecedent (t-1) exposure; both are columns of the design table, so a
row resample pairs the two arms at the same outcome months. Model per
hazard and arm: the primary Phase-3 model of code/34 (negative
binomial GLM, calendar-month fixed effects, linear year term, ONI
covariate), with the NB alpha fixed at the full-frame ML estimate for
that hazard and arm (stability and speed in the bootstrap; the
full-frame fits at the estimated alphas are the point estimates).
Difference: d = log(IRR_same) - log(IRR_lagged), reported with its
percentile interval, and as exp(d), the ratio of the two IRRs.
B = 2000, seed 20261102.

Outputs: results/fixround2_2026-11-02/paired_difference.csv

Deterministic. Deps: numpy, pandas, statsmodels.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial

PKG = Path(__file__).resolve().parents[1]
P3 = PKG / "results" / "phase3_2026-11-02"
OUT = PKG / "results" / "fixround2_2026-11-02"
OUT.mkdir(parents=True, exist_ok=True)
B = 2000
SEED = 20261102
HAZARDS = [("tornado_all", "Tornadoes"),
           ("hail_ge1in", "Hail >= 1 in"),
           ("heatwave_cell_days", "Heat-wave cell-days")]


def design(frame, expcol):
    X = pd.get_dummies(frame["cal"], prefix="m", drop_first=True
                       ).astype(float)
    X.insert(0, "cdpe", frame[expcol].values.astype(float))
    X.insert(0, "const", 1.0)
    X["year_c"] = frame["year"].values - 2001.5
    X["oni"] = frame["oni"].values
    return X


def fit_logirr(y, X, alpha):
    fam = sm.families.NegativeBinomial(alpha=alpha)
    return float(sm.GLM(y, X, family=fam).fit().params["cdpe"])


def main() -> int:
    df = pd.read_csv(P3 / "design_monthly.csv")
    frame = df.iloc[1:].copy()  # outcome months Feb 1980 - Dec 2023
    assert len(frame) == 527
    n = len(frame)
    rng = np.random.default_rng(SEED)
    rows = []
    for ycol, hlabel in HAZARDS:
        y = frame[ycol].values.astype(float)
        alphas, point = {}, {}
        for arm, col in (("same", "exp_same52"), ("lagged", "exp_lag52")):
            X = design(frame, col)
            nb_ml = NegativeBinomial(y, X).fit(disp=0)
            alphas[arm] = float(nb_ml.params.iloc[-1])
            point[arm] = fit_logirr(y, X, alphas[arm])
        diffs = []
        Xs = {arm: design(frame, col) for arm, col in
              (("same", "exp_same52"), ("lagged", "exp_lag52"))}
        for _ in range(B):
            idx = rng.integers(0, n, size=n)
            yb = y[idx]
            try:
                ls = fit_logirr(yb, Xs["same"].iloc[idx], alphas["same"])
                ll = fit_logirr(yb, Xs["lagged"].iloc[idx],
                                alphas["lagged"])
                diffs.append(ls - ll)
            except Exception:
                continue
        diffs = np.array([d for d in diffs if np.isfinite(d)])
        d_point = point["same"] - point["lagged"]
        rows.append({
            "hazard": ycol, "hazard_label": hlabel,
            "irr_same_shared_frame": float(np.exp(point["same"])),
            "irr_lagged_shared_frame": float(np.exp(point["lagged"])),
            "paired_diff_log_irr": float(d_point),
            "paired_diff_ci_lo": float(np.percentile(diffs, 2.5)),
            "paired_diff_ci_hi": float(np.percentile(diffs, 97.5)),
            "ratio_of_irrs": float(np.exp(d_point)),
            "ratio_ci_lo": float(np.exp(np.percentile(diffs, 2.5))),
            "ratio_ci_hi": float(np.exp(np.percentile(diffs, 97.5))),
            "alpha_same": alphas["same"], "alpha_lagged": alphas["lagged"],
            "bootstrap_finite": int(len(diffs))})
        print(hlabel, "same", round(float(np.exp(point["same"])), 3),
              "lagged", round(float(np.exp(point["lagged"])), 3),
              "diff", round(float(d_point), 3),
              "CI", round(float(np.percentile(diffs, 2.5)), 3),
              round(float(np.percentile(diffs, 97.5)), 3),
              "finite", len(diffs), flush=True)
    pd.DataFrame(rows).to_csv(OUT / "paired_difference.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
