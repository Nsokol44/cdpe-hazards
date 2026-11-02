# Catalog Alignment — Hazards Papers Matched to the SEG / Companion Catalog

**Date:** 2026-11-02 · **Status:** Phase 1 of the implementation of the two
adopted external reviews · **Author directive:** "We need these studies to
match the SEG paper catalog."

All numbers below come from `code/28_subset_test_companion.py` and
`code/31_catalog_alignment.py`; outputs in
`results/alignment_2026-11-02/` (`aligned_month_sets.csv`,
`pole_classification.csv`, `alignment_summary.json`). Deterministic; no
randomness anywhere in this phase.

## 1. The question

The hazards papers' Arm A (the port of the author's detector run on the
staged SPEIbase v2.10 files, 1980–2023) returns 46 SPEI-1 CDPE months at
the baseline settings (threshold 1.5, radius 4.0°). The companion study
(Physical Geography, in review) publishes 52 qualifying months over
1980–2024, and the Southeastern Geographer (SEG) paper's national
comparison uses that same companion catalog (52 national events, 13
touching the Southeast, 3 shared at radius 4.0°; 162 / 54 / 8 at radius
2.0°; verified in `seg_revision_outputs_v211/04_national_vs_regional.csv`,
computed on SPEIbase v2.11). The external review hypothesised that the
46-vs-52 gap is a window artifact (the companion's extra year, 2024) and
demanded a month-list subset test before any non-reproduction claim is
printed.

## 2. The subset test (run, not argued)

The companion's published month list does not survive on disk as a file,
so the catalog was regenerated with the companion's own frozen detector
(`Sokol_Study1_CDPE_Identification.py`, imported unmodified) on the
MD5-verified SPEIbase v2.11 spei01 file (MD5
3eba69cbbbf95c671cabbd71e01b6f4c). The regeneration returns **exactly 52
months** over 1980–2024, the companion's printed count, which validates
the regeneration as the published catalog. Independently, the frozen
port detector (`cdpe_sens.author_detector`, audited in 2026-10 to agree
with the original script month-for-month, Jaccard 1.000) run on the same
v2.11 file returns the identical 52 months and their pole locations, and
at the published grid-maximum configuration (threshold 1.0, radius 3.0°)
returns **214 months**, the companion's printed grid maximum (Arm A on
v2.10: 189; the v2.11 count trimmed to 2023 is 209).

Findings (SPEI-1, baseline settings):

| Quantity | Value |
|---|---|
| Companion catalog (v2.11), 1980–2024 | 52 months |
| Companion months falling in 2024 | **0** |
| Companion months trimmed to Dec 2023 | 52 |
| Arm A (v2.10), 1980–2023 | 46 months |
| Intersection | 32 months |
| Only in Arm A | 14 months |
| Only in companion | 20 months |
| Arm A a subset of companion? | **No** |
| Jaccard | 0.485 |
| Chance-expected overlap (46 × 52 / 528) | 4.5 months |

**The window hypothesis is refuted.** The companion catalog contains no
2024 months at all, so the extra year explains none of the gap. The gap
is a release difference: SPEIbase v2.10 (CRU TS 4.08) and v2.11 (CRU TS
4.09) fields put the detector's two pole buffers on opposite sides of
the qualification line in 34 of the 66 distinct months involved. The
earlier Arm A attribution of the gap to the release was stated before
this test as "leading but unproven"; it is now proven for SPEI-1 in the
only way available (identical frozen code, both releases, month lists
compared directly), with the arithmetic caveat for the other timescales
in §4.

## 3. The decision

**The catalog of record for both hazards papers is the companion
(Study-1) catalog: SPEIbase v2.11, frozen author detector, baseline
settings, 52 months.** Because none of the 52 falls in 2024, the aligned
catalog sits entirely inside the hazards window Jan 1980–Dec 2023 with
no trimming and no window change. Concretely:

- The headline conditioning (Phase 3) is estimated on the 52 aligned
  months; the Arm A 46-month estimates are retained as a continuity
  comparison showing what the staged-release port gives.
- The definition envelope (36 Arm A scenarios) and the timescale and
  index contrasts remain computed on the staged v2.10 fields, and the
  manuscript must say so: the envelope is a sensitivity ensemble over
  definitions on a stated input release, while the headline catalog is
  the catalog of record. The envelope's baseline cell (46 months)
  overlaps the catalog of record in 32 months (Jaccard 0.485, against a
  chance expectation of 4.5 shared months).
- SEG needs no change: its national numbers already derive from this
  catalog. (Its only edit in this implementation is the McKee et al.
  page range, 179–183 corrected to 179–184, verified against three
  independent bibliographies; done 2026-11-02, Drive copy updated in
  place.)

## 4. What cannot be aligned (recorded, not worked around)

- **SPEI-3 / SPEI-6:** SPEIbase v2.11 spei03/spei06 files are not in
  hand. The only candidate uploads (author-supplied, 2026-11-01) failed
  verification (one is v2.9 on CRU TS 4.07 ending Dec 2022; the other is
  unversioned, ending Dec 2018) and are quarantined under REJECTED
  names. Count-level accounting only: the published-vs-Arm A gaps are
  16 months (SPEI-3: 64 vs 48) and 5 months (SPEI-6: 56 vs 51). A window
  can contribute at most 12 months, so the SPEI-3 gap cannot be a window
  artifact; the SPEI-6 gap is small enough that either cause could
  dominate, and it stays unattributed. No aligned SPEI-3/6 month sets
  exist, so no lagged SPEI-3/6 regime variant can be built for Paper 1.
- **SPI-1:** the companion's original spi01.nc and its generating script
  were never supplied; the 66-vs-22 gap is unresolved at month level
  (2026-10-05 audit, item 1b: calibration and distribution variants give
  27 / 27 / 3 months, never near 66). SPI-1 stays in the envelope only,
  with the published contrast described as not reproduced under the
  documented specification.

## 5. The US-anchored catalog

Pole locations for all 52 aligned months were recorded from the v2.11
run and classified against Natural Earth 50 m admin-0 polygons
(`pole_classification.csv`). Of the 104 poles: **61 (58.7%) fall inside
the CONUS, 27 (26.0%) in Canada, 16 (15.4%) in Mexico; 41.3% of the
catalog's poles are anchored outside the United States.** Eleven poles
(10.6%) sit on the domain's northernmost cell row (49.75°N): 6 dry poles
and 5 wet poles. The Arm A set is similar (51 of 92 poles in CONUS,
55.4%; 12 anchored months).

**US-anchored months** (both poles inside the CONUS) number **15 of 52**
in the aligned catalog: 1980-05, 1987-12, 1988-04, 1995-03, 1999-08,
2001-04, 2004-05, 2004-09, 2005-02, 2007-05, 2011-12, 2013-06, 2015-06,
2016-10, 2020-05. These 15 months carry the US-anchored headline
conditioning in Phase 3, and the pole geography becomes a Results
subsection of Paper 1 rather than a buried diagnostic: a catalog whose
dry and wet poles sit outside the country in two of five cases cannot be
described, without qualification, as a catalog of events "over the
contiguous United States".

## 6. Provenance

- Inputs: `seg-revision/seg_rerun/data/spei01.nc` (SPEIbase v2.11, MD5
  above); `cdpe_sensitivity/results/run_armA_2026-10-05/
  cdpe_monthly_series.csv`; `cdpe_sensitivity/results/
  run_armA_speibase_rebuild_2026-11-02/B_speibase_full/
  baseline_poles.csv`; Natural Earth 50 m admin-0 in
  `cdpe_sensitivity/data/natural_earth/`.
- Code: `code/28_subset_test_companion.py`,
  `code/31_catalog_alignment.py` (this project).
