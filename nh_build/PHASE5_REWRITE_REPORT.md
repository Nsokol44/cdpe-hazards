# Phase 5 Rewrite Report — Natural Hazards manuscript (Paper 1)

**Date:** 2026-11-02 · **Scope:** manuscript_nh.md, supplementary_information_nh.md,
references_nh.bib, builders code/20 and code/23, rebuilt DOCX files, and the
Natural Hazards Drive folder (1cpdPXhSfWNm7WMawdxYRRGMFvVjYTIX1), updated in
place. The retired AAS hazards project, the sensitivity project, and GitHub
were not touched.

## What was done

The manuscript was rewritten to the post-review specification as the
frequency companion to the regional catalog study. The headline catalog is
now the companion Study-1 catalog (SPEIbase v2.11, SPEI-1, 52 months,
1980 to 2023) with its 15-month US-anchored subset. The negative binomial
count model (calendar month fixed effects, linear year, ONI covariate from
NOAA CPC on the ERSST v6 vintage) is the primary estimand, the stratified
ratio of means is retained for continuity, and a lagged (antecedent-month)
arm addresses reverse causation. A provenance table (Table 1) states the
detector, data release, CRU version, window, and size of every analysis
set, including the disclosure that the Arm A SPEI fields rest on CRU TS
4.08 (SPEIbase v2.10) while the Arm A SPI-1 sets were computed from CRU TS
4.09 precipitation, and that SPEIbase v2.11 SPEI-3/6 files could not be
obtained, so the envelope runs on v2.10. Results are restructured as
Sections 3.1 to 3.7 (aligned catalog and pole geography, headline
conditioning, lagged arm, robustness, pole-relative strata, definition
envelope with the corrected Arm B summary, detectability). The discussion
and conclusions use the inconclusive framing throughout: the design
detects only rate ratios above about 1.6 to 1.9, so the estimates bound
rather than exclude an association. No "honest null" phrasing remains.

The supplement was rewritten in full: S1 gives the proven catalog account
(the port is faithful on both fields, the releases differ, the 14
Arm-A-only and 20 companion-only months and the 15 US-anchored months are
listed, and the false same-release sentence of the previous supplement is
deleted and explicitly withdrawn). S2 gives the corrected Arm B (tie rule,
272 of 720 zero-count scenarios before the fix and 58 after, corrected
baseline counts, corrected raw and log-count decompositions). S3 folds in
the masked-control section from
results/phase3_2026-11-02/supplement_masked_control.md near-verbatim (em
dash removed for the standing style rules, numbers unchanged and
re-verified). S4 to S10 give the split-era table, median contrasts,
leave-one-month-out ranges, the pole-relative table, the seven hail
configurations, the Jaccard table with chance baselines (with the SPEI-6
overlap stated as at chance, 4 observed against 4.44 expected), the MDES
table, Spearman correlations, and era representation.

## Verification

- **Abstract word count: 194 words**, counted programmatically on the
  abstract block (inside the required 150 to 200 band).
- **Preflight (pf wrapper, profile nick): 0 errors on both DOCX files**,
  with "text identical to original: True" on the fix pass for each.
  Logs: preflight_manuscript.log and preflight_supplement.log in this
  project. Remaining manuscript warnings are documented non-errors: the
  "Sokol 2026" author-year warning is the directed in-text companion
  mention with no reference entry, "B = 2000" is the bootstrap size, the
  two NUM-PCT warnings misread the pole percentages whose denominator is
  104 poles (27 of 104 is 26.0 percent and 16 of 104 is 15.4 percent,
  verified), the et al. warning reflects the bib "and others" entries in
  Springer form, and the REF-ORDER warning is triggered by the
  Statements and Declarations block that follows the reference list. The
  supplement warning (no reference list) is expected, as the supplement
  carries no bibliography by design.
- **Citation closure: 35 cited / 35 listed, 0 orphans in either
  direction**, checked programmatically against references_nh.bib. Both
  unpublished Sokol entries were removed from the bib and the reference
  list. The companion is mentioned in text exactly once, as "Sokol 2026,
  in revision", with no reference-list entry and no entry for the SEG
  companion. McKee et al. 1993 renders at pages 179 to 184 (verified in
  the built DOCX). Das and Allen 2024 now carries article number 47 and
  renders as "npj Nat Hazards 1:47".
- **DOCX hygiene (formatted builds):** 9 captions (3 tables, 6 figures),
  35 rendered reference entries, 6 embedded figures matching the six
  figure files by MD5, no themeColor, no "python-docx" metadata, creator
  "Nicholas J. Sokol", all text black. The old fig_h1_forest and
  fig_h2_envelope files are not embedded anywhere. LibreOffice renders:
  manuscript 18 pages, supplement 7 pages, figure and table pages
  visually inspected (Table 2 complete on one page, booktabs rules).
- **Em dashes: 0** in both sources. Semicolons appear only inside
  citation groups in the manuscript and nowhere in the supplement. No
  AI-use declaration anywhere. Funding statement is the standard
  no-funding declaration. Data availability is GitHub only
  (github.com/Nsokol44/cdpe-hazards).

## Figure-number mapping used (final numbering by first mention)

| Figure | File | First mention |
|---|---|---|
| Figure 1 | fig_map_geography | Section 2.2 (hazard data) |
| Figure 2 | fig_map_poles | Section 3.1 |
| Figure 3 | fig_forest_envelope | Section 3.2 |
| Figure 4 | fig_h3_series | Section 3.4 |
| Figure 5 | fig_s1_count_heatmaps | Section 3.6 |
| Figure 6 | fig_s2_variance | Section 3.6 |

## Number trace (where each headline number came from)

- Same-month and lagged ratios and NB IRRs for the 52 and the 15,
  leave-2011-out ratios and NB analogues, LOO ranges, median contrasts,
  split-era ratios and era differences, pole-relative ratios and shares,
  MDES values, Spearman correlations, and era representation:
  results/phase3_2026-11-02/PHASE3_RESULTS.md (sections 1 to 7, 9, and
  10), read from its saved CSV outputs. A scripted presence check
  confirmed every headline value string in the rewritten text.
- Catalog counts (52, 46, intersection 32, 14 Arm-A-only, 20
  companion-only, Jaccard 0.485, chance expectation 4.5), pole geography
  (104 poles, CONUS 61 at 58.7 percent, Canada 27 at 26.0 percent,
  Mexico 16 at 15.4 percent, dry poles outside CONUS 44.2 percent, wet
  38.5 percent, 20 dry poles at or north of 47.75 N), and the
  US-anchored 15-month list: CATALOG_ALIGNMENT_2026-11-02.md and
  results/alignment_2026-11-02/alignment_summary.json and
  pole_classification.csv.
- Figure 1 panel b statistics (672 displayed cells, 229 intervals
  excluding 1, 164 above and 65 below, report-weighted aggregate 1.06):
  recomputed in this phase from
  results/phase3_2026-11-02/monthly_cell_counts.csv with the Figure 1
  script (code/37) construction, matching the values in the tasking.
- Corrected Arm B (zeros 272 of 720 before and 58 after, masked NARR
  SPEI-6 empirical baseline 68 in place of 6, ERA5 109, log-logistic
  masked 50, threshold shares 0.854 Arm A and 0.786 Arm B on log counts,
  radius 0.076 and 0.120, distribution share 0.345 to 0.0003 on log
  counts and 0.188 to 0.005 on raw counts):
  cdpe_sensitivity/results/run_armB_tiefix_2026-11-02/PHASE2_REPORT.md
  and its decomposition_tiefix.csv.
- Masked-control numbers (46/48/51 full, 10/15/14 masked, 3/8/8
  nClimGrid, gate failures 296 to 436 of 528, valid cells 3,575 and
  4,399, dry tails 3.9 and 5.7 percent, wet tails 8.1 and 7.9 percent):
  results/phase3_2026-11-02/supplement_masked_control.md, whose own
  verification note ties each number to the archived run outputs.
- Seven hail configurations and their intervals: PHASE3_RESULTS.md
  section 8. Jaccard chance baselines (12 against 4.18, 4 against 4.44,
  32 against 4.53, 17 against 7.23): PHASE3_RESULTS.md section 7.
- Land-mask comparison counts (NARR 175 to 44, ERA5 217 to 69 in the
  original run): REVIEW_TRIAGE_2026-11-02.md section D5, retained as an
  original-run comparison and reframed as a caution.
- Hazard record totals (54,607 tornadoes, 229,650 severe hail, 379,430
  hail overall) and Storm Events processing counts: retained from the
  previous manuscript and asserted in the Phase 3 validation
  (PHASE3_RESULTS.md section 0).

No number in the rewritten texts could not be sourced to one of the
files above.

## Drive filing (folder 1cpdPXhSfWNm7WMawdxYRRGMFvVjYTIX1, in place, sizes verified against local bytes)

Updated by file ID: manuscript_nh.docx (formatted build) 2,023,241,
manuscript_nh.md 39,581, references_nh.bib 11,573,
supplementary_information_nh.docx (formatted build) 47,814,
supplementary_information_nh.md 17,294, fig_map_geography.png 229,016,
fig_map_geography.pdf 960,100, fig_map_poles.png 335,776,
fig_map_poles.pdf 1,236,950, fig_h3_series.png 302,168,
fig_s1_count_heatmaps.png 135,692, fig_s1_count_heatmaps.pdf 21,937,
fig_s2_variance.png 210,089, fig_s2_variance.pdf 21,873.
Created new: fig_forest_envelope.png (936,335,
17younTcWHIvuRYeya_jbVbjf-mFzlwax) and fig_forest_envelope.pdf (52,606,
1b4Dwu8j-YVbfaGaDiXutSGI5t0UTpQZP), plus this report.
Nothing was deleted. The superseded fig_h1_forest.png and
fig_h2_envelope.png and fig_h2_envelope.pdf remain in the folder for the
author to delete.

## Deviations and notes

1. The Phase 5 tasking for Section 2.2 referred to the 1996 to 1998
   reporting step as visible in "Fig. 6", but the tasking's own final
   figure numbering makes the series figure Figure 4. The text points
   to Section 3.4 instead, and Figure 4 is first cited there, keeping
   first-mention order sequential.
2. No PDF of the manuscript was filed. Per REBUILD_REPORT_2026-11-02.md,
   the Natural Hazards package has no PDF route (PDFs were filed only
   for the AAS package), so the PDF was produced locally by LibreOffice
   for render QA only and not added to the project or Drive.
3. No fact sheet exists in the NH project or the NH Drive folder (the
   fact_sheet.txt on record belongs to the AAS package), so none was
   regenerated.
4. fig_h3_series.pdf (36,960 bytes) was already present in the Drive
   folder at exactly the size of the local Phase 3 render, verified in
   the final folder listing, so it needed no update. The other replaced
   figures were updated in both PNG and PDF.
5. Builders: code/20 now expects 9 captions, applies booktabs to all
   three tables, and sets Table 2 column widths for its new four-column
   layout. code/23 was extended to render the rewritten supplement's
   YAML front matter, headings, markdown tables (booktabs), and inline
   emphasis, as the previous builder could not build a supplement with
   tables. Both builders remain deterministic.
6. Where the tasking quoted the US-anchored lagged heat-wave NB estimate
   as the point value 0.73 only, the full interval from PHASE3_RESULTS.md
   (0.73, 0.40 to 1.32) is printed. Where the tasking described the Arm B
   distribution-share collapse as "0.345 (raw counts)", the source files
   place 0.345 on the log-count scale (raw counts: 0.188 to 0.005), and
   the text and supplement state both scales exactly as sourced.
7. The cover letter was not in the Phase 5 scope and is unchanged.
