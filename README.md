# Code and CDPE month sets: CDPE hazards frequency analysis

Archive supporting the manuscript "Do tornadoes, hail, and heat waves
occur differently during concurrent drought-pluvial months? A
count-model analysis over the contiguous United States" by
Nicholas J. Sokol, submitted to Natural Hazards.

Deposited in this repository (github.com/Nsokol44/cdpe-hazards)
on 2026-11-01.

## Rebuild — 2026-11-02

On the author's direction, the lightning (GLM) arm was removed from the
manuscript, and the pole-geography map of the 46 baseline CDPE months
was added as Figure 2. The conditioning was rerun without lightning
(`hazards_analysis/code/06b_conditioning_no_lightning.py`, the frozen
step 06 with the GLM estimates discarded; every retained estimate is
bit-identical to the previous run of record), and
`hazards_analysis/results/` now holds those no-lightning outputs. The
SPEIbase detection rerun with pole locations saved is
`sensitivity_analysis/scripts/run_arm_a_speibase_rebuild.py`; its
baseline pole table is
`monthsets/run_armA_speibase_rebuild_2026-11-02/baseline_poles.csv`,
and `nh_build/code/28_build_rebuild_maps.py` draws the two map figures
from it and from the archived report series. The GLM fetch and series
steps (03, and the lightning parts of the original step 06 run) remain
in the archive as the record of the analysis as first run.

## Contents

- `nh_build/` - the Natural Hazards submission package build: the
  manuscript, cover letter and supplementary information sources
  (Markdown with pandoc-style citations), the bibliography
  (references_nh.bib), and `code/` steps 20 to 43 (the document builds,
  the verification suite, the publication figure regenerations, the
  rebuild map builder, and the fix-round steps 39 to 43).
- `hazards_analysis/` - the analysis pipeline of record for the
  hazard-conditioning arm and for the Storm Events and heat-wave
  series (steps 00 to 12, plus step 06b, the no-lightning conditioning
  rerun whose outputs the current manuscript reports), with its
  pinned requirements.txt and run_all.sh driver, plus its results
  tables.
- `sensitivity_analysis/` - the CDPE sensitivity pipeline (the
  cdpe_sens package and its run scripts) that produced the
  756-configuration ensemble in two arms.
- `monthsets/` - the CDPE month sets: the Arm A monthly CDPE indicator
  series as consumed by the hazards pipeline, and the per-run result
  tables for Arm A, land-masked Arm B and unmasked Arm B, including the
  Arm B per-configuration month-series chunks.

## Versions

Python 3.12.3. Pinned packages for the hazards pipeline are listed in
hazards_analysis/code/requirements.txt (numpy 2.5.3, pandas 3.0.6,
scipy 1.18.1, matplotlib 3.11.2, netCDF4 1.7.4, requests 2.34.2,
python-docx 1.2.0).

## How to run

1. Sensitivity ensemble: `python sensitivity_analysis/scripts/run_two_arms.py`
   (Arm A and unmasked Arm B) and
   `python sensitivity_analysis/scripts/run_arm_b_masked.py`
   (land-masked Arm B), with the data staging described in those
   scripts. Outputs land in results folders like the ones mirrored
   under `monthsets/`.
2. Hazards arm: `bash hazards_analysis/code/run_all.sh` runs steps 00
   to 12 in order (data fetch, series construction, rate ratios with a
   whole-year bootstrap, B = 2000, seed 20261026, figures, citation
   closure, fact sheet and number verification).
3. Submission documents: `python nh_build/code/20_build_nh_docx.py`,
   `21_build_nh_cover_letter.py` and `23_build_nh_supplement.py` build
   the DOCX files from the Markdown sources. Steps 24 to 26 regenerate
   the sensitivity and envelope figures from the archived result
   tables, and step 28 draws the two map figures (Figures 1 and 2).
   `python nh_build/code/22_verify_nh.py` runs the verification suite
   (citation closure, number trace against the results corpus, and
   document hygiene checks).

## Data

Source data are public and are not redistributed in this archive:
SPEIbase (CSIC), CRU TS (Climatic Research Unit), NARR (NOAA Physical
Sciences Laboratory), ERA5 (Copernicus Climate Data Store and the
ARCO-ERA5 mirror), gridMET (University of Idaho), Storm Events (NOAA
NCEI) and GOES-16 GLM (NOAA Open Data on AWS). The derived CDPE month
sets under `monthsets/` are the author's own outputs and are included
in full.

## License

Code in this archive is released under the MIT License. Data products
remain under the terms of their respective providers.

## Rebuild of 2026-11-02 (two-paper split)

Following external review, the hazards work was split into a frequency
paper (Natural Hazards, this repository's `nh_build/`) and a physical
dynamics paper (Advances in Atmospheric Sciences special issue; design
memo only, `paper2_design/DESIGN_MEMO.md`). The Natural Hazards paper
now uses the companion Study-1 catalog on SPEIbase v2.11 (52 baseline
months) as its headline catalog, with a US-anchored subset (both poles
inside the CONUS, 15 months), a negative-binomial count model as the
primary estimand, and a lagged (antecedent-month) arm addressing
reverse causation. Alignment evidence: `nh_build/CATALOG_ALIGNMENT_2026-11-02.md`;
statistics: `hazards_analysis/results/phase3_2026-11-02/` (one-command
rerun `nh_build/code/run_phase3.sh`); the Arm B tie-break correction
and redone variance decomposition are under `sensitivity_analysis/`
and `monthsets/run_armB_tiefix_2026-11-02/`.

## Fix round 2 — 2026-11-02

After the author's verification read of the rebuilt package, the
manuscript was retitled (title above) and four checks were added,
under `nh_build/code/` steps 39 to 42 with outputs in
`nh_build/results_fixround2_2026-11-02/`:

- Step 39 verifies the heat-wave series against the raw gridMET daily
  Tmax files for late 2010 to mid 2012: the early-2011 plateau in the
  series of record reproduces (plateau months within about 3 percent),
  so the frozen series stands.
- Step 40 reruns the frozen detector with the domain box expanded
  north by 3 and 5 degrees: the northern dry-pole pile-up is
  substantially an edge artifact in pole location (retained poles move
  north, never south), while month qualification is more robust. The
  headline catalog is unchanged; see `EDGE_TEST_NOTE.md` in the
  results folder.
- Step 41 adds the lagged pole-relative strata (following-month
  reports by regime-month poles). Every lagged interval includes 1
  and the same-month near-dry tornado deficit inverts, so the
  same-month pattern is reported in the paper as exploratory. The
  pole-relative family is 12 stratum-hazard estimates across both
  timings.
- Step 42 computes the month-paired bootstrap difference between the
  same-month and lagged count-model arms: all three differences
  include zero, and the paper reports the two arms without a causal
  reading of their difference.

The full record is the Fix Round 2 addendum in
`nh_build/IMPLEMENTATION_CHECKLIST_2026-11-02.md`.
