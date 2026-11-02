---
title: "How much does the definition matter? Concurrent drought-pluvial regimes and the occurrence of tornadoes, hail, and heat waves over the contiguous United States"
author: "Nicholas J. Sokol"
affiliation: "Department of Geography & Sustainability, University of Tennessee, Knoxville, TN, USA"
email: "nsokol@utk.edu"
orcid: "0000-0002-4798-0056"
---

## Abstract

We identify concurrent drought-pluvial events (CDPEs), in which sustained drought in one region coincides with anomalous wetness in another, from standardized indices whose construction involves many analyst choices. How much those choices govern CDPE catalogs, and whether other weather hazards occur at different rates during CDPE regime months, we quantify over the contiguous United States for 1980 to 2023. A 756-configuration sensitivity ensemble shows that the detection threshold and the index fitting distribution dominate CDPE frequency, that configurations agree far less on event timing than on event counts, and that applying a land mask to computed fields removes about 70 percent of baseline events. We then condition tornadoes, hail, and heat waves on CDPE months against calendar-matched non-CDPE months. At the baseline configuration, tornado reports give a rate ratio of 1.13 (95 percent interval 0.83 to 1.50), severe hail 1.10 (0.80 to 1.49), and heat-wave days 0.90 (0.54 to 1.39), with no association passing pre-specified robustness rules and the heat-wave estimate changing sign across the envelope. We report each association as an envelope across configurations, rather than as a single estimate, the minimum standard the sensitivity results support.

**Keywords:** compound events, concurrent drought-pluvial events, SPEI, tornadoes, heat waves, sensitivity analysis

# 1. Introduction

Compound and concurrent extremes cause impacts that single-hazard analyses miss [@zscheischler2020]. One such pattern is the concurrent drought-pluvial event (CDPE), a month in which sustained drought in one part of a domain coincides with anomalous wetness in another, a configuration the literature classifies as spatially compounding [@zscheischler2020; @zscheischler2017]. A reproducible detector for CDPEs over the contiguous United States (CONUS) is described in a companion study [@sokol_cdpe] and applied there to produce a national catalog, and a regional analysis for the Southeastern United States is in revision [@sokol_seg]. Related work has approached the drought-pluvial relationship through event coincidence at a point [@hesheffield2020], through network representations of drought-pluvial dipoles [@wanghe2025], through spatially compounding drought-flood events over Europe [@brunner2025], and through temporal dipoles within subregions of the Great Plains [@christian2015]. Reviews note how thin the United States literature remains [@wheaton2023; @aghakouchak2020].

Every CDPE catalog is the output of a chain of analyst choices: the index product and its release, the accumulation timescale, the fitting distribution, the calibration period, the treatment of evaporative demand, the detection threshold and buffer radius, and whether computed fields are masked to land. For single-index drought assessment, several of these choices move classifications materially [@stagge2015; @begueria2014; @sheffield2012]. For CDPEs the problem compounds, because an event requires a dry and a wet classification to hold at once in different places. The first question of this paper is therefore methodological: which analyst choices explain the most variance in CDPE frequency, and do configurations agree on when events occur, not only on how many occur?

The second question is physical, and it motivates this paper's new analysis. A CDPE month is a large-scale circulation regime, with a ridge over the dry pole and a trough near the wet pole, and such regimes plausibly redistribute more than precipitation. Large-scale climate states modulate severe convective weather: the El Niño-Southern Oscillation shifts tornado and hail frequency over the United States [@allentippett2015], and modeled environments link large hail to the large-scale state [@battaglioli2023]. Heat waves, whose measurement conventions are themselves a methodological literature [@perkins2013; @domeisen2023], are the natural hazard of the dry pole. Hail climatologies carry their own reporting complications [@raupach2021; @allentippett2021]. Yet no study has asked whether tornadoes, hail, or heat waves occur at different rates during CDPE regime months than during comparable non-CDPE months. That question also has a methodological edge. If the answer changes when the CDPE catalog is produced by a different defensible configuration, then hazard claims built on any single catalog inherit the catalog's instability.

We answer both questions with one design. Section 2 describes the detector, a 756-configuration sensitivity ensemble in two arms, the hazard data, and a conditioning estimand that compares hazard rates in CDPE months with calendar-month-matched non-CDPE months. Section 3 reports the sensitivity results in condensed form, then the hazard associations at a baseline configuration and across the configuration envelope. Section 4 discusses what the conditioning does and does not show, and Section 5 concludes. Three contributions follow. We decompose the sensitivity of CDPE detection across the full index-construction chain, not only the detector's own parameters. We condition hazard occurrence on CDPE regimes for the first time. And we report each hazard association as an envelope across configurations, so that its robustness to the choices documented in the first arm is part of the result.

# 2. Data and methods

## 2.1 CDPE detection

We detect CDPEs with the algorithm of the companion study [@sokol_cdpe], implemented in NumPy for this study and validated against the companion study's original code (Section 3.1). For each month's standardized index field over the CONUS bounding box, the detector (1) locates the driest and wettest cells, (2) draws a circular buffer of radius r around each, and (3) qualifies a buffer when fewer than a fraction q of its cells are missing and at least a fraction f of its non-missing cells pass the threshold theta in the appropriate direction. A month is a CDPE month only if both buffers qualify. We classify months independently, with no duration or merging rule. The baseline operating point, taken from the companion study, is 1-month SPEI with theta = 1.5, r = 4 degrees, f = 0.5, and q = 0.10.

## 2.2 Sensitivity design

We vary the choices around that operating point in two arms. Arm A takes precomputed index products, SPEI at 1-, 3-, and 6-month timescales from SPEIbase v2.10 [@begueria2014; @harris2020] and a 1-month SPI [@mckee1993] computed from CRU TS 4.09 precipitation with the climate_indices package [@adams2017] under a gamma fit and a 1981 to 2010 calibration, and varies only theta in {1.0, 1.5, 2.0} and r in {3, 4, 5} degrees, giving 36 scenarios over January 1980 to December 2023. Arm B computes standardized indices from North American Regional Reanalysis (NARR) [@mesinger2006] and ERA5 [@hersbach2020] monthly precipitation and temperature on a common 0.5 degree grid for 1980 to 2014, crossing dataset, timescale (1, 3, 6, 12 months), fitting distribution (three-parameter log-logistic by probability-weighted moments [@vicenteserrano2010; @singh1993], or an empirical transform with the Gringorten plotting position [@gringorten1963]), calibration period, water-balance formulation (SPEI with Thornthwaite evapotranspiration [@thornthwaite1948; @allen1998], or precipitation only), theta, and r, giving 720 scenarios (Table 1). Because reanalysis fields carry values over water, the primary Arm B applies a land mask derived from SPEIbase to every computed field before detection, and we retain the same factorial on unmasked fields as a sensitivity comparison. Our response variable is the number of CDPE months. Variance shares are exact closed shares for the balanced design [@saltelli2008], we measure agreement between configurations with the Jaccard index of month sets [@jaccard1912] and the Spearman correlation of annual counts, and we estimate sampling uncertainty by resampling whole calendar years (B = 2000) [@kunsch1989].

**Table 1.** Factors and levels of the sensitivity design.

| Factor | Arm A (36 scenarios) | Arm B (720 scenarios, twice: land-masked and unmasked) |
|---|---|---|
| Index | SPEI-1, SPEI-3, SPEI-6, SPI-1 | – |
| Dataset | – | NARR, ERA5 |
| Timescale (months) | – | 1, 3, 6, 12 |
| Fitting distribution | – | log-logistic, empirical |
| Calibration period | – | full period, 1981 to 2010 |
| Water balance | – | SPEI, precipitation only |
| Detection threshold theta | 1.0, 1.5, 2.0 | 1.0, 1.5, 2.0 |
| Buffer radius r (degrees) | 3, 4, 5 | 3, 4, 5 |
| Buffer fractions f and q | f = 0.5, q = 0.10 | f = 0.5, q = 0.10 |

## 2.3 Hazard data

We take tornado and hail occurrence from the NOAA Storm Events database [@ncei_storm_events], yearly details files, January 1980 to December 2023. We assign events to the study domain (25 to 50 N, 125 to 66 W) by their begin coordinates, with county centroids from the Census Bureau gazetteer as the fallback for records lacking coordinates (of 434,420 tornado and hail records processed, 413,052 carried usable begin coordinates, we placed 21,178 by county centroid, 190 could not be located and were excluded, and 193 located records fell outside the domain). The primary tornado metric is the monthly count of tornado reports. Pre-specified secondary metrics restrict the count to tornadoes rated F/EF1 or stronger and F/EF2 or stronger. The primary hail metric is the monthly count of hail reports of at least 1.00 inch, the severe-hail criterion in force for most of the record, with all hail reports as the secondary metric. Storm Events reporting is known to be inhomogeneous: counts rose with population, spotter networks, and the deployment of the NEXRAD radar network, weak-tornado reporting is the least homogeneous component [@verbout2006], and hail report characteristics changed over the record [@allentippett2021]. We therefore make no trend claims, and we report a split-era comparison (1980 to 1995 against 1996 to 2023) as a descriptive robustness display.

[FIGURE: fig_map_geography] *Figure 1.* Report geography for the two convective hazards, 1980 to 2023. (a) Tornado and severe-hail (at least 1.00 inch) reports per 1-degree cell (log scale). (b) The share of each cell's reports that fell in the 46 baseline CDPE months, shown for cells with at least 25 reports. CDPE status is a property of the month nationally rather than of place, so panel (b) redistributes the same reports in time: a cell at 8.7 percent holds exactly the share expected if CDPE months drew reports in proportion to their share of the record (46 of 528 months).

We compute heat waves from gridMET daily maximum temperature [@abatzoglou2013], aggregated to the 0.5 degree grid of Arm B by cell-mean binning. Cells valid on at least 99 percent of days in 1981 to 2010 form the land set (3,608 of the 5,900 cells). A cell's heat-wave day is a day in a run of at least three consecutive days above the cell's calendar-day 98th percentile, computed over 1981 to 2010 within a 31-day window, following established percentile-based practice [@perkins2013]. The monthly metric is total heat-wave cell-days divided by the number of land cells, interpretable as mean heat-wave days per cell.

## 2.4 Conditioning estimand and envelope

For hazard h and configuration c, the estimand is a stratified monthly rate ratio. Calendar months form 12 strata. Within each stratum, we compare the mean monthly hazard metric in CDPE months of configuration c with the mean in non-CDPE months of the same calendar month, and we average the stratum ratios with weights equal to the share of c's CDPE months falling in the stratum. Calendar matching absorbs seasonality and month length by construction. We compute intervals from the same whole-year bootstrap as Section 2.2 (B = 2000), recomputing the ratio per replicate. We report associations at the baseline configuration and as an envelope across the 36 Arm A configurations, restricted to configurations with at least 10 CDPE months in the analysis window for tornadoes, hail, and heat waves. We call a hazard association robust only when the baseline interval excludes one and at least 80 percent of envelope configurations place their point estimate on the same side of one as the baseline. We fixed these rules before the hazards analysis ran.

# 3. Results

## 3.1 Sensitivity of CDPE detection

We completed all 756 primary scenarios (36 in Arm A, 720 in masked Arm B), as well as the 720 unmasked Arm B scenarios retained as the mask comparison. At the baseline scenario (SPEI-1, theta = 1.5, r = 4 degrees), Arm A identifies 46 CDPE months over 1980 to 2023, against 52 reported by the companion study over 1980 to 2024 [@sokol_cdpe], and every directly comparable Arm A count is at or below the companion value (Table 2). The companion counts do not reproduce from the staged inputs, even though the companion study's original code returns our month sets exactly on those inputs, and Supplementary Information S1 gives the full comparison, including the SPI-1 count that does not replicate under any construction variant tested. Figure 2 maps the dry and wet pole locations of the 46 baseline months.

**Table 2.** CDPE months in the companion study [@sokol_cdpe] and in Arm A, at f = 0.5 and q = 0.10.

| Configuration | Companion study | Arm A | Ratio |
|---|---|---|---|
| SPEI-1, theta = 1.5, r = 4 degrees | 52 | 46 | 0.88 |
| SPEI-3, theta = 1.5, r = 4 degrees | 64 | 48 | 0.75 |
| SPEI-6, theta = 1.5, r = 4 degrees | 56 | 51 | 0.91 |
| SPEI-1, theta = 1.0, r = 3 degrees | 214 | 189 | 0.88 |
| SPEI-1, theta = 2.0, r = 4 degrees | 0 | 0 | – |
| SPI-1, theta = 1.5, r = 4 degrees | 66 | 22 | 0.33 |

[FIGURE: fig_map_poles] *Figure 2.* Pole geography of the 46 baseline CDPE months (SPEI-1, theta = 1.5, r = 4 degrees), 1980 to 2023. (a) Dry poles: the number of baseline months whose driest pole fell in each 1-degree cell (43 cells occupied, at most 3 months in any cell), with the 46 dry-pole locations overlaid as white points. (b) Wet poles: as in (a), for the wettest pole (42 cells occupied). A single colour scale serves both panels. The basemap shows North American land across the full analysis domain (25 to 50 N, 125 to 66 W), and the poles are plotted where they fall, including cells in Canada, Mexico, and the ocean margins of the domain.

CDPE frequency spans orders of magnitude across configurations (Figure 3). Arm A returns 0 to 189 CDPE months (median 45.5), and masked Arm B returns 0 to 170 (median 2), with 272 of the 720 masked Arm B scenarios returning zero, concentrated at the strictest thresholds. The neighborhood of each baseline is steep: in Arm A at theta = 1.5, SPEI-1 counts fall from 84 to 46 to 20 as r rises from 3 to 5 degrees, and at r = 4 degrees they fall from 140 to 46 to 0 as theta rises from 1.0 to 2.

[FIGURE: fig_s1_count_heatmaps] *Figure 3.* CDPE months by detection threshold and buffer radius in Arm A. Counts fall monotonically in the threshold within every group, and the baseline (theta = 1.5, r = 4 degrees, 46 months) sits midway down a steep gradient.

The detection threshold holds the largest single variance share in both arms (Figure 4). In Arm A, threshold accounts for 0.76 of the variance in CDPE months, followed by radius (0.13), the threshold by radius interaction (0.06), and index (0.03). In masked Arm B, threshold's share falls to 0.32 and the fitting distribution (0.19) with its threshold interaction (0.17) together contributes as much, while dataset (0.011), timescale (0.010), water balance (0.010), and calibration period (effectively zero) contribute little. On the restricted grid theta in {1.0, 1.5} the order of threshold and distribution reverses (0.21 against 0.31), so we report the two as co-dominant in Arm B. Part of the distribution effect is a detector artifact rather than a property of either standardization: the empirical transform ties many cells at each pole value, the detector's first-occurrence rule parks the poles at the southernmost tied cell, and the coastal missing-data gate then rejects most of those months. Breaking pole ties at random returns 57 to 80 CDPE months at the Arm B baseline configuration rather than 6 under the empirical fit (44 under the log-logistic fit).

[FIGURE: fig_s2_variance] *Figure 4.* Variance shares of CDPE months in masked Arm B (720 scenarios). Threshold (0.32), fitting distribution (0.19), and their interaction (0.17) dominate, and calibration period contributes essentially nothing.

Agreement on timing is far weaker than agreement on counts. In Arm A, SPEI-3 and SPEI-6 at the baseline settings return near-baseline counts (48 and 51 months against 46) but share few months with the baseline (Jaccard 0.146 and 0.043), so a change of timescale replaces the catalog rather than resampling it. In masked Arm B, NARR and ERA5 at otherwise identical baseline settings share 17 CDPE months (Jaccard 0.177, which is 39 percent of NARR's 44 months and 25 percent of ERA5's 69), although dataset choice explains only about 1 percent of the count variance. Bootstrap intervals for baseline rates are narrow (Arm A SPEI-1: 1.05 months per year, 95 percent interval 0.77 to 1.34) relative to the across-configuration spread, so sampling uncertainty is not the binding uncertainty in CDPE frequency. The land mask is itself a first-order choice: unmasked, 58.9 percent of NARR and 70.0 percent of ERA5 baseline CDPE months anchor at least one pole over water, and masking removes about 70 percent of baseline months (NARR 175 to 44, ERA5 217 to 69), with the survivors largely different months rather than subsets (Jaccard 0.237 and 0.212).

## 3.2 Hazard occurrence in CDPE months at the baseline configuration

Over 1980 to 2023 the domain recorded 54,607 tornado reports (25,533 rated F/EF1 or stronger and 7,958 rated F/EF2 or stronger) and 379,430 hail reports, of which 229,650 were at least 1.00 inch (Figure 1). At the baseline configuration (46 CDPE months), hazard occurrence in CDPE months, relative to calendar-matched non-CDPE months, was as follows (Figure 5, Table 3). Tornadoes: the rate ratio was 1.13 (95 percent interval 0.83 to 1.50). Severe hail: the rate ratio was 1.10 (0.80 to 1.49). Heat waves: heat-wave days per cell gave a rate ratio of 0.90 (0.54 to 1.39), the only primary estimate below one.

[FIGURE: fig_h1_forest] *Figure 5.* Baseline rate ratios (points, 95 percent bootstrap intervals) and configuration envelopes (shaded bands) for hazard occurrence in CDPE months. The dashed line marks a rate ratio of one.

**Table 3.** Rate ratios for hazard occurrence in CDPE months against calendar-matched non-CDPE months. Baseline configuration (SPEI-1, theta = 1.5, r = 4 degrees) with 95 percent bootstrap intervals, and the envelope across included configurations (23 configurations). The final column gives the share of envelope configurations whose point estimate lies on the same side of one as the baseline.

| Hazard | Baseline rate ratio (95% interval) | Envelope range | Share on baseline side |
|---|---|---|---|
| Tornadoes (all reports) | 1.13 (0.83 to 1.50) | 0.99 to 1.50 | 0.96 |
| Tornadoes (F/EF1 or stronger) | 1.22 (0.81 to 1.73) | 0.91 to 1.86 | 0.87 |
| Tornadoes (F/EF2 or stronger) | 1.21 (0.69 to 1.84) | 0.78 to 2.05 | 0.65 |
| Hail (at least 1.00 in) | 1.10 (0.80 to 1.49) | 0.86 to 1.53 | 0.96 |
| Hail (all reports) | 1.10 (0.81 to 1.42) | 0.94 to 1.45 | 0.96 |
| Heat-wave days per cell | 0.90 (0.54 to 1.39) | 0.56 to 2.62 | 0.30 |

## 3.3 The configuration envelope

The envelope answers whether those associations are properties of the climate or of the baseline catalog (Figure 6). Across the 23 included configurations, tornado rate ratios ran from 0.99 to 1.50 and severe-hail ratios from 0.86 to 1.53, with 96 percent of configurations on the same side of one as the baseline in both cases. The direction of the convective association is therefore stable across the envelope even though its size is not. No tornado configuration's interval excluded one (a share of 0.00), against 30 percent of configurations for severe hail. Heat waves behaved differently: only 30 percent of configurations placed their point estimate on the baseline's side of one, and the envelope ran from 0.56 to 2.62, the widest of any hazard, so the baseline estimate of 0.90 sits in a small lower cluster while most configurations return values above one. Under the rules fixed in Section 2.4, no hazard association is robust. Every baseline interval includes one, so the first condition fails for all three primary hazards, and heat waves also fail the envelope-agreement condition. The defensible summary is therefore narrow: CDPE months carry point estimates of roughly one tenth more tornado and severe-hail reports at the baseline configuration, with the sign of those estimates stable across configurations, and no detectable difference for heat waves.

[FIGURE: fig_h2_envelope] *Figure 6.* Rate ratios across the configuration envelope for the three primary hazards. Each point is one included configuration, sorted by rate ratio. The vertical dashed line marks one, and the vermilion line and point mark the baseline estimate.

## 3.4 Robustness displays

Secondary metrics and the split-era comparison qualify the headline associations (Figure 7). Restricting tornado counts to rated events strengthens the point estimates without narrowing the intervals: tornadoes rated F/EF1 or stronger gave 1.22 (0.81 to 1.73) and F/EF2 or stronger gave 1.21 (0.69 to 1.84), with envelope agreement falling to 87 and 65 percent, so the apparent strengthening comes with wider uncertainty and weaker cross-configuration support. All hail reports matched the severe subset (1.10, 0.81 to 1.42). The split-era display tempers any physical reading of the convective elevation: tornado ratios were 1.02 (0.75 to 1.38) in 1980 to 1995 and 1.20 (0.78 to 1.64) in 1996 to 2023, and severe hail moved from 0.91 (0.68 to 1.23) to 1.19 (0.94 to 1.53). The elevation is concentrated in the era of denser reporting, although the era intervals overlap widely, and the baseline catalog supplies 21 CDPE months to the early era against 25 to the later one.

[FIGURE: fig_h3_series] *Figure 7.* Monthly hazard series, 1980 to 2023, with baseline CDPE months shaded. Panels: (a) tornado reports, (b) hail reports of at least 1.00 inch, (c) heat-wave days per cell.

# 4. Discussion

The sensitivity arm establishes the ground rule for everything that follows. A CDPE count is a joint property of the climate and the analyst's settings, dominated by the detection threshold and by how the index is fitted, and two defensible configurations that return similar counts generally return different months. Any downstream use of a CDPE catalog, including the hazard conditioning of this paper, inherits that instability unless it is reported as an envelope. That is why we state the hazard results twice, once at the baseline configuration and once across the Arm A envelope, and why we fixed the robustness rules before the hazards analysis ran.

What should be made of point estimates near 1.1 for the convective hazards? The sign stability across 23 configurations (96 percent for both tornadoes and severe hail) says the elevation is not an artifact of the baseline catalog choice. Its size, however, is small next to the reporting inhomogeneity of the underlying records, and the split-era pattern, flat in 1980 to 1995 and elevated in 1996 to 2023, is the pattern a reporting-driven signal would produce. A physical channel exists in principle. CDPE regimes reorganize moisture transport and instability, most directly over the wet pole, and recent work on compound drought and heat over the CONUS [@yoon2024] and on the environments that produce very large hail [@das2024] shows how strongly convective outcomes respond to exactly those fields. The domain-wide monthly estimand used here cannot separate that channel from reporting, and the honest conclusion is that the convective elevation is suggestive and unresolved.

Heat waves were the hazard with the strongest prior for an association, through the dry pole, and they return the weakest and least stable result: the baseline catalog gives 0.90 while most other catalogs give values above one, up to 2.62. That inversion is itself a finding about method. A study built on a different defensible catalog could have reported a substantial heat-wave elevation, and nothing inside a single-catalog analysis would have flagged the catalog choice as load-bearing. The same warning applies in reverse to the convective hazards: their sign stability across this envelope is evidence, but it is evidence about this family of configurations, and a differently constructed index family could move it.

Two limitations bound the hazard arm. First, the estimand is domain-wide and monthly. A CDPE regime pairs a dry pole with a wet pole inside the same domain, so opposing local effects on convective hazards can cancel in a domain total, and a null domain-wide ratio does not imply null local effects. Pole-relative conditioning is the natural next step and requires the pole locations. The saved month sets used here do not carry them, so we recovered them by re-running the frozen detector, which reproduced the archived month sets exactly across all 27 scenarios, and Figure 2 plots the recovered locations for the baseline months. Second, the hazard records are inhomogeneous. Tornado and hail reporting improved across the record [@verbout2006; @allentippett2021], and calendar matching does not remove reporting trends that differ between the years that supply CDPE months and the years that supply their controls. The split-era display is the check on that confound, and the year bootstrap does not correct it.

The sensitivity arm has its own limits, carried from the parent design. Both arms use a rectangular domain that includes land in southern Canada and northern Mexico, so neither is an analysis of United States territory as such. Arm A takes SPEIbase's fitting as given while Arm B substitutes this study's fits, so cross-arm contrasts combine those sources. In Arm B, Thornthwaite evapotranspiration depends only on temperature, regridding is by linear interpolation, and ERA5 temperature uses four synoptic hours. Variance shares depend on the factor levels chosen, and the bootstrap does not refit the index. Finally, the detector's missing-data gate discounts coastal poles, so every catalog here is a catalog of dipoles anchored inland. We inherit that selection from the detector rather than introducing it here, and it bounds the population of regimes to which the hazard statements apply.

# 5. Conclusions

Two conclusions survive the envelope discipline this paper applies to itself. First, analyst choices govern CDPE frequency more than sampling noise: the detection threshold and the index fitting distribution dominate the variance, configurations that agree on counts disagree on months, and the land-mask decision alone removes about 70 percent of baseline events. Any use of a CDPE catalog should therefore state its configuration and, where claims depend on the catalog, report an envelope across defensible configurations. Second, conditioning three hazards on CDPE regime months returns no robust association at the baseline configuration. Tornado and severe-hail reports carry small positive point estimates whose sign is stable across configurations but whose size neither the data nor the reporting record can pin down, and heat-wave occurrence is configuration-fragile to the point of changing sign across the envelope. The contribution is the pairing of the two arms: hazard claims about regime catalogs are only as strong as the catalog sensitivity reported beside them.

# Acknowledgments

The author thanks the developers and providers of the SPEIbase, CRU TS, NARR, ERA5, gridMET, and Storm Events datasets used in this study.

# Statements and Declarations

## Funding

This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

## Competing Interests

The author declares no competing interests.

## Author Contributions

Nicholas J. Sokol conceived and designed the study, performed the data collection and analysis, and wrote the manuscript.

## Data Availability

Source data are publicly available: SPEIbase from the CSIC SPEI database, CRU TS from the Climatic Research Unit, NARR from the NOAA Physical Sciences Laboratory, ERA5 through the ARCO-ERA5 mirror and the Copernicus Climate Data Store, gridMET from the University of Idaho, Storm Events from NOAA NCEI. All analysis code for this paper, including data acquisition, the hazards arm, and figure generation, together with the CDPE month sets for both sensitivity arms, is deposited in a public GitHub repository (github.com/Nsokol44/cdpe-hazards).
