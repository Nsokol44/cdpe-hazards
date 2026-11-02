# Implementation checklist — CDPE two-paper split (2026-11-02)

Work order: the two external reviews of 2026-11-02 (text review and
figures review) plus the third review installment (Paper 2 design and
the Paper 1 circularity question), adopted by the author the same day:
"Implement this to further distinguish the papers. Rebuild as needed.
I want all of it implemented except anything that's redundant. Replace
figures as needed." Governing directive: "We need these studies to
match the SEG paper catalog." Outcome: Paper 1 (frequency) is a single
Natural Hazards paper rebuilt on the companion catalog; Paper 2
(physical dynamics) targets the AAS "Compound Climate Extremes"
special issue (deadline 15 January 2027) at design stage. Lightning is
excluded from both papers. Statuses: DONE (evidence given),
REDUNDANT-SKIPPED (reason given), BLOCKED-ON-AUTHOR (what is needed).

## Phase 0 — SEG safety

- McKee et al. 1993 page range in the SEG R1 manuscript corrected
  179–183 → 179–184 (true range verified against three independent
  bibliographies and WMO-No. 1090; Crossref does not index the
  proceedings paper). DONE. Evidence: single-string DOCX edit;
  extracted-text diff shows only that change; Drive copy updated in
  place and read back (28,393 B).
- SEG catalog provenance confirmed: SEG's national numbers derive from
  the companion Study-1 catalog on SPEIbase v2.11 (its script imports
  Sokol_Study1_CDPE_Identification; Arm A has no 2-degree scenario, so
  the 162-at-2-degrees figure cannot be an Arm A product). SEG is NOT
  contaminated by the Arm A divergence. DONE (recorded; no SEG edits
  beyond McKee). SEG R1 upload by 4 November 2026 remains the author's
  act.
- NH bibliography already printed 179–184; verified again in the
  rebuilt DOCX. DONE.

## Phase 1 — One catalog, US-anchored

- Subset test run (code/28_subset_test_companion.py,
  code/31_catalog_alignment.py, cross-asserted identical): the
  companion's 52 published SPEI-1 months contain ZERO months in 2024,
  so the review's window hypothesis explains 0% of the 46-vs-52 gap.
  Arm A's 46 are not a subset (intersection 32; 14 Arm-A-only; 20
  companion-only; Jaccard 0.485 vs 4.5 expected by chance). DONE.
- Port-vs-release check: the frozen Arm A port on the v2.11 field
  returns exactly the companion's 52, and the grid-max configuration
  returns exactly the published 214. The port is faithful; the release
  difference (v2.10 / CRU TS 4.08 vs v2.11 / CRU TS 4.09) is PROVEN for
  SPEI-1. DONE.
- Headline catalog adopted = the companion 52 months (all inside
  January 1980 – December 2023). Decision and reasoning in
  CATALOG_ALIGNMENT_2026-11-02.md; conditioning rerun in Phase 3. DONE.
- Poles generated from the v2.11 run and classified (Natural Earth):
  104 poles; CONUS 61 (58.7%), Canada 27 (26.0%), Mexico 16 (15.4%);
  dry poles outside CONUS 44.2%, wet poles 38.5%; 20 dry poles at
  latitude ≥ 47.75°N; US-anchored months (both poles in CONUS) = 15.
  Saved: results/alignment_2026-11-02/ (aligned_month_sets.csv,
  pole_classification.csv, alignment_summary.json). DONE.
- SPEI-3 / SPEI-6 alignment to v2.11: BLOCKED (v2.11 spei03/spei06
  files unobtainable; two author uploads were rejected as non-v2.11
  files and quarantined). Recorded as a stated limitation; the
  envelope keeps the v2.10 sets and the paper carries a provenance
  table (detector, release, CRU version, window per analysis set),
  disclosing the internal CRU mix (SPEI via CRU TS 4.08; SPI-1 from
  CRU TS 4.09 precipitation). Count accounting: SPEI-3 gap 16 exceeds
  any window contribution (≤ 12); SPEI-6 gap 5 unattributed.
- SPI-1 closure (companion 66 vs Arm A 22): BLOCKED-ON-AUTHOR (the
  companion's original spi01.nc and script were never supplied; local
  variants give 3–27). Evidence note prepared for the Physical
  Geography editor: PG_COMPANION_NOTE_2026-11-02.md (prepare-only, not
  sent). The note also records that SPEI-1 and the grid max reproduce
  exactly on v2.11, so no companion correction is needed there.

## Phase 2 — Arm B tie-break fix and decomposition redo

- Review's zero count verified: 272 of 720 archived masked Arm B
  scenarios are zeros (empirical 241, log-logistic 31); the archived
  zeros came from non-deterministic tie-breaking in pole selection.
  DONE (verified).
- Deterministic fix implemented as a new module
  (cdpe_sens/detector_tiefix.py; the frozen author detector is
  untouched): uniform choice among exactly tied finite cells, seed =
  first 8 bytes of SHA-256 over the documented string
  cdpe-tiefix-v1 | base seed 20261102 | scenario | month | pole;
  bit-identical rerun asserted; reproduce-first gate passed (720/720
  archived counts reproduced before the fix). DONE.
- Corrected results: zeros 272 → 58; masked NARR SPEI-6 empirical
  baseline 6 → 68 months (5-seed range 68–84); ERA5 empirical 27 →
  109; masked log-logistic 44 → 50. DONE
  (cdpe_sensitivity/results/run_armB_tiefix_2026-11-02/).
- Variance decomposition redone on log counts for both arms, raw
  counts kept alongside, higher-order interactions as their own
  category, shares exact (sum to 1.0): Arm B fitting-distribution
  share collapses (log 0.345 → 0.0003; raw 0.188 → 0.005); threshold
  dominates (Arm B log 0.786, Arm A log 0.854); radius second (0.120 /
  0.076). The old abstract's "threshold and fitting distribution
  dominate" claim was therefore wrong and has been rewritten. DONE.

## Phase 3 — Paper 1 statistics rebuilt

- Continuity gate: the frozen estimator on the Arm A 46 reproduces
  tornadoes 1.13, hail 1.10, heat 0.90 exactly before any new number
  was used. DONE.
- Headline conditioning on the aligned 52 (same-month, stratified
  ratio): tornadoes 1.16 (0.78–1.53), hail 1.01 (0.70–1.37), heat-wave
  days 0.88 (0.50–1.42). US-anchored 15: 0.99 / 1.00 / 0.93. DONE.
- Count model as primary estimand (calendar-month effects, year term,
  ONI covariate; ONI fetched from NOAA CPC, archived with
  DATA_MANIFEST and SHA-256): Poisson dispersion 44.9–2048 in every
  cell, so the negative binomial is primary everywhere. NB incidence
  rate ratios, aligned same-month: 1.09 (0.79–1.49) / 1.12 (0.89–1.41)
  / 0.91 (0.60–1.37). DONE.
- Lagged-regime arm as a FIRST-CLASS analysis (author-directed
  addition, 2026-11-02, from the third review installment):
  antecedent-month CDPE sets, following-month hazards, same model and
  robustness. Ratio: 1.12 / 1.10 / 1.15. NB: 1.00 / 0.96 / 1.14
  (attenuation for tornadoes and hail, none for heat). DONE. The
  lagged SPEI-3/6 variant is not constructible (no aligned v2.11
  SPEI-3/6 sets) — recorded in the report and the paper.
- Robustness: leave-April–May-2011-cluster-out on both arms
  (same-month ratios fall to 1.00 / 0.86 / 0.70: the aligned signal is
  2011-dependent); leave-one-month-out ranges; median contrasts. DONE.
- Split-era with corrected interpretation: within-era ratios reported;
  every era-difference interval includes 1 (tornadoes 1.47
  [0.85–2.24], hail 1.41 [0.98–2.01], heat 1.32 [0.46–3.28]): era
  differences are noise-compatible; no emergence claim. DONE.
- Pole-relative strata (frozen Step-04 1-degree counts vs matched
  non-CDPE calendar months): tornadoes near wet pole 2.52
  (1.12–5.02), near dry pole 0.56 (0.17–0.77), elsewhere 1.16; hail
  near dry 0.71, near wet 1.13; with the small-share caveat (strata
  hold 1.4% and 6.3% of CDPE-month tornado reports). Heat waves are
  not constructible on the report grid (gridMET cell field) —
  recorded. DONE.
- Power / MDES at 80%: same-month n = 52: 1.67 / 1.74 / 1.87; lagged
  n = 52: 1.61 / 1.65 / 2.21; US-anchored n = 15: up to 2.40. The
  design cannot detect effects of the observed size; the paper's
  framing is inconclusive, not a proven null. DONE.
- Masked-coverage control written as a supplement section, every
  number reconciled against the archived nclimgrid_rebuild_2026-11-02
  outputs and SPEIBASE_REBUILD_REPORT.md (masked 10/15/14; gate
  failures 296 → 436 of 528 months; valid cells 3,575 vs 4,399;
  dry-tail cell-months ≤ −1.5: 3.9% nClimGrid vs 5.7% SPEIbase; wet
  8.1% vs 7.9%). DONE (results/phase3_2026-11-02/
  supplement_masked_control.md, folded into the supplement).
- Jaccard overlaps reported with chance baselines: SPEI-3 vs SPEI-1
  12 observed vs 4.18 expected; SPEI-6 vs SPEI-1 4 vs 4.44 (at
  chance); companion vs Arm A 32 vs 4.53; NARR vs ERA5 17 vs 7.23.
  DONE.
- Spearman annual-count correlations (promised in Methods, previously
  unreported) now computed and reported: tornadoes −0.14 (p = 0.38),
  hail −0.20 (p = 0.19), heat +0.02 (p = 0.91). DONE.
- Era representation: 24 of 52 aligned months (46.2%) fall in
  1980–1995 vs the era's 36.4% share of the window. DONE.
- Lightning arm: REDUNDANT-SKIPPED (only 4 in-window CDPE months on
  the settled inputs; cannot support an analysis; the author's
  standing decision, recorded in both papers' scopes).

## Phase 4 — Figures replaced (all ≤ 6.85 in wide, opaque white RGB,
300-dpi PNG + vector PDF, every render visually inspected)

- Fig. 1: panel (a) unchanged; panel (b) REPLACED with a
  calendar-month × era standardized local rate-ratio map with
  Poisson-interval stippling (672 cells shown; 229 stippled, 164 above
  1 and 65 below; report-weighted aggregate 1.06; method and the
  unadjusted-interval caveat stated in the caption; era stratification
  added after the first render showed the reporting-growth artifact).
  DONE.
- Fig. 2 poles: one dot per pole-month, colored by season, shared
  legend above, no colorbar, outside-CONUS shading, printed shares
  (dry 44%, wet 38% outside CONUS). DONE.
- Fig. 3 (supplement-order heatmaps): Arm A count printed in every
  cell, baseline cell outlined in all panels, colorbar corrected to
  "CDPE months, 1980 to 2023". DONE.
- Fig. 4 (variance): both arms, log-count shares, distinct main-effect
  colors, interactions grey, higher-order as its own category, values
  printed; caption states the shares are exact closed shares of a
  complete enumeration (no sampling uncertainty). DONE.
- Merged forest plot replacing the old Figs. 5 and 6: all 23 included
  envelope configurations per primary hazard with point and interval,
  rows labeled by index, threshold and radius, Arm A baseline
  highlighted, aligned-catalog and US-anchored headline rows as
  distinct markers, log axis with full ticks. DONE
  (fig_forest_envelope).
- Series figure rebuilt as monthly anomalies with the 52 aligned
  months shaded and the April–May 2011 cluster and the 1996–98
  reporting step annotated. DONE.
- Figures renumbered by first mention (1 geography, 2 poles, 3 forest,
  4 series, 5 heatmaps, 6 variance) and every in-text reference
  updated. DONE.
- CDPE-events report map (built during the rebuild): REDUNDANT-SKIPPED
  for the paper (archived in the repository and sensitivity results;
  Fig. 1a and the pole-relative analysis cover the geography with
  matched controls).

## Phase 5 — Paper 1 manuscript rebuild (Natural Hazards)

- Manuscript rewritten to the Paper 1 spec: frequency question;
  aligned catalog with provenance table; US-anchored headline; count
  model primary; lagged arm first-class with the circularity rationale
  stated plainly in Methods and the agreement/attenuation reading in
  Discussion (attenuation under lagging is evidence about how much of
  the same-month association is reverse-caused); Arm A envelope as
  robustness backbone with nesting and non-independence disclosed;
  the 7 of 23 hail configurations whose intervals exclude 1 (all
  SPEI-3/SPEI-6) reported as the thesis's best illustration; Arm B
  (corrected) confined to the supplement with the masked-control
  section. DONE (PHASE5_REWRITE_REPORT.md).
- Highest-priority text fix: the supplement's false sentence "Both
  studies use the same SPEIbase release (v2.10), so a difference
  between releases is ruled out" is replaced with the proven account
  and the month-level diff; the §3.1 "does not reproduce" framing is
  rewritten likewise. DONE.
- Verified text defects fixed: hail criterion sentence (NWS severe
  threshold 0.75 in until 5 January 2010; 1.00 in applied throughout
  for consistency); abstract states exact windows per arm (Arm B ends
  2014) and is 194 words (programmatic count); Spearman reported;
  "for the first time" softened; ridge/trough sentence rewritten as
  hypothesis (no composite exists in either paper); Wheaton, Yoon,
  AghaKouchak and Das & Allen re-scoped to what they support; Das &
  Allen article number 47 added; "honest null" replaced by
  inconclusive framing with the MDES; split-era passages corrected;
  land-mask result reframed as a caution; pole geography promoted to
  a Results subsection; "sustained drought" wording reconciled with
  the SPEI-1 baseline; Table captions state both windows. DONE.
- References per Springer practice: both in-pipeline Sokol entries
  removed from the reference list (the companion is mentioned once in
  text as "Sokol 2026, in revision"); the SEG citation cut entirely;
  citation closure verified 35 cited / 35 listed, no orphans. DONE.
- Rebuild and QA: DOCX rebuilt for manuscript and supplement;
  preflight (pf wrapper, profile nick) 0 errors on both with text
  identity; full number trace against Phase 1–3 outputs; figures
  inspected in situ in an 18-page render. DONE.
- Drive: the NH folder (1cpdPXhSfWNm7WMawdxYRRGMFvVjYTIX1) updated in
  place, sizes verified (manuscript DOCX/MD, supplement DOCX/MD,
  references, all six figures; fig_forest_envelope created new). The
  superseded fig_h1_forest and fig_h2_envelope files remain in the
  folder for the author to delete; nothing was deleted. No NH fact
  sheet exists (the fact sheet on record belongs to the retired AAS
  package), so none was regenerated. The cover letter was out of
  scope for this pass and still carries pre-rebuild framing; flagged
  for the author's call before submission. DONE with those notes.
- AAS hazards version retired: superseded note in AAS_COMPLIANCE.md
  (local and Drive, 30,036 B verified); START HERE index entry 2
  updated to RETIRED and entry 8 updated to the final state; the
  AAS-2026-0874 desk rejection (31 October 2026) stands as the record.
  DONE.
- The review's doubled-title claim: REDUNDANT-SKIPPED (checked in all
  current local and Drive builds; not present). The review's
  dual-submission concern: not a problem (AAS-2026-0874 was
  desk-rejected 2026-10-31; Natural Hazards only).

## Phase 6 — Paper 2 design fold-in (no analysis run)

- One dated amendment appended to cdpe-dynamics-aas/DESIGN_MEMO.md
  (sections A1–A9); the frozen memo body is byte-identical (backup
  verified; 17,721 → 40,781 B). DONE.
- Venue settled per the author: AAS "Compound Climate Extremes"
  special issue, deadline 15 January 2027 (the review's MWR/JAMC/WCE
  suggestions are recorded in the amendment and closed). DONE.
- Folded in: circularity fix as first principle (regime from the
  antecedent state; severe days in the following month; 2×2 retained
  on top); mechanism steps (STP/SCP/SHIP decomposition into CAPE,
  shear, SRH and LCL; Lagrangian trajectories or moisture budget;
  dry-pole soil-moisture coupling); frame extended to 1950–2023 with
  significant-severe events only (EF2+, hail ≥ 2 in); permutation
  composites with field significance; controls matched on calendar
  month, era and ENSO; block bootstrap by CDPE month; shared-catalog
  rule (same aligned, US-anchored v2.11 catalog; cites Paper 1; no
  reused results); literature plan engaging the elevated-mixed-layer,
  Great Plains low-level jet, and soil-moisture–convection strands.
  DONE.
- Pre-committed headline hypothesis recorded verbatim: "dry poles
  over the Mexican Plateau and Southwest feed an elevated mixed layer
  that strengthens the cap and lapse rates, while wet poles sit where
  low-level moisture transport is enhanced", with the explicit clause
  that if the data do not show it, the paper has no story. DONE.
- Go/no-go pilot fully specified as the mandated first execution step
  (event lists back to 1950, reduced variable set: 5 pressure
  variables on 13 levels + 6 single-level fields; volume audit ~93 GB
  at perfect packing vs ~572 GB for the full design, against 124 GB
  of disk; if nothing is field-significant, the deliverable is a
  short note). DONE (design only).
- Pilot and pipeline execution: BLOCKED-ON-AUTHOR (the reanalysis
  decision: ERA5 needs the author's own Copernicus CDS credentials,
  which do not exist in this environment; NOAA NARR is verified
  working end to end for 1980–2023 and is the recommended path for the
  hazards-era portion. No dataset has been substituted.)

## Phase 7 — Sync

- GitHub (Nsokol44/cdpe-hazards, branch main): DONE. Four commits,
  remote tree verified (manuscript size matches local exactly):
  999de782 (NH build: manuscript, supplement, references, code 28–38,
  reports, README addendum); 56f58e12 (Phase 1–3 outputs incl. the
  archived ONI series; Arm B tiefix run); a95ccd92 (detector_tiefix
  module and rerun script); 4fbf07bb (paper2_design/DESIGN_MEMO.md).
  The push tool accepts UTF-8 text only, so DOCX and figure binaries
  are not in the repository; they live in the Drive package.
- Repository default branch: BLOCKED-ON-AUTHOR. The default branch is
  still master (a lone README) while the archive lives on main.
  Author-side fix, three clicks: repository Settings → General →
  Default branch → switch to main.
- This checklist: filed in the NH project and the NH Drive folder.
  DONE.

## Remaining author acts (summary)

1. Submit the Natural Hazards package via the portal (author's act).
2. Upload the SEG R1 package by 4 November 2026 (author's act).
3. Delete fig_h1_forest / fig_h2_envelope from the NH Drive folder
   (superseded by fig_forest_envelope) when convenient.
4. Decide whether the NH cover letter is refreshed before submission.
5. Make the reanalysis call (ERA5 via a new CDS account, or NARR) to
   unblock the Paper 2 pilot.
6. Switch the GitHub default branch to main (three clicks, above).
7. Optional: supply the companion's original spi01.nc / script if
   SPI-1 closure with the Physical Geography editor is wanted.

## Addendum (2026-11-02, figure-defect fix and sweep)

- Defect: in Figure 1 (fig_map_geography), panel (b)'s single-line
  title "(b) Calendar- and era-matched local rate ratio" was clipped
  by the right-hand colorbar, rendering as "(b) Calendar- and
  era-matched local rate ra" with the remainder hidden. The Phase 4
  checklist had recorded every render as visually inspected; the
  defect shipped anyway. Caught by: the lead agent's first-hand
  verification read of the rebuilt figure after the implementation
  reported completion.
- Fix: code/37_fig1_geography_localrr.py now sets a three-line panel
  (b) title in the same pattern as panel (a): "(b) Local rate ratio
  in CDPE months, / calendar- and era-matched / (dots: interval
  excludes 1)". The stippling information stays on the figure and is
  also stated in the Figure 1 caption in the manuscript. No data,
  counts, or other figure elements changed (672 cells, 229 stippled,
  identical to the values in the caption and text). Figure re-rendered
  at the standing spec (6.85 in wide, opaque white background, RGB,
  300-dpi PNG + vector PDF) and read back by eye: titles, colorbar
  labels, and axis labels all complete, no clipping or collision.
  The fixed figure was also verified in situ on page 4 of the rebuilt
  manuscript render.
- Sweep of the other rebuilt figures (each PNG read by eye, the
  forest plot additionally at 2x crops of its right-hand annotation
  column): fig_map_poles CLEAN (titles, shared legend, and CONUS-share
  annotations complete); fig_forest_envelope CLEAN (all row labels and
  value annotations render in full; the annotation column sits tight
  against the right spine but nothing is clipped); fig_s1_count_heatmaps
  CLEAN (cell counts, baseline outlines, colorbar label complete);
  fig_s2_variance CLEAN (both panel titles and every bar value
  complete); fig_h3_series CLEAN (panel titles and both annotations
  complete, arrows unobstructed). No sibling defects found, so no other
  figure was re-rendered. The superseded fig_h1_forest and
  fig_h2_envelope are not used by the rebuilt manuscript and were not
  touched (they remain listed under author acts for deletion).
- Propagation: manuscript DOCX rebuilt with code/20_build_nh_docx.py
  (extracted text identical to the previous build) and the preflight
  fix pass re-run (pf wrapper, profile nick): 0 errors, no new
  findings; the formatted DOCX embeds the corrected Figure 1 (media
  bytes match the new PNG exactly) and its extracted text is identical
  to the previous formatted build. The supplement was not rebuilt (it
  embeds no figure that changed). Drive copies updated in place with
  sizes verified: fig_map_geography.png, fig_map_geography.pdf,
  manuscript_nh.docx (the preflight-formatted build, as filed in
  Phase 5), and this checklist.

---

## FIX ROUND 2 ADDENDUM — 2026-11-02 (the author's verification read, 09:49 EST)

**Item 1 — Cover letter.** The author's replacement letter was NOT FOUND. Searched: ~/workspace/user/files/ (newest files are the SEG package, 2026-11-02 02:49), the NH Drive folder (its cover_letter_nh.docx is the stale letter, Drive-modified 2026-11-02T05:35 UTC), a Drive-wide name search for letter files, and the project folder. Per the fallback branch, a replacement was DRAFTED from the rebuilt manuscript's claims only: cover_letter_nh_DRAFT_2026-11-02.md and .docx in the project (Times New Roman, built by code/43_build_draft_cover_letter.py). It carries the new title, the inconclusive framing, the aligned 52-month catalog, the count model, the lagged arm, the pole geography, and the four verified suggested reviewers (Zscheischler, Bevacqua, AghaKouchak, Tippett). It contains none of the four stale claims (string-verified absent: the 756-configuration ensemble, 46 months as the headline, "threshold and fitting distribution dominate", the 70 percent land-mask removal). It is marked DRAFT FOR AUTHOR APPROVAL and was NOT filed to Drive. The stale filed letter and the pre-round DOCXs are archived locally under pre_fix_originals_2026-11-02_fixround2/.

**Item 2 — Title.** The manuscript is retitled to exactly: "Do tornadoes, hail, and heat waves occur differently during concurrent drought-pluvial months? A count-model analysis over the contiguous United States" (MD YAML, DOCX body, and DOCX core title property; the supplement preamble matches). The START HERE Drive index was updated in place on the same file ID: entry 8 carries the new title, a fix-round-2 status line, and a stale-cover-letter warning. Entry 2 keeps the old title deliberately, because it quotes the title of the desk-rejected AAS submission of record (AAS-2026-0874); rewriting it would falsify that record. The repo README is updated in the fix-round-2 push.

**Item 3 — Title duplication.** Verdict: the title appears ONCE in the manuscript body (paragraph 0; paragraphs 1 to 4 are the author line, affiliation, corresponding author, and the Abstract heading). The doubling the author saw is an artifact of Drive's text export rendering the DOCX core title property alongside the first paragraph. No change made.

**Item 4 — Lagged pole-relative strata (code/41_lagged_pole_relative.py, seed 20261102; same design as code/35 shifted one month; 1,979 matched control month instances).** Tornadoes: near wet 1.37 (0.83 to 1.92), near dry 1.40 (0.91 to 2.17), elsewhere 1.13 (0.86 to 1.48). Hail: near wet 1.19 (0.61 to 1.94), near dry 0.84 (0.37 to 1.52), elsewhere 1.14 (0.88 to 1.44). Every lagged interval includes 1, and the same-month near-dry tornado deficit inverts (0.56 same-month against 1.40 lagged). Multiplicity: 12 stratum-hazard estimates across both timings, unadjusted. Text consequence (demotion branch): 2.52 removed from the abstract; Section 3.5 rewritten with a Timing-column Table 3 (12 rows) and the circularity caveat in the text; the Section 4 pole-relative paragraph rewritten with the reverse-causation reading stated plainly; Section 5 states the pattern does not survive lagging and is reported as exploratory; supplement S7 carries the lagged table and the multiplicity sentence; the Section 4 limitations item now calls it the exploratory pole-relative pattern.

**Item 5 — Paired difference (code/42_paired_difference.py, seed 20261102, B = 2000, month-paired over 527 outcome months, dispersion fixed at full-frame ML estimates).** Differences in log IRR, same-month minus lagged: tornadoes 0.086 (-0.215 to 0.374), hail 0.151 (-0.160 to 0.461), heat-wave days -0.224 (-0.853 to 0.467). All include zero. Text consequence: every causal-phrased attenuation sentence was replaced with the neutral report of both arms plus the paired differences and their intervals (abstract, Section 3.3, Section 4, Section 5).

**Item 6 — Northern-edge artifact test (code/40_edge_test.py; EDGE_TEST_NOTE.md in results/fixround2_2026-11-02/).** Frozen detector, baseline definition, SPEIbase v2.11, box expanded north by 3 degrees (top row 52.75 N) and by 5 degrees (54.75 N); the unexpanded control reproduces the 52 exactly. Expanded runs: 58 months at +3 (overlap 43, Jaccard 0.642) and 73 months at +5 (overlap 41, Jaccard 0.488); each expanded run places 7 dry poles on its new top row. Of the 20 northern baseline dry poles: at +3, moved north 8, moved to the new edge 3, same place 6, lost 3, moved south 0; at +5, moved north 10, moved to the new edge 1, same place 5, lost 4, moved south 0. Verdict: the pile-up is substantially an edge artifact at the level of pole location (11 of 17 and 11 of 16 retained months move north, never south, so those months' minima lie in Canada and the baseline pole is the clipped position), while CDPE qualification is more robust (17 of 20 and 16 of 20 months persist) and domain extent is itself a major catalog sensitivity. The headline catalog is unchanged (the 52). The note's draft limitations paragraph is FOR THE AUTHOR'S CALL and was not inserted into the manuscript. Paper 2 implication recorded in the note: pole-centred sampling must extend the domain north or treat northern dry poles as boundary-censored.

**Item 7 — Heat-wave series verification (code/39_verify_heatwave_2011.py).** Independent recompute from the raw gridMET daily Tmax files with the paper's own definition (3,608 land cells, matching the series of record exactly) reproduces the frozen values: June 2011 frozen 3.363 against recomputed 3.436 (+2.2 percent), July 2.936 against 3.014 (+2.7 percent), August 3.473 against 3.519 (+1.3 percent); the worst 2011 month differs by 16.4 percent (March, a near-zero month), and the 2012-07 record maximum also confirms (4.751 against 4.826). The small systematic offset matches the documented strided-threshold difference between the verification and Step 05. Verdict: the early-2011 plateau is data, not an artifact. No downstream heat numbers change.

**Item 8 — Wording.** (a) The Methods meta-instruction ("Two or three sentences in Section 3.6 summarize...") replaced with real prose describing how Section 3.6 and the supplement report Arm B. (b) Abstract "the catalog of the companion catalog study" repaired. (c) Companion corrected to the national study, under review, everywhere (introduction framing, in-text citation "(Sokol 2026, under review)", and Section 2.1 harmonized to "the companion national study"). (d) Early-era hail Discussion paragraph added (0.77 [0.60 to 0.98] early era against 1.08 later, era difference 1.41 [0.98 to 2.01] including 1, hail reporting inhomogeneity context, pooled estimate between the era values, no conclusion rested on it). (e) Full-text sweep for drafting or meta language: one instance found and fixed at (a); a residual "the one positive signal" in the Section 4 limitations list was caught by the post-build stale-string scan and corrected to "the exploratory pole-relative pattern".

**Build and file record.** Abstract 198 words (under the 200-word cap; inside the journal's 150 to 250 band). Citation closure 35 of 35. Preflight 0 errors on the manuscript and the supplement, text identical to original True for both. DOCX hygiene: w:val colors {000000} only, no themeColor, no python-docx metadata, creator Nicholas J. Sokol, core title property equals the new title. The extracted-text diff against the pre-round DOCXs shows only the directed changes. Drive NH folder updated in place: manuscript_nh.docx 2,031,678 B, supplementary_information_nh.docx 48,552 B, manuscript_nh.md 44,245 B, supplementary_information_nh.md 18,573 B, sizes verified on Drive. The cover letter was NOT updated (item 1). Note on the legacy suite: code/22_verify_nh.py's NH-against-AAS token-identity checks and its 188-word abstract assertion belong to the retired AAS comparison and the pre-split abstract; this round's verification used the presence and stale-string scans, citation closure, the extracted-text diff, and preflight recorded here. Fix-round code and outputs pushed to Nsokol44/cdpe-hazards (see the repository's commit history for the fix-round-2 commit).
