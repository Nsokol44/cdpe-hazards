# DATA MANIFEST — nClimGrid SPEI (replacement for SPEIbase, hazards paper only)

Retrieved: 2026-11-01 (America/New_York). All metadata below was read from
the downloaded files themselves (netCDF global/variable attributes) or
from the archive's own readme; nothing is taken from secondary sources.

## Source

NOAA NCEI NIDIS gridded climate indices archive (the directory that
drought.gov's data-download page links as "SPI and SPEI – File
Directory"):

- Archive root: https://www.ncei.noaa.gov/pub/data/nidis/indices/nclimgrid-monthly/
- Readme: https://www.ncei.noaa.gov/pub/data/nidis/indices/nclimgrid-monthly/readme.txt
- Files used (subdirectory `spei-gamma/`):
  - https://www.ncei.noaa.gov/pub/data/nidis/indices/nclimgrid-monthly/spei-gamma/nclimgrid-spei-gamma-01.nc
  - https://www.ncei.noaa.gov/pub/data/nidis/indices/nclimgrid-monthly/spei-gamma/nclimgrid-spei-gamma-03.nc
  - https://www.ncei.noaa.gov/pub/data/nidis/indices/nclimgrid-monthly/spei-gamma/nclimgrid-spei-gamma-06.nc
- Also archived for reference (not used in the analysis):
  `spei-pearson/nclimgrid-spei-pearson-01.nc`.

## Provenance note (read carefully)

The brief named the drought.gov product "U.S. Gridded SPEI from
nClimGrid-Daily". The drought.gov product pages describe Climate Engine
current-condition, trailing-window GeoTIFF snapshots; no downloadable
monthly archive of that exact product exists. The archive above is the
official downloadable gridded monthly SPEI from the same nClimGrid
family: per the archive readme (J. Durre, NCEI), the indices are
"derived from the nClimGrid **monthly** dataset of maximum and minimum
temperature and total precipitation" — i.e. nClimGrid-Monthly, not
nClimGrid-Daily. This is the closest official product to the brief's
intent (gridded monthly CONUS SPEI, 1/3/6-month timescales, full period
of record) and the substitution is recorded here rather than made
silently.

## Variant decision: GAMMA

The archive carries two SPEI variants, `spei-gamma` and `spei-pearson`
(gamma vs Pearson III fitting of the water-balance distribution). The
drought.gov product-family description for these standardized indices
names the gamma distribution, and the archive lists gamma first; the
GAMMA variant is therefore the analysis input. The choice is
transparent and reversible: the Pearson III files live in the same
archive (the 1-month Pearson file was downloaded and archived here as
evidence). The old SPEIbase product also fits a log-logistic
distribution, so neither variant is a like-for-like distributional
match; this is a documented property of the substitution, not a hidden
one.

## Files (sizes verified byte-exact against server Content-Length)

| File | Bytes | SHA-256 |
|---|---|---|
| nclimgrid-spei-gamma-01.nc | 2,300,698,427 | 9d3583ae77485a64a1644f6ce068740597e5395a0ab148b82ee1b22b018091a5 |
| nclimgrid-spei-gamma-03.nc | 2,310,127,139 | 66b36a5ab1ea5d5207b4c9a688925157195449934469888054230a78a8ee32c3 |
| nclimgrid-spei-gamma-06.nc | 2,307,806,793 | 12aca0ba0788edf26811dcd05bc3e33b7d03caa9f804b4a5b57ecac3592ce4a2 |
| nclimgrid-spei-pearson-01.nc (reference only) | 2,319,662,079 | eead5a47da3e3f7984f30dbc562aeab138bc3f10ce46496b9e56f15ac7afd142 |

SHA-256 values are also in `SHA256SUMS.txt` in this directory.

## Product metadata (from the gamma files' own attributes)

- Title (gamma-01): "SPEI/Gamma 1-month values computed by NIDIS/NCEI/NOAA, for internal use only" (03/06 analogous).
- Variables: `spei_01`, `spei_03`, `spei_06`.
- Grid: lat 596 × lon 1385 at 1/24° (≈4.6 km); lat centres 24.5625 → 49.3542 N, lon centres −124.6875 → −67.0208.
- Time: 1,581 monthly steps, 1895-01 → 2026-09, stamps on the 1st of the month.
- **Calibration (reference) period: 1895–2014** (variable attributes `calibration_start_year`/`calibration_end_year`). This differs from the Climate Engine pages' 1991–2020 trailing-window description; the files' own metadata governs.
- Fill/missing: −999.9. Valid data range ≈ ±3.09.
- Coverage: CONUS land only — ocean, Canada and Mexico cells are masked in the product itself.
- Last month with values: **2026-09** for all three timescales (confirmed in `agg05/prep_report.json`).

## Aggregation to the Arm A grid

`../scripts/prep_nclimgrid_spei.py` aggregates each timescale to the
detector's 0.5° grid (lat centres 25.25..49.75, lon centres
−125.25..−66.75) by exact spherical-overlap area weighting over the
product cells (weight = Δλ·(sin φ_top − sin φ_bot) of the overlap),
NaN where no valid fine cell contributes. Outputs in `agg05/`:
`spei{01,03,06}_nclimgrid_gamma_05deg.nc`, `prep_report.json`,
per-index valid-count files.

- Valid (covered) 0.5° cells on the aggregated grid: **3,575** of 5,900
  domain cells (static across the record), vs **4,399** valid cells on
  the SPEIbase grid over the same box (2020-01) — the difference is the
  product's CONUS land mask vs SPEIbase's global land coverage (border,
  coastal and Great Lakes cells).
- Verification: a hand-checked cell (35.25, −95.25), 2020-01 aggregated
  value 1.8501 equals the direct fine-cell mean 1.8501.
