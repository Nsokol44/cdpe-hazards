# Code and CDPE month sets: "How much does the definition matter?"

Archive supporting the manuscript "How much does the definition matter?
Concurrent drought-pluvial regimes and the occurrence of tornadoes, hail,
heat waves, and lightning over the contiguous United States" by
Nicholas J. Sokol, submitted to Natural Hazards.

Deposited in this repository (github.com/Nsokol44/cdpe-hazards)
on 2026-11-01.

## Contents

- `nh_build/` - the Natural Hazards submission package build: the
  manuscript, cover letter and supplementary information sources
  (Markdown with pandoc-style citations), the bibliography
  (references_nh.bib), and `code/` steps 20 to 26 (the document builds,
  the verification suite, and the publication figure regenerations for
  Figures 1, 2 and 4).
- `hazards_analysis/` - the analysis pipeline of record for the
  hazard-conditioning arm and for the Storm Events, heat-wave and
  lightning series (steps 00 to 12), with its pinned requirements.txt
  and run_all.sh driver, plus its results tables.
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
   Figures 1, 2 and 4 from the archived result tables.
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
