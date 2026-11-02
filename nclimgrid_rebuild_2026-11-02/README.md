# nClimGrid substitution episode and SPEIbase rebuild — archive, 2026-11-02

This folder archives a closed episode in the history of the manuscript
"How much does the definition matter?" (see the repository root). The
papers were **not** rebuilt on the substitute product; this archive is
the record of the test the author directed, its result, and the
SPEIbase rebuild that followed from it.

## What happened

On 2026-11-01 the author directed a test: replace SPEIbase with NOAA's
gridded SPEI from the nClimGrid family for the hazards paper (AAS +
Natural Hazards versions only), after the SPEIbase v2.11 spei03/spei06
files proved unobtainable (the author's own uploaded copies turned out
to be legacy files — v2.9 and a record ending 2018 — and were rejected
at the metadata gate and quarantined). The frozen CDPE detector,
parameters unchanged, was run on the substitute product over
1980–2023 and over an extended window to July 2026 (Storm Events was
the binding endpoint).

**Result:** the baseline catalog collapsed — SPEI-1 46 → 3 CDPE
months, SPEI-3 48 → 8, SPEI-6 51 → 8 — and the extension added zero
baseline months. The cause, decomposed in the reports below, is the
frozen buffer-local coverage gate meeting a CONUS-only grid: the gate
rejects 82–87% of months on the masked grid (vs 56–60% on the SPEIbase
grid) because pole buffers reaching past the coasts and borders find
no data. A masked control (SPEIbase values under the nClimGrid CONUS
mask) gives 10/15/14, so of the SPEI-1 collapse, roughly 36 months are
coverage geometry and roughly 7 are genuine product-value differences
(the substitute's dry tail is thinner at the detector threshold:
3.9% vs 5.7% of cell-months at or below −1.5). The pipeline itself was
validated: the same code on the old grid reproduces 46/48/51 exactly.

On 2026-11-02 the author decided the papers remain on SPEIbase. The
detection was re-run on SPEIbase with pole locations saved (it
reproduces the archived month sets exactly, all 27 scenarios), the
hazards conditioning was rerun without the lightning arm (the author
directed its removal; every retained estimate is bit-identical to the
previous run of record), and the rebuilt manuscripts report three
hazards. That rebuild is Push 1's companion commit on this repository
("Rebuild 2026-11-02").

## Provenance of the substitute product

`data_nclimgrid/DATA_MANIFEST.md` records it in full. In brief: the
drought.gov "SPEI from nClimGrid-Daily" product has no downloadable
monthly archive (Climate Engine snapshots only); the files used are
NOAA NCEI's official downloadable gridded monthly SPEI of the same
family, derived from nClimGrid-**Monthly** (gamma variant; calibration
1895–2014), from
https://www.ncei.noaa.gov/pub/data/nidis/indices/nclimgrid-monthly/.
`data_nclimgrid/SHA256SUMS.txt` lists the raw files' hashes.

## Contents

- `NCLIMGRID_DELTA_REPORT.md` — the substitution run: counts, gate
  decomposition, conditioning on the collapsed month sets, endpoints.
- `SPEIBASE_REBUILD_REPORT.md` — the masked control, the verified
  SPEIbase re-detection with pole locations, and the no-lightning
  conditioning.
- `data_nclimgrid/` — the product manifest, raw-file hashes, and the
  0.5° aggregation prep report and month lists (`agg05/`).
- `runs/run_armA_nclimgrid_ext_2026-11-01/` — month sets, pole table,
  gate diagnostics, run manifest for the substitute-product detection.
- `runs/run_armA_speibase_rebuild_2026-11-02/` — the masked control
  (A), the full SPEIbase re-detection (B), and the no-lightning
  conditioning (C), with verification files.
- `scripts/` — the fetch, prep, detection, conditioning and map
  scripts, including the extended-window and 1980–2023 pipeline copies
  from the working tree (`nclimgrid_pipeline_extended/`,
  `nclimgrid_pipeline_win2023/`).

## Not in this archive

- **Raw product files** (~8.8 GB of netCDF) and the **0.5° analysis
  grids** (3 × 37 MB netCDF): too large and binary for this
  repository's snapshot pushes. They are re-derivable from the
  manifest URLs plus `scripts/prep_nclimgrid_spei.py`; the month lists
  and prep report in `data_nclimgrid/agg05/` document them.
- **Map figures** (PNG/PDF): binary, so the snapshot push cannot carry
  them. The SPEIbase report-geography and pole-geography maps are
  filed with the submission packages in the author's Drive (NH folder:
  `fig_map_geography.*`, `fig_map_poles.*`) and remain in the local
  run directories; the substitute product's coverage and extended
  maps remain local only.
