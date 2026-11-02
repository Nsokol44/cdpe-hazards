#!/usr/bin/env python3
"""Phase 3, Step 34 - count models (primary estimand).

Model (per hazard x arm): monthly count ~ CDPE indicator + calendar-month
fixed effects (11 dummies) + linear year term (year - 2001.5) + ONI
(outcome month's centred ONI; in lagged arms the outcome month's ONI and
calendar month, with the exposure label carried from regime month t).
  * Poisson GLM (log link) first; overdispersion = Pearson chi2 / df.
  * If dispersion > 1.5: Negative Binomial is primary - alpha estimated
    by maximum likelihood with statsmodels' discrete NegativeBinomial,
    then a GLM with NegativeBinomial family at that alpha (NB2), which
    supports cluster-robust covariance. Both Poisson and NB are reported
    whenever the NB is triggered; otherwise Poisson alone is primary.
  * Intervals: cluster-robust by year (cov_type='cluster', groups=year)
    is PRIMARY; a year-block bootstrap (resample years with replacement,
    refit the primary family, B = 2000, seed 20261102, percentile CI on
    the IRR) is reported alongside.
Heat waves: the count is heatwave_cell_days (Step 32: days per cell x
3,608 land cells, rounded) so the same count model applies; the IRR is
identical in interpretation to the days-per-cell scale.

Arms: (a) aligned 52 same-month, (b) US-anchored 15 same-month,
(c) aligned 52 lagged, (d) US-anchored 15 lagged (lagged frame = outcome
months Feb 1980-Dec 2023, clusters = outcome years).
Robustness: drop outcome months Apr + May 2011 (same-month arm) /
outcome months Apr + May 2011 i.e. regime Mar + Apr 2011 (lagged arm),
refit the primary family, cluster-robust interval.

Deps: numpy, pandas, statsmodels. Deterministic (seed above).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial

PKG = Path(__file__).resolve().parents[1]
OUT = PKG / "results" / "phase3_2026-11-02"
B = 2000
SEED = 20261102
HAZARDS = [("tornado_all", "Tornadoes"),
           ("hail_ge1in", "Hail >= 1 in"),
           ("heatwave_cell_days", "Heat-wave cell-days")]
ARMS = [("a_same52", "Aligned 52, same-month", "same", "exp_same52"),
        ("b_same15", "US-anchored 15, same-month", "same", "exp_same15"),
        ("c_lag52", "Aligned 52, lagged (t+1)", "lag", "exp_lag52"),
        ("d_lag15", "US-anchored 15, lagged (t+1)", "lag", "exp_lag15")]


def design(frame, expcol):
    X = pd.get_dummies(frame["cal"], prefix="m", drop_first=True
                       ).astype(float)
    X.insert(0, "cdpe", frame[expcol].values.astype(float))
    X.insert(0, "const", 1.0)
    X["year_c"] = frame["year"].values - 2001.5
    X["oni"] = frame["oni"].values
    return X


def fit_family(y, X, family_name, alpha=None):
    fam = (sm.families.Poisson() if family_name == "poisson"
           else sm.families.NegativeBinomial(alpha=alpha))
    return sm.GLM(y, X, family=fam).fit()


def cluster_fit(y, X, family_name, alpha, groups):
    """Fit with year-cluster-robust covariance (fit-time cov_type;
    statsmodels 0.15 GLM results expose robust results this way)."""
    fam = (sm.families.Poisson() if family_name == "poisson"
           else sm.families.NegativeBinomial(alpha=alpha))
    return sm.GLM(y, X, family=fam).fit(
        cov_type="cluster", cov_kwds={"groups": groups})


def analyse(frame, expcol, ycol):
    X = design(frame, expcol)
    y = frame[ycol].values.astype(float)
    groups = frame["year"].values
    pois = fit_family(y, X, "poisson")
    disp = float(pois.pearson_chi2 / pois.df_resid)
    out = {"dispersion_poisson": disp}
    results = {}
    rc = cluster_fit(y, X, "poisson", None, groups)
    ci = np.exp(rc.conf_int().loc["cdpe"].values)
    results["poisson"] = {"irr": float(np.exp(rc.params["cdpe"])),
                          "cluster_se": float(rc.bse["cdpe"]),
                          "ci_lo": float(ci[0]), "ci_hi": float(ci[1]),
                          "p": float(rc.pvalues["cdpe"])}
    primary = "poisson"
    alpha = None
    if disp > 1.5:
        nb_ml = NegativeBinomial(y, X).fit(disp=0)
        alpha = float(nb_ml.params.iloc[-1])
        rc = cluster_fit(y, X, "negbin", alpha, groups)
        ci = np.exp(rc.conf_int().loc["cdpe"].values)
        results["negbin"] = {"irr": float(np.exp(rc.params["cdpe"])),
                             "cluster_se": float(rc.bse["cdpe"]),
                             "ci_lo": float(ci[0]),
                             "ci_hi": float(ci[1]),
                             "p": float(rc.pvalues["cdpe"])}
        primary = "negbin"
    out.update({"primary_family": primary, "alpha_negbin": alpha,
                "results": results})
    # year-block bootstrap of the primary family
    rng = np.random.default_rng(SEED)
    years = np.array(sorted(frame["year"].unique()))
    yr = frame["year"].values
    irrs = []
    for _ in range(B):
        sampled = rng.choice(years, size=len(years), replace=True)
        idx = np.concatenate([np.where(yr == yy)[0] for yy in sampled])
        try:
            f = fit_family(y[idx], X.iloc[idx], primary, alpha)
            irrs.append(float(np.exp(f.params.iloc[1])))
        except Exception:
            continue
    irrs = np.array([v for v in irrs if np.isfinite(v)])
    out["boot"] = {"irr_median": float(np.median(irrs)),
                   "ci_lo": float(np.percentile(irrs, 2.5)),
                   "ci_hi": float(np.percentile(irrs, 97.5)),
                   "n_finite": int(len(irrs))}
    return out


def main() -> int:
    df = pd.read_csv(OUT / "design_monthly.csv")
    lag = df.iloc[1:].copy()
    frames = {"same": df, "lag": lag}
    rows, boot_rows = [], []
    for akey, alabel, kind, col in ARMS:
        frame = frames[kind]
        for ycol, hlabel in HAZARDS:
            a = analyse(frame, col, ycol)
            for fam, r in a["results"].items():
                rows.append({"arm": akey, "arm_label": alabel,
                             "hazard": ycol, "hazard_label": hlabel,
                             "family": fam,
                             "is_primary": fam == a["primary_family"],
                             "dispersion_poisson":
                                 a["dispersion_poisson"],
                             "alpha_negbin": a["alpha_negbin"], **r})
            boot_rows.append({"arm": akey, "arm_label": alabel,
                              "hazard": ycol, "hazard_label": hlabel,
                              "primary_family": a["primary_family"],
                              **a["boot"]})
            print(akey, ycol, a["primary_family"],
                  round(a["dispersion_poisson"], 2), flush=True)
    pd.DataFrame(rows).to_csv(OUT / "glm_results.csv", index=False)
    pd.DataFrame(boot_rows).to_csv(OUT / "glm_yearblock_bootstrap.csv",
                                   index=False)

    # robustness: drop the 2011 outcome cluster
    rob = []
    for akey, alabel, kind, col in [ARMS[0], ARMS[2]]:
        frame = frames[kind]
        f2 = frame[~frame["month"].isin(["2011-04", "2011-05"])]
        for ycol, hlabel in HAZARDS:
            a = analyse(f2, col, ycol)
            r = a["results"][a["primary_family"]]
            rob.append({"arm": akey, "arm_label": alabel,
                        "hazard": ycol, "hazard_label": hlabel,
                        "variant": "drop_outcome_2011-04_2011-05",
                        "primary_family": a["primary_family"],
                        "dispersion_poisson": a["dispersion_poisson"],
                        "alpha_negbin": a["alpha_negbin"], **r})
    pd.DataFrame(rob).to_csv(OUT / "glm_robustness_2011.csv",
                             index=False)
    print("GLM done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
