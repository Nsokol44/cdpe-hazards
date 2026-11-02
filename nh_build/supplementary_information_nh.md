---
title: "Supplementary Information"
author: "Nicholas J. Sokol"
affiliation: "Department of Geography & Sustainability, University of Tennessee, Knoxville, TN, USA"
---

Supplementary Information for the manuscript "How much does the definition matter? Concurrent drought-pluvial regimes and the occurrence of tornadoes, hail, and heat waves over the contiguous United States", submitted to Natural Hazards.

## S1. The aligned catalog and the Arm A port

The headline catalog of the main text is the companion Study-1 catalog: the frozen Study-1 detector at its baseline settings (SPEI-1, threshold 1.5, radius 4.0 degrees, f = 0.5, q = 0.10) on the SPEIbase v2.11 field, giving 52 CDPE months over 1980 to 2023 and no month in 2024. The Arm A port of the same detector on the staged SPEIbase v2.10 field gives 46 months at the same settings. The difference is a release difference, and it is proven rather than inferred. The detector port is faithful on both fields: run on the v2.11 field it returns exactly the 52 aligned months, and run on the v2.10 field it returns the 46 Arm A months, and the original Study-1 code returns the same month sets on common inputs. The two releases rest on different CRU versions (v2.10 on CRU TS 4.08 and v2.11 on CRU TS 4.09), and their fields put the detector pole buffers on opposite sides of the qualification line in 34 of the 66 distinct months involved. The earlier statement that both studies used the same SPEIbase release was wrong and is withdrawn.

The month-level difference is symmetric. The intersection is 32 months, the Jaccard index is 0.485, and 4.5 shared months would be expected by chance for catalogs of 46 and 52 months over a 528-month window. The 14 months only in Arm A (v2.10) are: 1982-02, 1984-01, 1985-07, 1990-06, 1990-11, 1994-03, 1995-07, 1998-01, 2005-04, 2006-06, 2007-11, 2008-04, 2008-08, and 2023-07. The 20 months only in the aligned catalog (v2.11) are: 1981-03, 1985-09, 1987-03, 1988-04, 1989-02, 1989-11, 1991-07, 1992-01, 1993-03, 1995-11, 1999-05, 1999-08, 2004-09, 2004-11, 2007-05, 2009-09, 2013-06, 2016-10, 2020-10, and 2022-03.

The 15 US-anchored months of the aligned catalog, in which both poles fall inside the CONUS land area (Natural Earth), are: 1980-05, 1987-12, 1988-04, 1995-03, 1999-08, 2001-04, 2004-05, 2004-09, 2005-02, 2007-05, 2011-12, 2013-06, 2015-06, 2016-10, and 2020-05.

Two parts of the alignment cannot be completed from the inputs in hand. SPEIbase v2.11 files for SPEI-3 and SPEI-6 could not be obtained, so no aligned multi-month month sets exist, and the Arm A SPEI-3 and SPEI-6 counts (48 and 51 months on v2.10 at the baseline settings) have no v2.11 counterparts. The companion SPI-1 count does not replicate under the documented specification used for the Arm A SPI-1 sets (22 months at the baseline settings), and SPI-1 appears in this paper only as a member of the Arm A envelope family.

## S2. Corrected Arm B: the tie-break fix, baseline counts, and variance decomposition

The original Arm B detector selected each pole as the first cell attaining the field minimum or maximum in index order. The empirical transform caps the standardized value at about 2.146 in absolute value for a 35-year record, so many land cells tie exactly at each pole value in every month, and the log-logistic fit has a smaller clip plateau at 4.753. First-occurrence selection parks a tied pole at the southernmost tied cell, where a 4.0-degree buffer usually fails the missing-data gate, so tied configurations returned few or no CDPE months for a reason that has nothing to do with the climate field.

The corrected detector changes only pole selection. All finite cells exactly equal to the field minimum (dry pole) or maximum (wet pole) are collected. A unique extremum is selected as before. With k tied cells, one is chosen uniformly at random among them. Randomness is deterministic: the generator for each pole and month is seeded with the first 8 bytes (little-endian) of the SHA-256 hash of a documented string that encodes the base seed (20261102), the full scenario key, the month index, and the pole. The archived masked run reproduces exactly (720 of 720 scenarios) under the original detector before the fix is applied, and the corrected baseline scenario reruns bit-identically under the fix.

Under the original rule, 272 of the 720 masked scenarios returned zero CDPE months (241 of 360 empirical scenarios and 31 of 360 log-logistic scenarios). Under the corrected rule, 58 of 720 return zero (26 empirical and 32 log-logistic). Corrected baseline counts at threshold 1.0, radius 4.0 degrees, full calibration, and SPEI water balance are:

| Dataset | Timescale (months) | Fitting distribution | Months before the fix | Months after the fix |
|---|---|---|---|---|
| NARR | 1 | Empirical | 9 | 80 |
| NARR | 1 | Log-logistic | 55 | 62 |
| NARR | 3 | Empirical | 3 | 79 |
| NARR | 3 | Log-logistic | 55 | 55 |
| NARR | 6 | Empirical | 6 | 68 |
| NARR | 6 | Log-logistic | 44 | 50 |
| NARR | 12 | Empirical | 2 | 55 |
| NARR | 12 | Log-logistic | 25 | 26 |
| ERA5 | 1 | Empirical | 18 | 112 |
| ERA5 | 1 | Log-logistic | 79 | 88 |
| ERA5 | 3 | Empirical | 13 | 116 |
| ERA5 | 3 | Log-logistic | 66 | 71 |
| ERA5 | 6 | Empirical | 27 | 109 |
| ERA5 | 6 | Log-logistic | 69 | 74 |
| ERA5 | 12 | Empirical | 8 | 85 |
| ERA5 | 12 | Log-logistic | 34 | 42 |

Seed sensitivity at the masked NARR SPEI-6 empirical baseline is modest: varying the base seed over five values gives 68 to 84 months, with a mean of 76.6, against 6 months under the first-occurrence rule.

The corrected variance decomposition of CDPE month counts (exact closed shares of the balanced 720-scenario design) is:

| Factor | Raw counts, before | Raw counts, after | Log counts, before | Log counts, after |
|---|---|---|---|---|
| Threshold | 0.319 | 0.641 | 0.445 | 0.786 |
| Radius | 0.066 | 0.126 | 0.046 | 0.120 |
| Fitting distribution | 0.188 | 0.005 | 0.345 | 0.0003 |
| Distribution by threshold | 0.167 | 0.012 | 0.052 | 0.005 |
| Dataset | 0.011 | 0.023 | 0.013 | 0.018 |
| Timescale | 0.010 | 0.008 | 0.006 | 0.008 |
| Water balance | 0.010 | 0.006 | 0.000 | 0.000 |
| Calibration period | 0.000 | 0.001 | 0.000 | 0.004 |
| Higher-order interactions | 0.072 | 0.028 | 0.052 | 0.035 |

Log counts are log(1 + n), the zero-safe log used because 272 of the 720 original scenarios are exactly zero. In Arm A, where the tie problem does not arise (the SPEIbase and CRU fields are continuous and tie-free), the threshold share is 0.759 on raw counts and 0.854 on log counts, the radius share is 0.127 and 0.076, and the index share is 0.031 and 0.035. After the fix, the threshold dominates in both arms and on both scales, the radius is second, and the fitting distribution contributes essentially nothing in Arm B. The distribution sensitivity of the original Arm B was substantially a tie-breaking artifact.

## S3. The nClimGrid masked control: how much of the SPEI difference is coverage geometry?

When the CDPE detector (threshold 1.5, radius 4.0 degrees, frozen gates) is run on nClimGrid-derived SPEI instead of SPEIbase, the baseline month counts collapse, for SPEI-1 from 46 months to 3 over January 1980 to December 2023. This section reports the masked control that decomposes that collapse. The control re-runs the detector on the unchanged SPEIbase v2.10 fields with one modification: every cell that is invalid in the aggregated nClimGrid product is set to missing, so the SPEIbase values are seen through the nClimGrid coverage mask and nothing else changes.

Baseline CDPE month counts (threshold 1.5, r = 4.0 degrees):

| Index | SPEIbase (full grid) | SPEIbase under the CONUS mask | nClimGrid |
|---|---|---|---|
| SPEI-1 | 46 | 10 | 3 |
| SPEI-3 | 48 | 15 | 8 |
| SPEI-6 | 51 | 14 | 8 |

For SPEI-1, the mask alone accounts for 46 to 10 of the 46 to 3 collapse, and the remaining 10 to 3 is a difference in the product values on the months the coverage gate lets through. The gate arithmetic is the dominant term: laying the CONUS mask over unchanged SPEIbase values raises the number of months failing the coverage gate (either pole) from 296 to 436 of 528 months, because any pole within 4 degrees of a coast, the northern border, or the Great Lakes then has more than 10 percent missing buffer cells. The mask leaves 3,575 valid cells of the 5,900-cell domain, against 4,399 for the SPEIbase grid.

The value difference is real but secondary. Among valid cell-months at SPEI-1, the dry tail (values at or below -1.5) holds 3.9 percent of cell-months in the nClimGrid gamma product against 5.7 percent in SPEIbase, while the wet tails (at or above +1.5) are nearly identical (8.1 percent against 7.9 percent). A thinner dry tail converts fewer gate-passing months even where coverage is equal.

Reading. Where both products have data they are recognisably the same phenomenon, but the frozen coverage gate is silently a rule about geographic coverage: on a CONUS-only grid it disqualifies most months before their values are ever tested. Product comparisons of CDPE counts that do not hold coverage fixed confound the gate with the climate signal.

## S4. Split-era rate ratios

Within-era ratios use the calendar-stratified ratio-of-means estimator with the year bootstrap restricted to the era years. The era difference is the ratio of the 1996 to 2023 ratio to the 1980 to 1995 ratio, with its own bootstrap interval. Exposed months are 24 in the early era and 28 in the later era for both arms.

| Arm | Hazard | 1980 to 1995 | 1996 to 2023 | Era difference |
|---|---|---|---|---|
| Same-month, aligned 52 | Tornadoes | 0.90 (0.66 to 1.19) | 1.33 (0.82 to 1.76) | 1.47 (0.85 to 2.24) |
| Same-month, aligned 52 | Hail (at least 1.00 in) | 0.77 (0.60 to 0.98) | 1.08 (0.83 to 1.41) | 1.41 (0.98 to 2.01) |
| Same-month, aligned 52 | Heat-wave days per cell | 0.75 (0.39 to 1.47) | 0.99 (0.43 to 1.84) | 1.32 (0.46 to 3.28) |
| Lagged, aligned 52 | Tornadoes | 0.96 (0.70 to 1.30) | 1.28 (0.91 to 1.67) | 1.33 (0.83 to 1.99) |
| Lagged, aligned 52 | Hail (at least 1.00 in) | 1.00 (0.72 to 1.36) | 1.21 (0.90 to 1.56) | 1.20 (0.75 to 1.83) |
| Lagged, aligned 52 | Heat-wave days per cell | 0.72 (0.37 to 1.39) | 1.44 (0.53 to 3.33) | 2.01 (0.62 to 5.90) |

Every era-difference interval includes 1, so no era difference is distinguishable from noise.

## S5. Median contrasts

Median monthly hazard counts in exposed and unexposed months, with the median ratio and a year-bootstrap interval (B = 2000). The US-anchored lagged hail contrast is the only median interval excluding 1, and the median contrasts are descriptive companions to the primary estimators, not tests.

| Arm | Hazard | Median, exposed | Median, unexposed | Median ratio (95 percent interval) |
|---|---|---|---|---|
| Same-month, aligned 52 | Tornadoes | 76.0 | 72.0 | 1.06 (0.65 to 1.94) |
| Same-month, aligned 52 | Hail (at least 1.00 in) | 189.0 | 184.0 | 1.03 (0.63 to 2.07) |
| Same-month, aligned 52 | Heat-wave days per cell | 0.079 | 0.086 | 0.91 (0.28 to 1.93) |
| Same-month, US-anchored 15 | Tornadoes | 131.0 | 72.0 | 1.82 (0.33 to 3.16) |
| Same-month, US-anchored 15 | Hail (at least 1.00 in) | 337.0 | 182.0 | 1.85 (0.80 to 6.80) |
| Same-month, US-anchored 15 | Heat-wave days per cell | 0.144 | 0.085 | 1.69 (0.28 to 3.20) |
| Lagged, aligned 52 | Tornadoes | 91.5 | 71.0 | 1.29 (0.91 to 2.04) |
| Lagged, aligned 52 | Hail (at least 1.00 in) | 357.0 | 181.0 | 1.97 (0.68 to 3.61) |
| Lagged, aligned 52 | Heat-wave days per cell | 0.072 | 0.086 | 0.83 (0.36 to 2.24) |
| Lagged, US-anchored 15 | Tornadoes | 94.0 | 72.0 | 1.31 (0.97 to 1.98) |
| Lagged, US-anchored 15 | Hail (at least 1.00 in) | 565.0 | 181.0 | 3.12 (1.06 to 5.96) |
| Lagged, US-anchored 15 | Heat-wave days per cell | 0.095 | 0.086 | 1.09 (0.36 to 2.75) |

## S6. Leave-one-month-out ranges

Range of the stratified ratio point estimate when each exposed month is left out in turn.

| Arm | Hazard | Leave-one-out range | Months left out |
|---|---|---|---|
| Same-month, aligned 52 | Tornadoes | 0.99 to 1.20 | 52 |
| Same-month, aligned 52 | Hail (at least 1.00 in) | 0.92 to 1.05 | 52 |
| Same-month, aligned 52 | Heat-wave days per cell | 0.76 to 0.92 | 52 |
| Same-month, US-anchored 15 | Tornadoes | 0.84 to 1.06 | 15 |
| Same-month, US-anchored 15 | Hail (at least 1.00 in) | 0.92 to 1.11 | 15 |
| Same-month, US-anchored 15 | Heat-wave days per cell | 0.74 to 1.04 | 15 |
| Lagged, aligned 52 | Tornadoes | 0.98 to 1.15 | 52 |
| Lagged, aligned 52 | Hail (at least 1.00 in) | 1.03 to 1.14 | 52 |
| Lagged, aligned 52 | Heat-wave days per cell | 0.86 to 1.19 | 52 |
| Lagged, US-anchored 15 | Tornadoes | 0.82 to 0.92 | 15 |
| Lagged, US-anchored 15 | Hail (at least 1.00 in) | 0.90 to 1.03 | 15 |
| Lagged, US-anchored 15 | Heat-wave days per cell | 0.51 to 0.67 | 15 |

## S7. Pole-relative strata

The pole-relative table of the main text (its Table 3) is repeated here for completeness. Cells within 4.0 degrees of both poles are assigned to the nearer pole, and controls are the same calendar months of non-CDPE years classified by the CDPE month poles.

| Hazard | Stratum | Rate ratio (95 percent interval) | CDPE-month reports | Share of CDPE-month reports |
|---|---|---|---|---|
| Tornadoes | Near dry pole | 0.56 (0.17 to 0.77) | 98 | 1.4 percent |
| Tornadoes | Near wet pole | 2.52 (1.12 to 5.02) | 447 | 6.3 percent |
| Tornadoes | Elsewhere | 1.16 (0.87 to 1.55) | 6,502 | 92.3 percent |
| Hail (at least 1.00 in) | Near dry pole | 0.71 (0.28 to 1.02) | 572 | 2.2 percent |
| Hail (at least 1.00 in) | Near wet pole | 1.13 (0.69 to 1.74) | 1,062 | 4.1 percent |
| Hail (at least 1.00 in) | Elsewhere | 1.04 (0.78 to 1.35) | 24,475 | 93.7 percent |

Heat waves have no pole-relative strata, because the heat-wave field is a gridMET mean over its own land grid rather than report counts on the 1-degree report grid.

## S8. The seven hail configurations with intervals excluding 1

Of the 23 included Arm A envelope configurations for severe hail (at least 10 CDPE months), exactly seven have 95 percent intervals excluding 1. All seven are SPEI-3 or SPEI-6 configurations.

| Configuration | Rate ratio (95 percent interval) |
|---|---|
| SPEI-3, threshold 1.0, radius 3.0 degrees | 1.23 (1.04 to 1.50) |
| SPEI-3, threshold 1.0, radius 4.0 degrees | 1.30 (1.09 to 1.59) |
| SPEI-3, threshold 1.0, radius 5.0 degrees | 1.30 (1.05 to 1.66) |
| SPEI-3, threshold 1.5, radius 3.0 degrees | 1.32 (1.05 to 1.64) |
| SPEI-6, threshold 1.0, radius 3.0 degrees | 1.33 (1.13 to 1.59) |
| SPEI-6, threshold 1.0, radius 4.0 degrees | 1.28 (1.06 to 1.55) |
| SPEI-6, threshold 1.5, radius 3.0 degrees | 1.33 (1.02 to 1.72) |

## S9. Catalog agreement and chance baselines

Observed intersections of month sets beside the intersections expected if the two sets were placed at random over the window. The expected value is the product of the set sizes divided by the window length.

| Comparison | Set sizes | Observed shared months | Expected by chance | Observed over expected | Jaccard index |
|---|---|---|---|---|---|
| SPEI-3 against SPEI-1 (Arm A baselines) | 48 and 46 | 12 | 4.18 | 2.87 | 0.146 |
| SPEI-6 against SPEI-1 (Arm A baselines) | 51 and 46 | 4 | 4.44 | 0.90 | 0.043 |
| Aligned v2.11 against Arm A v2.10 (SPEI-1) | 52 and 46 | 32 | 4.53 | 7.06 | 0.485 |
| NARR against ERA5 (Arm B masked baselines) | 44 and 69 | 17 | 7.23 | 2.35 | 0.177 |

The SPEI-3 overlap is about three times the chance level, while the SPEI-6 overlap with SPEI-1 is at chance (4 observed against 4.44 expected), so a change of timescale to SPEI-6 replaces the catalog rather than resampling it. The aligned and Arm A SPEI-1 catalogs overlap far above chance, as two releases of one product should, and the NARR and ERA5 baseline catalogs also overlap above chance while sharing only a minority of their months.

## S10. Minimum detectable effect sizes and annual correlations

Analytic minimum detectable rate ratios at 80 percent power, two-sided alpha of 0.05, under the ratio-of-means design. The protective-side value is the reciprocal.

| Design | Hazard | Exposed months | MDES (rate ratio) |
|---|---|---|---|
| Same-month, aligned 52 | Tornadoes | 52 | 1.67 |
| Same-month, aligned 52 | Hail (at least 1.00 in) | 52 | 1.74 |
| Same-month, aligned 52 | Heat-wave days per cell | 52 | 1.87 |
| Same-month, US-anchored 15 | Tornadoes | 15 | 2.05 |
| Same-month, US-anchored 15 | Hail (at least 1.00 in) | 15 | 2.11 |
| Same-month, US-anchored 15 | Heat-wave days per cell | 15 | 2.40 |
| Lagged, aligned 52 | Tornadoes | 52 | 1.61 |
| Lagged, aligned 52 | Hail (at least 1.00 in) | 52 | 1.65 |
| Lagged, aligned 52 | Heat-wave days per cell | 52 | 2.21 |
| Lagged, US-anchored 15 | Tornadoes | 15 | 1.60 |
| Lagged, US-anchored 15 | Hail (at least 1.00 in) | 15 | 1.78 |
| Lagged, US-anchored 15 | Heat-wave days per cell | 15 | 2.42 |

Spearman correlations between annual CDPE month counts (aligned catalog) and annual hazard totals, 44 years (1980 to 2023): tornadoes -0.14 (p = 0.38), severe hail -0.20 (p = 0.19), and heat-wave days 0.02 (p = 0.91). Era representation: 24 of the 52 aligned months (46.2 percent) fall in 1980 to 1995, against that era share of 36.4 percent of the 528-month window.
