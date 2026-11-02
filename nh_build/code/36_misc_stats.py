#!/usr/bin/env python3
"""Phase 3, Step 36 - MDES, Jaccard chance baselines, envelope hail
check, Spearman correlations, era representation.

MDES (Task 6): analytic minimum detectable rate ratio at 80% power,
two-sided alpha = 0.05, for the (unstratified) ratio-of-means design:
  MDES = exp((z_0.975 + z_0.80) * sqrt(var_e/n_e + var_u/n_u)),
where var is the variance of the log monthly count, estimated by the
delta method as s^2 / mean^2 from the observed monthly counts in each
group (the log of a monthly count is undefined for zero-count months -
heat-wave months include exact zeros - so the delta-method variance of
the log count is the operative input; it is reported explicitly per
design). Designs: same-month n_e = 52 / 15 with n_u = 528 - n_e; lagged
frame 527 outcome months with n_e = 52 / 15, n_u = 527 - n_e. The
detectable protective effect is exp(-(z sum) * SE) = 1/MDES.

Jaccard chance baselines (Task 7): observed intersection, hypergeometric
expectation n1*n2/N, observed/expected. N = 528 for the 1980-2023 arms;
N = 420 for the Arm B NARR/ERA5 comparison (its run window is
Jan 1980-Dec 2014 per its run_manifest.json). Arm B intersection is
recovered exactly from dataset_agreement.csv: J = I/(n1+n2-I) with
n1 = 44, n2 = 69, J = 0.17708333... gives I = 17 exactly (asserted by
recomputing J from I = 17).

Envelope hail check (Task 8): from cdpe-hazards-aas/results/
rate_ratios_by_config.csv (the current copy of record): envelope
inclusion rule = configurations with >= 10 CDPE months in the window
(included_in_envelope), 23 of 36 for hail >= 1 in; count and list those
whose 95% CI excludes 1.

Spearman (Task 9): annual aligned-CDPE-month counts vs annual hazard
totals, 44 years (1980-2023), scipy spearmanr.

Era representation (Task 10): share of the 52 aligned months falling in
1980-1995 vs the early era's share of the 528 months (192/528).

Deps: numpy, pandas, scipy. Deterministic; no randomness.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PKG = Path(__file__).resolve().parents[1]
OUT = PKG / "results" / "phase3_2026-11-02"
AAS_RES = PKG.parent / "cdpe-hazards-aas" / "results"
SENS = PKG.parent / "cdpe_sensitivity"
HAZARDS = [("tornado_all", "Tornadoes"), ("hail_ge1in", "Hail >= 1 in"),
           ("heatwave_days_per_cell", "Heat-wave days per cell")]
Z = stats.norm.ppf(0.975) + stats.norm.ppf(0.80)


def main() -> int:
    df = pd.read_csv(OUT / "design_monthly.csv")
    lag = df.iloc[1:].copy()

    # ---- MDES ----
    mdes_rows = []
    designs = [("same52", "Same-month, aligned 52", df, "exp_same52"),
               ("same15", "Same-month, US-anchored 15", df, "exp_same15"),
               ("lag52", "Lagged, aligned 52", lag, "exp_lag52"),
               ("lag15", "Lagged, US-anchored 15", lag, "exp_lag15")]
    for key, label, frame, col in designs:
        for h, hlabel in HAZARDS:
            e = frame.loc[frame[col] == 1, h].values.astype(float)
            u = frame.loc[frame[col] == 0, h].values.astype(float)
            var_e = float(np.var(e, ddof=1) / np.mean(e) ** 2)
            var_u = float(np.var(u, ddof=1) / np.mean(u) ** 2)
            se = float(np.sqrt(var_e / len(e) + var_u / len(u)))
            mdes_rows.append({
                "design": key, "design_label": label, "hazard": h,
                "hazard_label": hlabel, "n_exposed": int(len(e)),
                "n_unexposed": int(len(u)),
                "mean_exposed": float(np.mean(e)),
                "mean_unexposed": float(np.mean(u)),
                "var_log_exposed_delta": var_e,
                "var_log_unexposed_delta": var_u, "se_log_rr": se,
                "mdes_rr_upper": float(np.exp(Z * se)),
                "mdes_rr_lower": float(np.exp(-Z * se))})
    pd.DataFrame(mdes_rows).to_csv(OUT / "mdes.csv", index=False)

    # ---- Jaccard chance baselines ----
    cfg = pd.read_csv(SENS / "results" / "run_armA_2026-10-05"
                      / "cdpe_monthly_series.csv")
    def months_of(colname):
        return set(cfg.loc[cfg[colname] == 1, "date"].astype(str)
                   .str[:7])
    s1 = months_of("SPEI-1|thr=1.5|r=4.0")
    s3 = months_of("SPEI-3|thr=1.5|r=4.0")
    s6 = months_of("SPEI-6|thr=1.5|r=4.0")
    assert len(s1) == 46 and len(s3) == 48 and len(s6) == 51
    assert len(s1 & s3) == 12 and len(s1 & s6) == 4
    summ = json.loads((PKG / "results" / "alignment_2026-11-02"
                       / "alignment_summary.json").read_text())
    inter_ca = int(summ["subset_test"]["intersection"])
    assert inter_ca == 32
    agr = pd.read_csv(SENS / "results" / "run_armB_masked_2026-10-05"
                      / "dataset_agreement.csv")
    row = agr[(agr["dataset_a"] == "NARR")
              & (agr["dataset_b"] == "ERA5")].iloc[0]
    n1b, n2b, jb = int(row["months_a"]), int(row["months_b"]), \
        float(row["jaccard"])
    inter_b = int(round(jb * (n1b + n2b) / (1 + jb)))
    assert abs(inter_b / (n1b + n2b - inter_b) - jb) < 1e-9
    assert inter_b == 17
    jrows = []
    for label, n1, n2, inter, ntot in [
            ("SPEI-3 vs SPEI-1 (Arm A baselines)", 48, 46, 12, 528),
            ("SPEI-6 vs SPEI-1 (Arm A baselines)", 51, 46, 4, 528),
            ("Companion v2.11 vs Arm A v2.10 SPEI-1", 52, 46, 32, 528),
            ("NARR vs ERA5 (Arm B masked baselines)", n1b, n2b, 17,
             420)]:
        exp = n1 * n2 / ntot
        jrows.append({"comparison": label, "n1": n1, "n2": n2,
                      "n_months_window": ntot,
                      "observed_intersection": inter,
                      "hypergeometric_expected": exp,
                      "observed_over_expected": inter / exp,
                      "jaccard": inter / (n1 + n2 - inter)})
    pd.DataFrame(jrows).to_csv(OUT / "jaccard_baselines.csv",
                               index=False)

    # ---- envelope hail check ----
    bc = pd.read_csv(AAS_RES / "rate_ratios_by_config.csv")
    h = bc[(bc["hazard"] == "hail_ge1in") & (bc["included_in_envelope"])]
    excl = h[(h["ci_lo"] > 1) | (h["ci_hi"] < 1)].copy()
    excl.to_csv(OUT / "envelope_hail_excluding1.csv", index=False)
    env_info = {"n_included": int(len(h)),
                "n_excluding_1": int(len(excl)),
                "inclusion_rule": "included_in_envelope == True in "
                "rate_ratios_by_config.csv, i.e. >= 10 CDPE months in "
                "the 1980-2023 window (frozen Step 06 envelope rule; "
                "23 of 36 Arm A configurations qualify)"}
    (OUT / "envelope_hail_check.json").write_text(
        json.dumps(env_info, indent=2))

    # ---- Spearman: annual CDPE counts vs annual hazard totals ----
    ann = df.groupby("year").agg(
        n_cdpe=("exp_same52", "sum"), tornado_all=("tornado_all", "sum"),
        hail_ge1in=("hail_ge1in", "sum"),
        heatwave_days_per_cell=("heatwave_days_per_cell", "sum")
        ).reset_index()
    ann.to_csv(OUT / "annual_cdpe_vs_hazards.csv", index=False)
    sp_rows = []
    for h, hlabel in HAZARDS:
        rho, p = stats.spearmanr(ann["n_cdpe"], ann[h])
        sp_rows.append({"hazard": h, "hazard_label": hlabel,
                        "spearman_rho": float(rho), "p_value": float(p),
                        "n_years": int(len(ann))})
    pd.DataFrame(sp_rows).to_csv(OUT / "spearman_annual.csv",
                                 index=False)

    # ---- era representation ----
    early_share_months = float((df["year"] <= 1995).mean())
    early_n = int(((df["year"] <= 1995) & (df["exp_same52"] == 1)).sum())
    era_info = {"aligned_months_early_era": early_n,
                "aligned_months_total": 52,
                "share_aligned_in_early_era": early_n / 52,
                "early_era_months": int((df["year"] <= 1995).sum()),
                "total_months": 528,
                "share_early_era_of_window": early_share_months}
    (OUT / "era_representation.json").write_text(
        json.dumps(era_info, indent=2))
    print(json.dumps({"mdes_rows": len(mdes_rows), **env_info,
                      **era_info}, indent=2))
    print(pd.DataFrame(sp_rows).to_string(index=False))
    print(pd.DataFrame(jrows).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
