# Rebuild report — CDPE hazards analysis on SPEIbase (masked control, pole locations, no-lightning conditioning, publication-grade maps)

Run date: 2026-11-02. Scope: the hazards paper only (AAS submission
AAS-2026-0874 and its Natural Hazards retarget — one analysis). The
author's 2026-11-02 decisions executed here: the papers stick with
SPEIbase (the nClimGrid substitution is closed; full record in
`NCLIMGRID_DELTA_REPORT.md`), the lightning arm is dropped from both
papers, and the map figures are rebuilt to publication standard. No
manuscript, package, or Drive file was edited. Detector, thresholds,
gates, seeds, and hazards-pipeline definitions are the frozen ones
throughout; every number below traces to a run output named in the
Reproducibility section.

Run directory: `cdpe_sensitivity/results/run_armA_speibase_rebuild_2026-11-02/`
(`A_speibase_masked/`, `B_speibase_full/`, `C_conditioning/`,
`verification.json`, figures).

## A. Masked control — the decisive decomposition

SPEIbase v2.10 SPEI-1/3/6 fields exactly as used by the run of record
(`run_armA_2026-10-05`), with the nClimGrid run's 0.5° valid-cell mask
applied on top: cells invalid in the aggregated nClimGrid product —
a static mask of 3,575 of 5,900 cells, verified identical across
timescales and across the window — were set to NaN; values elsewhere
unchanged. Frozen detector, Jan 1980–Dec 2023, 27 scenarios.

**Baseline counts (thr 1.5, r 4.0°) — three-way comparison:**

| Index | SPEIbase, full grid | SPEIbase values under the CONUS mask | nClimGrid values (delta report) |
|---|---|---|---|
| SPEI-1 | 46 | **10** | 3 |
| SPEI-3 | 48 | **15** | 8 |
| SPEI-6 | 51 | **14** | 8 |

**Gate table (baseline configuration, delta report §3 format;
window 1980–2023, 528 months):**

| Grid / index | Domain finite share | Months failing the NaN gate (either pole) | Gate-passing months | Of gate-passers, failing majority | CDPE months |
|---|---|---|---|---|---|
| SPEIbase full, SPEI-1 | 0.746 | 296 (56.1%) | 232 | 186 | 46 |
| SPEIbase full, SPEI-3 | 0.746 | 315 (59.7%) | 213 | 165 | 48 |
| SPEIbase full, SPEI-6 | 0.746 | 299 (56.6%) | 229 | 178 | 51 |
| SPEIbase masked, SPEI-1 | 0.602 | 436 (82.6%) | 92 | 82 | **10** |
| SPEIbase masked, SPEI-3 | 0.602 | 437 (82.8%) | 91 | 76 | **15** |
| SPEIbase masked, SPEI-6 | 0.602 | 432 (81.8%) | 96 | 82 | **14** |
| nClimGrid, SPEI-1 | 0.606 | 460 (87.1%) | 68 | 65 | 3 |
| nClimGrid, SPEI-3 | 0.606 | 446 (84.5%) | 82 | 74 | 8 |
| nClimGrid, SPEI-6 | 0.606 | 433 (82.0%) | 95 | 87 | 8 |

(The masked grid's finite share, 0.602, is the SPEIbase fields' own
finite share under the mask: SPEIbase itself is not complete in every
one of the 3,575 mask cells in every month. The nClimGrid rows are
the delta report's §3 values.)

**Reading.** The decomposition is decisive, and it is arithmetic, not
inference. Of the SPEI-1 baseline collapse 46 → 3, the mask alone
accounts for 46 → 10 and the product values for the remaining
10 → 3. The gate term is pure coverage geometry: laying the CONUS
mask over unchanged SPEIbase values raises gate failures from 296 to
436 months and cuts gate-passers from 232 to 92, because any pole
within 4° of a coast, the northern border, or the Great Lakes then
has >10% missing buffer cells. The value term is real but secondary:
among gate-passers the masked SPEIbase fields still convert at
10/92 (SPEI-1), 15/91, 14/96, against nClimGrid's 3/68, 8/82, 8/95 —
the thinner dry tail of the gamma product (delta report §3) at work
on the months the gate lets through. Same split at the other
timescales (48 → 15 → 8; 51 → 14 → 8). The author's question —
shouldn't two SPEI products show the same amount — is answered:
where both products have data they are recognisably the same
phenomenon, but the frozen coverage gate is silently a rule about
geographic coverage, and on a CONUS-only grid it disqualifies most
months before values are ever tested.

Full 27-scenario counts (CDPE months; full = run of record, masked =
this control, nClimGrid = delta report §2):

| Index | Thr | r=3.0 full / masked / nClim | r=4.0 full / masked / nClim | r=5.0 full / masked / nClim |
|---|---|---|---|---|
| SPEI-1 | 1.0 | 189 / 92 / 41 | 140 / 51 / 16 | 99 / 31 / 11 |
| SPEI-1 | 1.5 | 84 / 38 / 4 | **46 / 10 / 3** | 20 / 3 / 1 |
| SPEI-1 | 2.0 | 4 / 2 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| SPEI-3 | 1.0 | 184 / 86 / 72 | 135 / 50 / 43 | 97 / 29 / 20 |
| SPEI-3 | 1.5 | 89 / 29 / 29 | **48 / 15 / 8** | 23 / 5 / 3 |
| SPEI-3 | 2.0 | 4 / 0 / 2 | 4 / 0 / 0 | 1 / 0 / 0 |
| SPEI-6 | 1.0 | 187 / 86 / 85 | 138 / 45 / 52 | 99 / 33 / 23 |
| SPEI-6 | 1.5 | 81 / 33 / 29 | **51 / 14 / 8** | 23 / 3 / 5 |
| SPEI-6 | 2.0 | 8 / 1 / 2 | 5 / 0 / 1 | 3 / 0 / 0 |

## B. SPEIbase detection with pole locations — verification

The frozen detector was re-run on the unmasked SPEIbase v2.10 fields
(same window and configuration), saving per-month dry-pole and
wet-pole lat/lon for **every** scenario
(`B_speibase_full/poles_by_scenario.csv`; the three baselines also in
`B_speibase_full/baseline_poles.csv`).

**Verification statement: PASS.** All 27 SPEI scenario month sets
match `run_armA_2026-10-05` exactly (per-scenario equality in
`verification.json`). Baselines: SPEI-1 **46**, SPEI-3 **48**,
SPEI-6 **51** CDPE months, Jaccard **1.000** against the run of
record at each timescale, with identical month lists:

- SPEI-1 (46): 1980-05, 1981-04, 1981-11, 1982-02, 1982-05, 1984-01, 1985-01, 1985-04, 1985-07, 1986-02, 1986-12, 1987-12, 1988-11, 1990-06, 1990-11, 1992-05, 1993-02, 1993-07, 1994-03, 1995-03, 1995-07, 1998-01, 1998-04, 1999-09, 2001-04, 2004-04, 2004-05, 2005-02, 2005-04, 2006-01, 2006-06, 2007-11, 2008-04, 2008-08, 2011-03, 2011-04, 2011-05, 2011-12, 2012-11, 2015-06, 2016-03, 2017-02, 2020-05, 2021-07, 2022-04, 2023-07.
- SPEI-3 (48): 1980-03, 1981-04, 1984-11, 1986-01, 1987-01, 1987-05, 1987-06, 1990-12, 1991-08, 1993-03, 1993-09, 1998-05, 1998-07, 1999-06, 1999-08, 1999-09, 2001-01, 2001-02, 2001-10, 2003-08, 2003-09, 2004-05, 2005-02, 2005-03, 2005-12, 2006-06, 2006-08, 2007-05, 2007-07, 2008-04, 2009-03, 2011-01, 2011-03, 2011-04, 2011-05, 2011-06, 2011-07, 2011-12, 2013-04, 2015-06, 2015-08, 2017-04, 2018-09, 2021-07, 2022-05, 2022-06, 2023-08, 2023-09.
- SPEI-6 (51): 1980-09, 1980-11, 1980-12, 1981-04, 1986-04, 1987-03, 1987-05, 1987-06, 1987-07, 1988-12, 1991-01, 1991-03, 1992-03, 1993-09, 1993-12, 1995-06, 1996-04, 1998-06, 1998-07, 1999-08, 2001-10, 2002-06, 2003-10, 2003-11, 2003-12, 2006-02, 2007-06, 2008-06, 2011-04, 2011-05, 2011-06, 2011-07, 2011-09, 2011-10, 2014-07, 2017-06, 2018-03, 2018-04, 2018-05, 2018-09, 2019-07, 2020-07, 2020-08, 2021-12, 2022-04, 2022-05, 2022-06, 2022-07, 2022-08, 2023-11, 2023-12.

Workstream C and the pole-geography figure below were run on these
verified sets.

## C. Hazards conditioning without the lightning arm

Frozen Step 06 (seed 20261026, B = 2000 year bootstrap), hazard series
as of record (win2023 tree copies, re-verified value-equal against
`cdpe-hazards-aas/results/`), verified month sets above, window
Jan 1980–Dec 2023. The lightning (GLM) arm is removed from every
output: no GLM baseline block, no G1 completeness block, no GLM rows
in the by-configuration table, no GLM column in the monthly series
table, no GLM envelope. To keep every retained number bit-identical
to the with-lightning run of record, the GLM series was still
estimated internally in the frozen series order — the shared
bootstrap RNG stream is consumed exactly as frozen — and its
estimates discarded, never written. Envelope inclusion rule
unchanged (≥10 CDPE months, over the 36 Arm A configurations).

**Verification: nothing changed for the retained arms.** Against
`cdpe-hazards-aas/results/rate_ratios_summary.json` and
`rate_ratios_by_config.csv`: every retained summary block
(baseline, envelope, G2, window), the full split-era block, and all
216 retained by-configuration rows are **bit-identical** (maximum
absolute deviation 0.0; `C_conditioning/verification_conditioning.json`).

**Headline rate ratios (baseline configuration, n = 46 months):**

| Outcome | RR (95% CI) |
|---|---|
| Tornadoes (all) | 1.13 (0.83–1.50) |
| Hail ≥ 1 in | 1.10 (0.80–1.49) |
| Heat-wave days per cell | 0.90 (0.54–1.39) |

**Secondaries:** EF1+ 1.22 (0.81–1.73); EF2+ 1.21 (0.69–1.84);
hail (all) 1.10 (0.81–1.42).

**Split-era (baseline configuration):**

| Outcome | 1980–1995 (n = 21) | 1996–2023 (n = 25) |
|---|---|---|
| Tornadoes (all) | 1.02 (0.75–1.38) | 1.20 (0.78–1.64) |
| EF1+ | 1.02 (0.69–1.47) | 1.34 (0.75–2.08) |
| EF2+ | 1.07 (0.62–1.80) | 1.31 (0.50–2.31) |
| Hail (all) | 0.91 (0.64–1.38) | 1.20 (0.97–1.45) |
| Hail ≥ 1 in | 0.91 (0.68–1.23) | 1.19 (0.94–1.53) |

**Envelope (23 of 36 configurations meet the ≥10-month rule):**

| Outcome | RR range | Share same side as baseline | Share of CIs excluding 1 | G2 robust |
|---|---|---|---|---|
| Tornadoes (all) | 0.99–1.50 | 0.96 | 0.00 | No |
| Hail ≥ 1 in | 0.86–1.53 | 0.96 | 0.30 | No |
| Heat-wave days per cell | 0.56–2.62 | 0.30 | 0.13 | No |
| EF1+ | 0.91–1.86 | 0.87 | 0.04 | No |
| EF2+ | 0.78–2.06 | 0.65 | 0.04 | No |
| Hail (all) | 0.94–1.45 | 0.96 | 0.26 | No |

Gate G2 is not passed for any outcome, as before. Outputs:
`C_conditioning/rate_ratios_summary.json`,
`C_conditioning/rate_ratios_by_config.csv`,
`C_conditioning/monthly_series_all.csv`.

## D. Publication-grade map figures

Built to the standing figure standard (exactly 6.0 in wide — 1800 px
at 300 dpi — plus vector PDF; state outlines and coastline from the
hazards project's `us_states_simplified.geojson`; colourblind-safe
palettes; panel labels; self-contained titles; no raw variable
names), and visually inspected after rendering:

1. **Report geography** —
   `results/run_armA_speibase_rebuild_2026-11-02/fig_map_geography_speibase.png` / `.pdf`.
   Rebuild of the NH Figure 1 design on the as-of-record series:
   (a) tornado + severe-hail reports per 1° cell (915 cells, viridis,
   log scale); (b) share of each cell's reports in the 46 baseline
   CDPE months (672 cells with ≥25 reports; BrBG centred on the
   proportional expectation 46/528 = 8.7%; median observed share
   10.8%). Counts recomputed from the win2023 Storm Events files
   under the frozen Step-04 rules and asserted in code against the
   Step-04 totals (54,607 tornadoes; 229,650 hail ≥1 in; 379,430 hail
   overall) — assertions passed; the cell counts and median share
   reproduce the NH package's Figure 1 exactly. (First render had a
   clipped one-line title; fixed with a two-line title and
   re-inspected.)
2. **Pole geography (new)** —
   `results/run_armA_speibase_rebuild_2026-11-02/fig_map_poles_speibase.png` / `.pdf`.
   Dry-pole (a) and wet-pole (b) geography of the 46 baseline months
   from Workstream B: counts of CDPE months whose pole fell in each
   1° cell (dry poles occupy 43 cells, wet poles 42, maximum 3 months
   per cell), cividis, **one shared legend** for both panels, the 46
   pole locations overlaid as points in each panel. Pole-to-cell
   alignment verified numerically (all 46 points of each pole inside
   a counted cell) as well as by eye. Poles falling in Canada, Mexico,
   or the domain's ocean margins are plotted where they are — the
   analysis domain is the full 25–50°N, 125–66°W box, as in the
   papers.

## Reproducibility

- Detection (A + B): `cdpe_sensitivity/scripts/run_arm_a_speibase_rebuild.py`
  → `results/run_armA_speibase_rebuild_2026-11-02/{A_speibase_masked,B_speibase_full}/`
  (scenarios.csv, events.csv, cdpe_monthly_series.csv,
  poles_by_scenario.csv, baseline_poles.csv,
  gate_diagnostics_per_month.csv, gate_diagnostics_summary.json,
  run_manifest.json) and `verification.json`.
- Conditioning (C): `cdpe_sensitivity/scripts/run_conditioning_no_lightning.py`
  (frozen Step 06 with the three documented changes in its docstring;
  `--verify-only` re-runs the verification alone) →
  `C_conditioning/` outputs above.
- Figures (D): `cdpe_sensitivity/scripts/build_rebuild_maps.py`.
- Environment: numpy 2.5.3 / pandas 3.0.6 (original runs: numpy
  1.26.4 / pandas 2.1.4 — the same note as the delta report's §9).
  Every reproduction check available was exact under this
  environment: detector month sets (27/27 scenarios), hazard series,
  and all retained conditioning numbers.
- Not done, by design: no manuscript or package edits (figure
  numbering, text updates for the dropped lightning arm, and the §3.1
  / supplement rewrite belong to the rebuild stage); Arm B unchanged.
