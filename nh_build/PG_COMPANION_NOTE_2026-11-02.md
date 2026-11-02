# Evidence Note for the Physical Geography Companion — Prepared 2026-11-02

**Purpose.** A short evidence note the author can use with the Physical
Geography editor if the companion study's catalog is ever queried. It
records what an independent re-derivation (2026-11-02, for the catalog
alignment of the Natural Hazards hazards paper) established about the
companion's published counts. **Not sent anywhere; prepared only.**

## What was checked

The companion's frozen identification code
(`Sokol_Study1_CDPE_Identification.py`, imported unmodified) and the
independently audited NumPy port of the same algorithm (validated
month-for-month against the original, Jaccard 1.000, in the 2026-10-05
audit) were run on the SPEIbase v2.11 spei01 file (MD5
3eba69cbbbf95c671cabbd71e01b6f4c; CRU TS 4.09) over the companion's
window, 1980–2024.

## Findings

1. **SPEI-1 reproduces exactly.** Both implementations return **52
   qualifying months** at the baseline settings (threshold 1.5, radius
   4.0°), the companion's printed count. None of the 52 falls in 2024;
   the catalog is unchanged if the window is trimmed to Dec 2023.
2. **The grid maximum reproduces exactly.** At threshold 1.0, radius
   3.0°, the v2.11 run returns **214 months**, the companion's printed
   grid maximum.
3. **No correction to the companion is needed for SPEI-1.** The
   discrepancy that prompted the check (a hazards-paper replication on
   the staged SPEIbase v2.10 files returning 46 months) is fully
   explained by the input release: v2.10 (CRU TS 4.08) versus v2.11
   (CRU TS 4.09). The two releases' catalogs share 32 months (Jaccard
   0.485; chance expectation 4.5). The hazards paper has adopted the
   companion's 52-month catalog as its headline set, so the three
   papers now share one catalog.
4. **SPEI-3 and SPEI-6 could not be re-derived**, because the SPEIbase
   v2.11 spei03 and spei06 files are not in hand (the publisher's
   download route was unavailable; two author-supplied candidate files
   failed version verification and were quarantined). The published
   counts (64 and 56) are therefore unverified rather than contradicted.
   For scale: the v2.10 replication returns 48 and 51, and a one-year
   window difference could account for at most 12 months of the
   16-month SPEI-3 gap, so a release contribution is likely there too.
   If the editor asks, the honest statement is that SPEI-3/6
   verification waits on the v2.11 files.
5. **SPI-1 remains the one open item.** The companion reports 66 SPI-1
   months computed from CRU TS precipitation (gamma fit, 1981–2010
   calibration, climate_indices package). A faithful implementation of
   that documented specification (CRU TS 4.09 precipitation,
   climate-indices 2.4.0) returns 22 months over 1980–2023; calibration
   variants return 27; a Pearson III variant returns 3. No tested
   construction approaches 66, and the original spi01.nc and its
   generating script were not available to close the comparison. The
   qualitative claim (the SPI and SPEI catalogs are near-disjoint,
   Jaccard about 0.05–0.06) holds in every variant. If the editor or a
   reviewer presses on any number in the companion, it will be this
   one, and the author's original SPI file or script is the only thing
   that settles it.

## Bottom line for the editor, if needed

The companion's SPEI-1 catalog and grid maximum are exactly
reproducible from SPEIbase v2.11 with the study's own code. The
hazards-paper replication shortfall was an input-release difference on
the replication side, not an error in the companion. SPEI-3/6 await
their v2.11 files for the same check; the SPI-1 count is the single
figure the author may wish to revisit with his original files in hand.
