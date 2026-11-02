# Delta report — CDPE hazards analysis rerun on nClimGrid SPEI (replacing SPEIbase)

Run date: 2026-11-01/02. Scope: the hazards paper only (AAS submission
AAS-2026-0874 and its Natural Hazards retarget — one analysis). No
manuscript or package file was edited. The detector, all thresholds,
gates, seeds and hazards-pipeline definitions are the frozen ones; only
the SPEI input product changed, plus the window extension the author
directed on 2026-11-01. Every number below traces to a run output file
named in §9.

## Baseline CDPE month counts (threshold 1.5, radius 4.0°, majority 0.5, max-NaN 0.10)

| Index | SPEIbase v2.10, 1980–2023 (of record) | nClimGrid, 1980–2023 (like-for-like) | nClimGrid, 1980–2026-07 (extended, headline) |
|---|---|---|---|
| SPEI-1 | **46** | **3** | **3** |
| SPEI-3 | **48** | **8** | **8** |
| SPEI-6 | **51** | **8** | **8** |

The extended window adds **zero** baseline CDPE months: every baseline
month at every timescale falls before 2024 (the 2024-01–2026-07 segment
contributes no CDPE month at any threshold ≥ 1.5; see §5). The collapse
from 46/48/51 to 3/8/8 is a property of the product swap, and its cause
is decomposed in §3: at the baseline configuration the frozen max-NaN
coverage gate alone rejects 82–87% of months on the CONUS-masked
nClimGrid grid (vs 56–60% on the SPEIbase grid), and most of the few
gate-passing months then fail the within-buffer majority test. No gate
or parameter was adjusted.

## 1. What was substituted

- **New input:** NOAA NCEI NIDIS gridded SPEI, gamma variant, 1/3/6-month
  timescales, period-of-record netCDF (1895-01–2026-09), aggregated to
  the Arm A 0.5° grid by exact spherical-overlap area weighting
  (`cdpe_sensitivity/data_nclimgrid/`, manifest `DATA_MANIFEST.md`).
- **Provenance flag:** the brief named the drought.gov "SPEI from
  nClimGrid-Daily" product; that product exists only as Climate Engine
  current-condition snapshots, with no downloadable monthly archive.
  The files used are the official downloadable gridded monthly SPEI of
  the same nClimGrid family, derived per the archive readme from
  **nClimGrid-Monthly** (not -Daily) temperature and precipitation.
- **Variant flag:** the archive carries gamma and Pearson III variants;
  gamma was chosen because the product-family description for these
  standardized indices names the gamma distribution (the Pearson 1-month
  file is archived alongside for reversibility). SPEIbase fits a
  log-logistic distribution, so neither variant is a distributional
  match to the old product.
- **Calibration flag:** the files' own metadata give a calibration
  period of **1895–2014** (not the 1991–2020 of the Climate Engine
  pages).
- **Coverage:** the product is CONUS-land-masked. Valid 0.5° cells on
  the Arm A grid: **3,575** of 5,900 (static across the record), vs
  **4,399** for the SPEIbase grid over the same box. Coverage map:
  `run_armA_nclimgrid_ext_2026-11-01/coverage_map.png`.
- **No SPI-1 arm exists under the new product** (it is SPEI-only); the
  old SPI-1 baseline (22 months) has no counterpart in this rerun.

## 2. (a) New-data counts at the OLD window (1980–2023) vs v2.10

Full 27-scenario table, CDPE months (new = nClimGrid gamma; old =
SPEIbase v2.10 run of record, `run_armA_2026-10-05/scenarios.csv`):

| Index | Thr | r=3.0 new / old | r=4.0 new / old | r=5.0 new / old |
|---|---|---|---|---|
| SPEI-1 | 1.0 | 41 / 189 | 16 / 140 | 11 / 99 |
| SPEI-1 | 1.5 | 4 / 84 | **3 / 46** | 1 / 20 |
| SPEI-1 | 2.0 | 0 / 4 | 0 / 0 | 0 / 0 |
| SPEI-3 | 1.0 | 72 / 184 | 43 / 135 | 20 / 97 |
| SPEI-3 | 1.5 | 29 / 89 | **8 / 48** | 3 / 23 |
| SPEI-3 | 2.0 | 2 / 4 | 0 / 4 | 0 / 1 |
| SPEI-6 | 1.0 | 85 / 187 | 52 / 138 | 23 / 99 |
| SPEI-6 | 1.5 | 29 / 81 | **8 / 51** | 5 / 23 |
| SPEI-6 | 2.0 | 2 / 8 | 1 / 5 | 0 / 3 |

New baseline month lists (thr 1.5, r 4.0):

- SPEI-1 (3): 1986-04, 2012-03, 2015-06
- SPEI-3 (8): 1983-09, 1993-08, 2003-07, 2007-05, 2013-04, 2015-06, 2019-09, 2019-10
- SPEI-6 (8): 1998-09, 2003-11, 2007-06, 2011-05, 2011-06, 2013-06, 2015-06, 2018-10

Jaccard overlap, new vs old baseline month sets: SPEI-1 **0.021**
(1 shared month), SPEI-3 **0.057** (3 shared), SPEI-6 **0.073**
(4 shared). 2015-06 is a CDPE month under both products at all three
timescales.

## 3. Gate arithmetic (frozen max-NaN gate, baseline configuration)

Per-month diagnostics from the frozen classifier
(`gate_diagnostics_summary.json` in both run directories; the same
diagnostic run reproduces the old run's 46/48/51 exactly on the old
grid, validating the pipeline end to end). Window 1980–2023, 528
months. The detector's coverage gate is buffer-local: a pole fails when
more than 10% of the cells in its 4.0° buffer are NaN.

| Grid / index | Domain finite share | Months failing the NaN gate (either pole) | Gate-passing months | Of gate-passers, failing majority | CDPE months |
|---|---|---|---|---|---|
| nClimGrid SPEI-1 | 0.606 | **460 (87.1%)** | 68 | 65 | 3 |
| nClimGrid SPEI-3 | 0.606 | 446 (84.5%) | 82 | 74 | 8 |
| nClimGrid SPEI-6 | 0.606 | 433 (82.0%) | 95 | 87 | 8 |
| SPEIbase SPEI-1 | 0.746 | 296 (56.1%) | 232 | 186 | 46 |
| SPEIbase SPEI-3 | 0.746 | 315 (59.7%) | 213 | 165 | 48 |
| SPEIbase SPEI-6 | 0.746 | 299 (56.6%) | 229 | 178 | 51 |

Mechanism: on the CONUS-masked grid, any month whose driest or wettest
cell lies within 4° of a coastline, the northern border, or the Great
Lakes has >10% masked cells in that pole's buffer and is rejected
before the majority test. Marginal tail mass also differs (share of
valid cell-months ≤ −1.5: SPEI-1 gamma 3.9% vs SPEIbase 5.7%; ≥ +1.5:
8.1% vs 7.9%), but the gate is the dominant term: it removes ~7 of
every 8 months at baseline. The gate was NOT adjusted, per the brief's
stop rule; the conditioning below is what the frozen pipeline produces
on the surviving month sets, and its limits are stated with it.

## 4. Hazards conditioning at the OLD window (1980–2023), old vs new

Frozen Step 06 (seed 20261026, B=2000 year bootstrap), identical hazard
series (the rerun reproduced the frozen storm and heat-wave series
exactly); only the CDPE month sets changed. Baseline n: old 46, new 3.

Headline rate ratios (RR, 95% CI):

| Outcome | v2.10 SPEIbase (n=46) | nClimGrid (n=3) |
|---|---|---|
| Tornadoes (all) | 1.13 (0.83–1.50) | 0.99 (0.45–2.16) |
| Hail ≥ 1 in | 1.10 (0.80–1.49) | 1.67 (0.52–4.81) |
| Heat-wave days per cell | 0.90 (0.54–1.39) | 4.26 (0.29–17.82) |
| Lightning (GLM flash box) | 0.98 (0.84–1.21), n=4 in GLM window | **not estimable — 0 baseline CDPE months fall in the GLM window (Mar 2018–Dec 2023)** |

Secondaries: tornado EF1+ 1.22 (0.81–1.73) → 1.03 (0.49–2.13);
EF2+ 1.21 (0.69–1.84) → 1.23 (0.49–3.28); hail (all) 1.10 (0.81–1.42)
→ 1.39 (0.52–3.76). Gate G2 (robustness): not passed under either
product. Split-era baseline tornado RR: old 1.02 (1980–1995, n=21) /
1.20 (1996–2023, n=25); new 0.74 (n=1) / 1.24 (n=2) — the new
split-era figures rest on one and two months and carry no information
beyond that.

Envelope (configs meeting the frozen ≥10-CDPE-month inclusion rule;
GLM ≥3 in-window): old 23 configs (main arms), 20 (GLM). New: **11
configs** — all nine threshold-1.0 configs plus SPEI-3 and SPEI-6 at
thr 1.5, r 3.0. **The new baseline itself (3 months) is envelope-
excluded by the frozen rule.** New envelope RR ranges: tornadoes
0.84–1.27, hail ≥1in 0.98–1.46, heat-wave 0.94–2.27 (vs old 0.99–1.50,
0.86–1.53, 0.56–2.62). GLM envelope: 8 configs meet the ≥3 rule
(by-config CSV; RR range 0.75–1.08); the summary JSON's GLM envelope
block is null because its statistics anchor to the undefined baseline
RR.

Interpretation, stated plainly: with three baseline months, the new
point estimates (notably heat-wave 4.26) are artefacts of which three
months survived — 1986-04, 2012-03, 2015-06 are all spring months —
and every interval spans the null by a wide margin. The like-for-like
conditioning cannot support or refute the v2.10 findings; it shows the
month set the new product yields is too small to condition on at the
baseline configuration.

## 5. (b) Extended window — endpoints and counts

Each source's endpoint, determined from the data itself:

| Source | Endpoint | Basis |
|---|---|---|
| nClimGrid SPEI (gamma, all timescales) | **2026-09** | last month with values in the domain (`prep_report.json`) |
| NCEI Storm Events | **2026-07** | 2026 details file (c20261026) contains BEGIN_YEARMONTH 202601–202607 only; 2025 file complete |
| gridMET (heat-wave source) | **2026-10-31** | tmmx_2026.nc holds 304 days, 2026-01-01–2026-10-31 |
| GOES GLM lightning | **2025-03** (last completable month) | bucket files sampled through 2025-04-07 (GOES-19 takeover); April 2025 cannot meet the frozen ≥90% month-validity rule |

**Binding endpoint: Storm Events, 2026-07 → headline window
Jan 1980–Jul 2026 (559 months).** Hazards inputs were extended with
their frozen processing: Storm Events through 2026-07 (series totals
over 559 months: 59,463 tornadoes; 250,404 hail ≥1in; 403,715 hail
all), heat-wave cell-days through 2026-07 (daily cube uses all days
the gridMET files contain, so boundary-crossing heat-wave runs credit
exactly as frozen), GLM through 2025-03.

Extended-window scenario counts differ from the old-window counts only
at threshold 1.0 (SPEI-1 r3: 44; SPEI-3 r3/r4: 74/44; SPEI-6 r3: 87).
At every threshold ≥ 1.5 configuration the counts — and therefore the
baseline month lists in §2 — are identical to the old window's. The
gate diagnostic for the added segment (SPEI-1, 2024-01–2026-07,
31 months): 26 fail the NaN gate, 5 pass it and fail the majority
test, 0 CDPE months.

## 6. (c) Hazards conditioning at the EXTENDED window (1980–2026-07)

Same frozen Step 06, extended hazard series, extended month sets
(baseline n still 3 — the same three months). The "old" column is the
v2.10 result at its own window (1980–2023): SPEIbase v2.10 ends in
Dec 2023, so no old-product run at the extended window exists; this
column is the comparison of record, not a like-for-like window match.

| Outcome | v2.10 SPEIbase, 1980–2023 (n=46) | nClimGrid, extended 1980–2026-07 (n=3) |
|---|---|---|
| Tornadoes (all) | 1.13 (0.83–1.50) | 0.95 (0.43–1.97) |
| Hail ≥ 1 in | 1.10 (0.80–1.49) | 1.61 (0.51–4.36) |
| Heat-wave days per cell | 0.90 (0.54–1.39) | 3.88 (0.31–13.98) |
| Lightning (GLM) | 0.98 (0.84–1.21), n=4 | not estimable — 0 baseline months in the GLM window |

Secondaries (extended): EF1+ 0.97 (0.46–1.98); EF2+ 1.21 (0.48–3.00);
hail (all) 1.39 (0.51–3.58). Split-era tornado RR (extended eras
1980–1995 / 1996–2026): 0.74 (n=1) / 1.18 (n=2). Gate G2: not passed.
The extended estimates move little from the old-window new-data
estimates (§4), as expected — the conditioning set is the same three
months; only the comparison pool grew. The same plain interpretation
applies: these numbers describe three spring months, not a
climatology, and no interval excludes the null.

**Lightning arm at the extended window:** gate G1 (completeness) now
**fails** under the frozen rule — 85 of 101 effective-window months
(2018-03 onward) are valid, because the GLM stream ends in Mar 2025
while the arm window runs to Jul 2026. Independent of G1, the arm has
no baseline CDPE months to condition on at either window.

## 7. (d) Envelope at the extended window

11 of 27 configs meet the frozen ≥10-month inclusion rule (the same
11 as at the old window). RR ranges across included configs:
tornadoes 0.84–1.23; hail ≥1in 0.94–1.41; heat-wave 0.99–2.09;
EF1+ 0.78–1.29; EF2+ 0.67–1.34; hail (all) 0.95–1.31 (old-product
envelope at 23 configs: 0.99–1.50, 0.86–1.53, 0.56–2.62, 0.91–1.86,
0.78–2.05, 0.94–1.45). GLM envelope: 9 configs meet the ≥3-in-window
rule, RR range 0.74–1.12 (by-config CSV; the summary block is null for
the reason given in §4). The baseline configuration remains
envelope-excluded (3 < 10 months) at both windows.

## 8. Figures (new data, extended window; run-stage deliverables)

In `cdpe_sensitivity/results/run_armA_nclimgrid_ext_2026-11-01/`
(PNG 300 dpi + vector PDF each), built with the NH package's map-figure
design (panel logic, captions, colourblind-safe palette, state
outlines):

1. **Report geography** — `fig_map_geography_extended.png/.pdf`.
   (a) Tornado + severe-hail (≥1.00 in) reports per 1° cell, Jan
   1980–Jul 2026 (916 cells). (b) Share of each cell's reports falling
   in the 3 extended-baseline CDPE months (cells with ≥25 reports;
   proportional expectation 0.54%; median observed share 0.7%).
   Counts recomputed from the extended Storm Events files under the
   Step-04 rules and asserted in code against the Step-04 series
   totals (59,463 tornadoes; 250,404 hail ≥1in; 403,715 hail all) —
   assertions passed.
2. **Pole geography** — `fig_map_poles_extended.png/.pdf`. Dry-pole
   and wet-pole locations for the 3 extended-baseline CDPE months
   (documented rendering: per-0.5°-cell counts of months with the pole
   in the cell, viridis, with the pole locations overlaid as points).
   Dry poles: 1986-04 → (36.25, −81.75); 2012-03 → (42.75, −104.25);
   2015-06 → (45.75, −119.75). Wet poles: 1986-04 → (45.25, −98.25);
   2012-03 → (48.25, −116.25); 2015-06 → (40.75, −84.75).
3. **Coverage map** — `coverage_map.png/.pdf` (§1).

Both maps were visually inspected after rendering. Formal manuscript
figure numbering is a rebuild-stage task and was not touched.

## 9. Flags, limits, and reproducibility

- **No SPI-1 arm** under the new product (§1). **Arm B was not
  rerun**, per the brief: Arm B's results of record derive from
  SPEIbase, so any manuscript text that treats Arms A and B as one
  single-product analysis is now internally inconsistent. Flagged
  here for the rebuild stage; not fixed, per instructions.
- **Headline caveat:** every baseline-configuration result in this
  report rests on 3 (SPEI-1) or 8 (SPEI-3/6) CDPE months, because the
  frozen coverage gate rejects 82–87% of months on the CONUS-masked
  grid (§3). Whether the hazards paper can proceed on this product —
  at the baseline configuration, it effectively cannot — is the
  author's decision; nothing in the pipeline was adjusted to soften
  that outcome.
- Companion published counts (SPEIbase v2.11, 1980–2024: 52/64/56)
  remain context only — different release and window.
- Environment note: this rerun used numpy 2.5.3 / pandas 3.0.6
  (original runs: numpy 1.26.4 / pandas 2.1.4). Where frozen outputs
  could be re-derived as checks, they reproduced exactly: the old
  grid's detector counts (46/48/51), the storm and heat-wave monthly
  series over 1980–2023 in both working projects, and land cells
  (3,608).
- Run outputs of record:
  - Detection: `cdpe_sensitivity/results/run_armA_nclimgrid_2026-11-01/`
    and `.../run_armA_nclimgrid_ext_2026-11-01/` (scenarios.csv,
    cdpe_monthly_series.csv, events.csv, baseline_poles.csv,
    monthly_grid_diagnostics.csv, gate_diagnostics_*, run_manifest.json).
  - Inputs: `cdpe_sensitivity/data_nclimgrid/` (DATA_MANIFEST.md,
    SHA256SUMS.txt, agg05/prep_report.json).
  - Conditioning: `cdpe-hazards-nclimgrid/win2023/results/` and
    `cdpe-hazards-nclimgrid/extended/results/`
    (rate_ratios_summary.json, rate_ratios_by_config.csv,
    monthly_series_all.csv, hazard_series_*.csv).
  - Scripts: `cdpe_sensitivity/scripts/` (prep_nclimgrid_spei.py,
    run_arm_a_nclimgrid.py, gate_diagnostics.py, build_coverage_map.py);
    `cdpe-hazards-nclimgrid/extended/code/` (frozen pipeline copies
    with window edits documented in-line, plus 08/09 map scripts).
    The one repair made during the run — a closing bracket displaced
    into a comment in the extended copy of Step 06's era list — is
    documented in that file's edit and changed no estimator logic.
