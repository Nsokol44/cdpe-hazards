# Phase 3 results — CDPE hazards statistics rebuilt on the aligned catalog (2026-11-02)

All numbers below are read from the saved outputs of scripts 32–36 in `code/` (outputs in `results/phase3_2026-11-02/`); each table names its source file. No manuscript was edited. Window: January 1980–December 2023 (528 months) throughout, except the lagged arms (527 outcome months, February 1980–December 2023) and Arm B (420 months, see §8).

## 0. Input validation (source: validation.json, script 32)

- Aligned catalog: companion v2.11 SPEI-1 baseline **52 months** (all within Jan 1980–Dec 2023; latest month 2022-04); US-anchored subset **15 months**; Arm A v2.10 **46 months**; companion ∩ Arm A = 32 months. Note: the latest aligned month is 2022-04 (the task brief said ≤ 2022-03); every regime month's t+1 is still inside the window, so the lagged design is unaffected.
- Monthly hazard series (`cdpe-hazards-aas/results/monthly_series_all.csv`, 528 rows): totals reproduce the frozen totals exactly — tornadoes 54,607, hail ≥ 1 in 229,650, hail overall 379,430. Heat waves: the series stores days per cell over 3,608 land cells; total = 475,232.99 cell-days (asserted in script 32), mean 0.249 days per cell per month.
- ONI covariate: NOAA PSL/CPC ONI, centred 3-month running mean, ERSST v6 vintage retrieved 2026-11-02 (see DATA_MANIFEST.md). Cross-check vs the SEG v5 fallback file: r = 0.996, max |difference| = 0.29.
- Era split of record: 1980–1995 vs 1996–2023 (1996 boundary, frozen Step 06 split-era block).

## 1. Ratio-of-means rate ratios — frozen Step 06 estimator (source: ratio_results.csv, script 33)

Estimator: calendar-month-stratified ratio of means; 95% CI from the year-resample bootstrap (B = 2000, percentile; fresh generator seeded 20261026, the frozen seed, consumed in table order — see script 33 docstring for why the frozen run's intervals differ in the second decimal: shared-stream position). Continuity: arm (e) reproduces the frozen point estimates exactly (tornadoes 1.13, hail 1.10, heat 0.90; asserted in code).

| Arm | Hazard | RR (95% CI) | Exposed months |
|---|---|---|---|
| Aligned 52, same-month | Tornadoes | 1.16 (0.78–1.53) | 52 |
| Aligned 52, same-month | Hail >= 1 in | 1.01 (0.70–1.37) | 52 |
| Aligned 52, same-month | Heat-wave days per cell | 0.88 (0.50–1.42) | 52 |
| US-anchored 15, same-month | Tornadoes | 0.99 (0.57–1.54) | 15 |
| US-anchored 15, same-month | Hail >= 1 in | 1.00 (0.67–1.32) | 15 |
| US-anchored 15, same-month | Heat-wave days per cell | 0.93 (0.46–1.76) | 15 |
| Aligned 52, lagged (t+1) | Tornadoes | 1.12 (0.84–1.44) | 52 |
| Aligned 52, lagged (t+1) | Hail >= 1 in | 1.10 (0.76–1.49) | 52 |
| Aligned 52, lagged (t+1) | Heat-wave days per cell | 1.15 (0.56–2.17) | 52 |
| US-anchored 15, lagged (t+1) | Tornadoes | 0.87 (0.68–1.09) | 15 |
| US-anchored 15, lagged (t+1) | Hail >= 1 in | 0.94 (0.68–1.21) | 15 |
| US-anchored 15, lagged (t+1) | Heat-wave days per cell | 0.60 (0.32–1.04) | 15 |
| Arm A 46, same-month (continuity) | Tornadoes | 1.13 (0.82–1.49) | 46 |
| Arm A 46, same-month (continuity) | Hail >= 1 in | 1.10 (0.79–1.50) | 46 |
| Arm A 46, same-month (continuity) | Heat-wave days per cell | 0.90 (0.54–1.36) | 46 |

## 2. Count models — primary estimand (sources: glm_results.csv, glm_yearblock_bootstrap.csv, script 34)

GLM of monthly counts on CDPE indicator + calendar-month fixed effects + linear year + ONI. Poisson fitted first; Pearson dispersion exceeded 1.5 for every hazard × arm, so the Negative Binomial (NB2; alpha by discrete-NB maximum likelihood, GLM at that alpha) is primary everywhere and both families are reported. Primary intervals are cluster-robust by year; the year-block bootstrap (B = 2000, seed 20261102) is shown alongside. Heat waves are modelled as cell-day counts (days per cell × 3,608 land cells).

| Arm | Hazard | Family | IRR (cluster 95% CI) | Bootstrap 95% CI | Poisson dispersion | NB alpha |
|---|---|---|---|---|---|---|
| Aligned 52, same-month | Tornadoes | poisson | 1.16 (0.86–1.56) | 0.77–1.44 | 44.9 | 0.51 |
| Aligned 52, same-month | Tornadoes | negbin | 1.09 (0.79–1.49) * | 0.77–1.44 | 44.9 | 0.51 |
| Aligned 52, same-month | Hail >= 1 in | poisson | 1.02 (0.79–1.33) | 0.88–1.40 | 100.7 | 0.57 |
| Aligned 52, same-month | Hail >= 1 in | negbin | 1.12 (0.89–1.41) * | 0.88–1.40 | 100.7 | 0.57 |
| Aligned 52, same-month | Heat-wave cell-days | poisson | 0.89 (0.57–1.40) | 0.59–1.38 | 2043.4 | 2.13 |
| Aligned 52, same-month | Heat-wave cell-days | negbin | 0.91 (0.60–1.37) * | 0.59–1.38 | 2043.4 | 2.13 |
| US-anchored 15, same-month | Tornadoes | poisson | 0.97 (0.57–1.64) | 0.53–1.79 | 46.0 | 0.51 |
| US-anchored 15, same-month | Tornadoes | negbin | 1.04 (0.53–2.02) * | 0.53–1.79 | 46.0 | 0.51 |
| US-anchored 15, same-month | Hail >= 1 in | poisson | 0.94 (0.74–1.20) | 0.71–1.28 | 100.8 | 0.57 |
| US-anchored 15, same-month | Hail >= 1 in | negbin | 0.98 (0.74–1.29) * | 0.71–1.28 | 100.8 | 0.57 |
| US-anchored 15, same-month | Heat-wave cell-days | poisson | 0.89 (0.50–1.58) | 0.49–1.94 | 2046.5 | 2.13 |
| US-anchored 15, same-month | Heat-wave cell-days | negbin | 1.05 (0.59–1.89) * | 0.49–1.94 | 2046.5 | 2.13 |
| Aligned 52, lagged (t+1) | Tornadoes | poisson | 1.13 (0.88–1.46) | 0.79–1.25 | 45.4 | 0.51 |
| Aligned 52, lagged (t+1) | Tornadoes | negbin | 1.00 (0.79–1.25) * | 0.79–1.25 | 45.4 | 0.51 |
| Aligned 52, lagged (t+1) | Hail >= 1 in | poisson | 1.14 (0.88–1.48) | 0.79–1.18 | 99.7 | 0.57 |
| Aligned 52, lagged (t+1) | Hail >= 1 in | negbin | 0.96 (0.79–1.17) * | 0.79–1.18 | 99.7 | 0.57 |
| Aligned 52, lagged (t+1) | Heat-wave cell-days | poisson | 1.17 (0.62–2.18) | 0.65–1.99 | 2048.2 | 2.13 |
| Aligned 52, lagged (t+1) | Heat-wave cell-days | negbin | 1.14 (0.66–1.96) * | 0.65–1.99 | 2048.2 | 2.13 |
| US-anchored 15, lagged (t+1) | Tornadoes | poisson | 0.87 (0.67–1.13) | 0.72–1.32 | 45.8 | 0.51 |
| US-anchored 15, lagged (t+1) | Tornadoes | negbin | 0.96 (0.73–1.28) * | 0.72–1.32 | 45.8 | 0.51 |
| US-anchored 15, lagged (t+1) | Hail >= 1 in | poisson | 0.94 (0.77–1.15) | 0.88–1.35 | 100.8 | 0.57 |
| US-anchored 15, lagged (t+1) | Hail >= 1 in | negbin | 1.06 (0.88–1.29) * | 0.88–1.35 | 100.8 | 0.57 |
| US-anchored 15, lagged (t+1) | Heat-wave cell-days | poisson | 0.56 (0.32–0.98) | 0.34–1.33 | 2029.3 | 2.13 |
| US-anchored 15, lagged (t+1) | Heat-wave cell-days | negbin | 0.73 (0.40–1.32) * | 0.34–1.33 | 2029.3 | 2.13 |

* = primary family for that hazard × arm (NB in all cases here).

## 3. Robustness (sources: robustness_ratio_2011.csv, glm_robustness_2011.csv, median_contrast.csv, loo_range.csv)

### 3a. Leave-the-2011-cluster-out — ratio estimator

| Variant | Hazard | RR (95% CI) |
|---|---|---|
| same52_drop2011 | Tornadoes | 1.00 (0.73–1.30) |
| same52_drop2011 | Hail >= 1 in | 0.86 (0.67–1.04) |
| same52_drop2011 | Heat-wave days per cell | 0.70 (0.42–1.13) |
| lag52_drop2011 | Tornadoes | 0.98 (0.79–1.18) |
| lag52_drop2011 | Hail >= 1 in | 0.98 (0.77–1.22) |
| lag52_drop2011 | Heat-wave days per cell | 1.00 (0.56–1.81) |

### 3b. Leave-the-2011-cluster-out — GLM (primary family, cluster-robust)

| Arm | Hazard | Family | IRR (cluster 95% CI) |
|---|---|---|---|
| Aligned 52, same-month | Tornadoes | negbin | 1.01 (0.72–1.41) |
| Aligned 52, same-month | Hail >= 1 in | negbin | 1.08 (0.85–1.36) |
| Aligned 52, same-month | Heat-wave cell-days | negbin | 0.80 (0.54–1.20) |
| Aligned 52, lagged (t+1) | Tornadoes | negbin | 0.92 (0.76–1.11) |
| Aligned 52, lagged (t+1) | Hail >= 1 in | negbin | 0.92 (0.78–1.08) |
| Aligned 52, lagged (t+1) | Heat-wave cell-days | negbin | 1.02 (0.63–1.68) |

### 3c. Median contrast (year bootstrap, B = 2000, seed 20261102)

| Arm | Hazard | Median count, exposed vs unexposed | Median ratio (95% CI) |
|---|---|---|---|
| Aligned 52, same-month | Tornadoes | 76.0 vs 72.0 | 1.06 (0.65–1.94) |
| Aligned 52, same-month | Hail >= 1 in | 189.0 vs 184.0 | 1.03 (0.63–2.07) |
| Aligned 52, same-month | Heat-wave days per cell | 0.079 vs 0.086 | 0.91 (0.28–1.93) |
| US-anchored 15, same-month | Tornadoes | 131.0 vs 72.0 | 1.82 (0.33–3.16) |
| US-anchored 15, same-month | Hail >= 1 in | 337.0 vs 182.0 | 1.85 (0.80–6.80) |
| US-anchored 15, same-month | Heat-wave days per cell | 0.144 vs 0.085 | 1.69 (0.28–3.20) |
| Aligned 52, lagged (t+1) | Tornadoes | 91.5 vs 71.0 | 1.29 (0.91–2.04) |
| Aligned 52, lagged (t+1) | Hail >= 1 in | 357.0 vs 181.0 | 1.97 (0.68–3.61) |
| Aligned 52, lagged (t+1) | Heat-wave days per cell | 0.072 vs 0.086 | 0.83 (0.36–2.24) |
| US-anchored 15, lagged (t+1) | Tornadoes | 94.0 vs 72.0 | 1.31 (0.97–1.98) |
| US-anchored 15, lagged (t+1) | Hail >= 1 in | 565.0 vs 181.0 | 3.12 (1.06–5.96) |
| US-anchored 15, lagged (t+1) | Heat-wave days per cell | 0.095 vs 0.086 | 1.09 (0.36–2.75) |

### 3d. Leave-one-exposed-month-out range (ratio estimator, point values)

| Arm | Hazard | LOO RR range | Months left out |
|---|---|---|---|
| Aligned 52, same-month | Tornadoes | 0.99–1.20 | 52 |
| Aligned 52, same-month | Hail >= 1 in | 0.92–1.05 | 52 |
| Aligned 52, same-month | Heat-wave days per cell | 0.76–0.92 | 52 |
| US-anchored 15, same-month | Tornadoes | 0.84–1.06 | 15 |
| US-anchored 15, same-month | Hail >= 1 in | 0.92–1.11 | 15 |
| US-anchored 15, same-month | Heat-wave days per cell | 0.74–1.04 | 15 |
| Aligned 52, lagged (t+1) | Tornadoes | 0.98–1.15 | 52 |
| Aligned 52, lagged (t+1) | Hail >= 1 in | 1.03–1.14 | 52 |
| Aligned 52, lagged (t+1) | Heat-wave days per cell | 0.86–1.19 | 52 |
| US-anchored 15, lagged (t+1) | Tornadoes | 0.82–0.92 | 15 |
| US-anchored 15, lagged (t+1) | Hail >= 1 in | 0.90–1.03 | 15 |
| US-anchored 15, lagged (t+1) | Heat-wave days per cell | 0.51–0.67 | 15 |

## 4. Split-era rate ratios and era difference (source: split_era_results.csv, script 33)

Within-era RRs use the frozen stratified estimator with the year bootstrap restricted to the era's years; the era difference (ratio of the 1996–2023 RR to the 1980–1995 RR) carries its own bootstrap CI from independent within-era year resamples.

| Arm | Hazard | Era / contrast | RR (95% CI) | Exposed months |
|---|---|---|---|---|
| same52 | Tornadoes | 1980-1995 | 0.90 (0.66–1.19) | 24 |
| same52 | Tornadoes | 1996-2023 | 1.33 (0.82–1.76) | 28 |
| same52 | Tornadoes | ratio_1996-2023_over_1980-1995 | 1.47 (0.85–2.24) | 28 |
| same52 | Hail >= 1 in | 1980-1995 | 0.77 (0.60–0.98) | 24 |
| same52 | Hail >= 1 in | 1996-2023 | 1.08 (0.83–1.41) | 28 |
| same52 | Hail >= 1 in | ratio_1996-2023_over_1980-1995 | 1.41 (0.98–2.01) | 28 |
| same52 | Heat-wave days per cell | 1980-1995 | 0.75 (0.39–1.47) | 24 |
| same52 | Heat-wave days per cell | 1996-2023 | 0.99 (0.43–1.84) | 28 |
| same52 | Heat-wave days per cell | ratio_1996-2023_over_1980-1995 | 1.32 (0.46–3.28) | 28 |
| lag52 | Tornadoes | 1980-1995 | 0.96 (0.70–1.30) | 24 |
| lag52 | Tornadoes | 1996-2023 | 1.28 (0.91–1.67) | 28 |
| lag52 | Tornadoes | ratio_1996-2023_over_1980-1995 | 1.33 (0.83–1.99) | 28 |
| lag52 | Hail >= 1 in | 1980-1995 | 1.00 (0.72–1.36) | 24 |
| lag52 | Hail >= 1 in | 1996-2023 | 1.21 (0.90–1.56) | 28 |
| lag52 | Hail >= 1 in | ratio_1996-2023_over_1980-1995 | 1.20 (0.75–1.83) | 28 |
| lag52 | Heat-wave days per cell | 1980-1995 | 0.72 (0.37–1.39) | 24 |
| lag52 | Heat-wave days per cell | 1996-2023 | 1.44 (0.53–3.33) | 28 |
| lag52 | Heat-wave days per cell | ratio_1996-2023_over_1980-1995 | 2.01 (0.62–5.90) | 28 |

## 5. Pole-relative strata (source: pole_relative_results.csv, monthly_cell_counts.csv, script 35)

Per-CDPE-month pole classification of 1-degree report cells (≤ 4.0° of a pole; both → nearer pole). Control = the same calendar months of non-CDPE years, classified by the CDPE month's poles; bootstrap resamples CDPE months (B = 2000, seed 20261102). Per-cell counts were rebuilt from the raw StormEvents files under the frozen Step-04 rules and asserted against the frozen totals (54,607 / 229,650 / 379,430) before use. Heat waves are excluded: the heat-wave field is a gridMET-based mean over 3,608 land cells on its own 50 × 118 grid, not report counts on the 1-degree report grid, so report-cell pole strata are not defined for it.

| Hazard | Stratum | RR (95% CI) | CDPE-month reports | Share of CDPE-month reports |
|---|---|---|---|---|
| Tornadoes | near_dry | 0.56 (0.17–0.77) | 98 | 1.4% |
| Tornadoes | near_wet | 2.52 (1.12–5.02) | 447 | 6.3% |
| Tornadoes | elsewhere | 1.16 (0.87–1.55) | 6502 | 92.3% |
| Hail >= 1 in | near_dry | 0.71 (0.28–1.02) | 572 | 2.2% |
| Hail >= 1 in | near_wet | 1.13 (0.69–1.74) | 1062 | 4.1% |
| Hail >= 1 in | elsewhere | 1.04 (0.78–1.35) | 24475 | 93.7% |

## 6. Power / MDES (source: mdes.csv, script 36)

Analytic minimum detectable rate ratio at 80% power, two-sided α = 0.05, ratio-of-means design: MDES = exp((z_0.975 + z_0.80) · sqrt(var_e/n_e + var_u/n_u)), z-sum = 2.8016, where var is the variance of the log monthly count estimated by the delta method (s²/mean²) from the observed group counts (the log of a monthly count is undefined for the zero heat-wave months, so the delta-method variance is the operative input; both group variances are in mdes.csv). The protective-side MDES is the reciprocal.

| Design | Hazard | n exposed | Monthly mean, exp / unexp | MDES RR (harm side) |
|---|---|---|---|---|
| Same-month, aligned 52 | Tornadoes | 52 | 135.5 / 99.9 | 1.67 |
| Same-month, aligned 52 | Hail >= 1 in | 52 | 502.1 / 427.6 | 1.74 |
| Same-month, aligned 52 | Heat-wave days per cell | 52 | 0.2 / 0.3 | 1.87 |
| Same-month, US-anchored 15 | Tornadoes | 15 | 150.7 / 102.0 | 2.05 |
| Same-month, US-anchored 15 | Hail >= 1 in | 15 | 680.3 / 427.8 | 2.11 |
| Same-month, US-anchored 15 | Heat-wave days per cell | 15 | 0.2 / 0.3 | 2.40 |
| Lagged, aligned 52 | Tornadoes | 52 | 146.7 / 98.9 | 1.61 |
| Lagged, aligned 52 | Hail >= 1 in | 52 | 638.5 / 413.6 | 1.65 |
| Lagged, aligned 52 | Heat-wave days per cell | 52 | 0.3 / 0.2 | 2.21 |
| Lagged, US-anchored 15 | Tornadoes | 15 | 124.2 / 103.0 | 1.60 |
| Lagged, US-anchored 15 | Hail >= 1 in | 15 | 629.7 / 430.1 | 1.78 |
| Lagged, US-anchored 15 | Heat-wave days per cell | 15 | 0.2 / 0.3 | 2.42 |

## 7. Jaccard chance baselines (source: jaccard_baselines.csv, script 36)

Expected intersection under random placement = n1·n2/N with N = window months (528 for the 1980–2023 arms; 420 for Arm B, whose run window is Jan 1980–Dec 2014 per its run_manifest.json).

| Comparison | n1 | n2 | Observed ∩ | Expected ∩ | Obs/Exp | Jaccard |
|---|---|---|---|---|---|---|
| SPEI-3 vs SPEI-1 (Arm A baselines) | 48 | 46 | 12 | 4.18 | 2.87 | 0.146 |
| SPEI-6 vs SPEI-1 (Arm A baselines) | 51 | 46 | 4 | 4.44 | 0.90 | 0.043 |
| Companion v2.11 vs Arm A v2.10 SPEI-1 | 52 | 46 | 32 | 4.53 | 7.06 | 0.485 |
| NARR vs ERA5 (Arm B masked baselines) | 44 | 69 | 17 | 7.23 | 2.35 | 0.177 |

## 8. Envelope hail check (source: envelope_hail_excluding1.csv, envelope_hail_check.json, script 36)

Inclusion rule (from rate_ratios_by_config.csv, cdpe-hazards-aas/results — the current copy): included_in_envelope == True in rate_ratios_by_config.csv, i.e. >= 10 CDPE months in the 1980-2023 window (frozen Step 06 envelope rule; 23 of 36 Arm A configurations qualify). Of the 23 included configurations for hail ≥ 1 in, **7** have 95% CIs excluding 1 — the review's claim of 7 of 23 is confirmed. They are:

| Configuration | RR (95% CI) |
|---|---|
| SPEI-3|thr=1.0|r=3.0 | 1.23 (1.04–1.50) |
| SPEI-3|thr=1.0|r=4.0 | 1.30 (1.09–1.59) |
| SPEI-3|thr=1.0|r=5.0 | 1.30 (1.05–1.66) |
| SPEI-3|thr=1.5|r=3.0 | 1.32 (1.05–1.64) |
| SPEI-6|thr=1.0|r=3.0 | 1.33 (1.13–1.59) |
| SPEI-6|thr=1.0|r=4.0 | 1.28 (1.06–1.55) |
| SPEI-6|thr=1.5|r=3.0 | 1.33 (1.02–1.72) |

## 9. Spearman correlation — annual CDPE counts vs annual hazard totals (source: spearman_annual.csv, annual_cdpe_vs_hazards.csv, script 36)

The analysis promised in the current Methods and not previously reported. 44 years (1980–2023); aligned 52 set.

| Hazard | Spearman ρ | p | Years |
|---|---|---|---|
| Tornadoes | -0.136 | 0.378 | 44 |
| Hail >= 1 in | -0.204 | 0.185 | 44 |
| Heat-wave days per cell | 0.017 | 0.911 | 44 |

## 10. Era representation (source: era_representation.json, script 36)

Aligned CDPE months in the early era (1980–1995): 24 of 52 = 46.2%, against the early era's share of the window: 192 of 528 months = 36.4%.

## 11. Masked-control supplement

See `supplement_masked_control.md` in this directory (written by this script from the archived run outputs; every number re-verified there).

## 12. Methods notes

- Same-month and lagged arms are separate designs throughout: in the lagged arm the exposure label of regime month t attaches to outcome month t + 1, and a month can be an exposed outcome in the lagged arm while also being a CDPE month in the same-month arm; the two arms' design columns (design_monthly.csv) are never mixed in one estimate.
- Ratio estimator and its bootstrap are the frozen Step 06 construction (calendar-month stratification, year resampling, B = 2000, percentile intervals). GLM intervals: year-cluster-robust primary, year-block bootstrap (B = 2000, seed 20261102) secondary.
- Dispersion: Poisson Pearson chi2/df ranged from 44.9 to 2048.2 across hazard × arm cells, so the NB is primary in every cell; Poisson IRRs are reported alongside in §2.
- Software: numpy/pandas/scipy/statsmodels (statsmodels 0.15.0); environment versions are printed by the run logs. Seeds: ratio bootstrap 20261026 (frozen); GLM bootstrap, median contrast, and pole-relative bootstrap 20261102. One-command rerun: `bash code/run_phase3.sh`.

## 13. Not constructible / caveats

- **Lagged (and any) SPEI-3 / SPEI-6 regimes on the aligned catalog: not constructible.** The aligned catalog (results/alignment_2026-11-02/) contains only the SPEI-1 sets (companion v2.11 and Arm A v2.10); SPEIbase v2.11 spei03/spei06 fields are not in hand, so no v2.11 SPEI-3 or SPEI-6 month sets exist to lag or to align. All Phase 3 arms are SPEI-1 only.
- Pole-relative analysis for heat waves: not constructible on the report grid (see §5).
- The task brief stated the aligned 52 all fall at or before 2022-03; the catalog's latest month is 2022-04. The lagged design is unaffected (2022-05 is in-window).
- ONI is the ERSST v6 vintage retrieved 2026-11-02; the SEG fallback file is the v5 vintage (r = 0.997 over 1980–2023). GLM results would differ trivially under the v5 series; the v6 CPC file of record was used.
