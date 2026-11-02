# Code and CDPE month sets: "How much does the definition matter?"

Archive supporting the manuscript "How much does the definition matter?
Concurrent drought-pluvial regimes and the occurrence of tornadoes, hail,
and heat waves over the contiguous United States" by
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
  (references_nh.bib), and `code/` steps 20 to 28 (the document builds,
  the verification suite, the publication figure regenerations, and
  the rebuild map builder).
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
