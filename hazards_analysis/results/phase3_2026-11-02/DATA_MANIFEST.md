# Phase 3 ONI data manifest

- Covariate file: `oni_monthly.csv` (528 rows, 1980-01 to 2023-12).
- Source: NOAA Physical Sciences Laboratory `oni.data` — the CPC Oceanic
  Nino Index (ONI). Official URL: https://psl.noaa.gov/data/correlation/oni.data
  (the file's own footer cites the CPC source
  https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt).
- Retrieved: 2026-11-02 (page crawl timestamp 2026-11-02 13:02 UTC).
- Convention: the ONI is the 3-month running mean of ERSST SST anomalies
  in the Nino 3.4 region (5N-5S, 120-170W); each overlapping season value
  is assigned to its centre month, so the value stored for month t is the
  season centred on t. The PSL file already stores values in this monthly
  centred layout (one row per year, Jan..Dec); no re-centring was applied.
- Vintage: the retrieved file states "As of 09/7/2026, uses NOAA ERSST
  V6". Values for 1980-2023 were transcribed verbatim from the retrieval
  into code/32_prepare_inputs.py (ONI_ROWS) and are written out unchanged.
- SHA-256 of oni_monthly.csv as written: computed at runtime and recorded
  in validation.json (this manifest is written by the same run).
- Cross-check against the fallback file
  ~/workspace/seg-revision/seg_rerun/data/NewONI.csv (ERSST v5 vintage;
  provenance: ~/workspace/seg-revision/seg_rerun/ONI_PROVENANCE.md):
  Pearson r = 0.9965, max |difference| = 0.29 over 1980-2023.
  Differences are the expected v5-to-v6 revision; the PSL/CPC file of
  record above is the covariate used in all Phase 3 models.
