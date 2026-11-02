# Rebuild Report — 2026-11-02

**Scope.** Both hazards-paper packages rebuilt on the author's 2026-11-02
decisions: the lightning (GLM) arm removed everywhere, the
pole-geography map added, and (AAS package) the AI-use declaration
removed. Authoritative inputs: `SPEIBASE_REBUILD_REPORT.md` and the
no-lightning conditioning outputs in
`cdpe_sensitivity/results/run_armA_speibase_rebuild_2026-11-02/C_conditioning/`,
whose retained blocks are bit-identical to the previous run of record.
The nClimGrid episode does not enter either manuscript. No other text,
number, or claim was changed; the extracted-text diffs against the
pre-rebuild packages show only the directed change classes.
Pre-rebuild originals are preserved in each package under
`pre_rebuild_originals_2026-11-02/`.

Both manuscripts are retitled: "How much does the definition matter?
Concurrent drought-pluvial regimes and the occurrence of tornadoes,
hail, and heat waves over the contiguous United States".

## Natural Hazards package (`cdpe-hazards-natural-hazards/`)

### Change inventory
- Title retitled (lightning removed).
- Abstract: lightning clauses removed; retained numbers identical
  (tornado RR 1.13, hail 1.10, heat-wave days 0.90; 46 of 528 months).
  **188 words** (recounted programmatically; inside Springer's
  150–250 band).
- Section 1: research question now three hazards; "link lightning and
  large hail" trimmed to "link large hail" (the Battaglioli citation
  stays, cited for large hail).
- Section 2.3: the GLM data paragraph deleted. Section 2.4: the
  lightning envelope-restriction clause deleted.
- Section 3.1: substance unchanged; a pointer sentence added ("Figure 2
  maps the dry and wet pole locations of the 46 baseline months").
- Section 3.2: the short-record lightning sentence deleted.
- Section 3.3: the lightning-envelope sentence deleted; "all four
  primary hazards" → "all three primary hazards"; "heat waves and
  lightning also fail" → "heat waves also fail"; "no detectable
  difference for heat waves or lightning" → "for heat waves".
- Section 4: the "Lightning, finally, …" paragraph deleted; limitations
  now two (the GLM limitation removed; the domain-composition
  limitation stays).
- Section 5: "conditioning four hazards" → "three hazards"; the
  sampled-lightning clause deleted.
- Table 3: lightning row deleted; caption now "(23 configurations)".
- Acknowledgments: "and GOES-16 GLM" removed from the dataset list.
- References: the three entries cited only for the lightning arm
  removed (NOAA GLM data notice, Goodman et al. 2013, Bateman et al.
  2021). 40 → **37 entries**.
- Cover letter: title and hazard list updated.
- Supplement (author's R3, the version of record): the quoted
  manuscript title updated in the DOCX in place (single-string edit;
  nothing else touched). Its substance, including the Section 3.1
  comparison, is unchanged.
- Data availability statement: unchanged, as directed (it still lists
  GOES-16 GLM among the public source datasets; see Flags).

### Figure inventory (7 figures, all inserted at 6.0 in)
1. `fig_map_geography` — report geography (unchanged position; file
   refreshed from the SPEIbase rebuild render, same design and data).
2. `fig_map_poles` — **new**: pole geography of the 46 baseline
   months, in Section 3.1 after Table 2, with a self-contained caption
   (dry poles 43 cells, wet poles 42, at most 3 months per cell; one
   shared colour scale).
3. `fig_s1_count_heatmaps` (was Figure 2). 4. `fig_s2_variance` (was
   Figure 3). 5. `fig_h1_forest` (was Figure 4) — regenerated without
   the lightning row. 6. `fig_h2_envelope` (was Figure 5) — regenerated
   as three panels; caption now "the three primary hazards".
   7. `fig_h3_series` (was Figure 6) — regenerated with three panels;
   caption drops the GLM panel. All in-text references renumbered.

### Verification (all gates pass)
- `code/22_verify_nh.py`, updated for the new inventory and arm set:
  **ALL PASS** — citation closure 37 cited / 37 listed, rendered
  reference entries 37, DOI sets equal; number trace 314 literals in
  the abstract and Sections 3–5, **0 unmatched**, with the NH–AAS
  delta exactly the directed Section 3.1 move plus the "S1" pointer
  token; NH–AAS numeric-token identities hold at md and DOCX level
  with only the itemised explained differences; abstract 188 words;
  keywords 6; em dashes 0; semicolons only inside citations; DOCX
  hygiene (no python-docx string, no themeColor in content parts, all
  content colours black, creator "Nicholas J. Sokol", blank
  dc:description, line numbering present, 7 embedded figures
  MD5-matched to `figures/`, 10 captions with keep_with_next).
- Preflight (pf wrapper, profile nick) on manuscript, cover letter,
  and supplement: **0 errors**, "text identical to original: True" on
  every format fix.
- Render: manuscript rendered via LibreOffice (14 pages); every figure
  page (pages 4–10) visually inspected — figures inside the text
  block, titles and legends complete, no clipping or collisions.

## AAS package (`cdpe-hazards-aas/`)

### Change inventory
- Mirrors the NH package edit for edit (title, abstract, Sections 1,
  2.3, 2.4, 3.2, 3.3, 3.4, 4, 5, Table 3, acknowledgments, cover
  letter, references 40 → **37**). The AAS abstract keeps its own
  wording ("passing the pre-specified robustness rules"; "(2018 to
  2023, sampled)" parenthetical removed with the rest of the clause):
  **189 words**.
- The **"Declaration of generative AI use" section is deleted**
  (author's standing rule 2026-11-01).
- The AAS Section 3.1 keeps its long form (unchanged, as directed).
- Results of record replaced by the no-lightning conditioning outputs
  (`results/rate_ratios_summary.json`, `rate_ratios_by_config.csv`,
  `monthly_series_all.csv`); fact sheet regenerated without the GLM
  section.
- `AAS_COMPLIANCE.md`: current-state lines updated (title, headline
  results without the lightning bullet, abstract 189 words, main text
  4,572 words including captions and tables, display items 10) and a
  dated rebuild section appended; historical sections stand.

### Figure inventory (7 figures + 3 tables = 10 display items)
1. `fig_map_geography` — **new to this package**: report geography,
   Section 2.3, with NH's Figure 1 caption and a "(Figure 1)" pointer
   added to the Section 3.2 records sentence.
2. `fig_map_poles` — **new**: pole geography, Section 3.1 after
   Table 2, with pointer sentence.
3. `fig_s1_count_heatmaps` (was Figure 1). 4. `fig_s2_variance` (was
   Figure 2). 5. `fig_h1_forest` (was Figure 3) — regenerated without
   lightning. 6. `fig_h2_envelope` (was Figure 4) — regenerated, three
   panels. 7. `fig_h3_series` (was Figure 5) — regenerated, three
   panels. All in-text references renumbered.
- The envelope and series figures use the separated suptitle/legend
  layout already established in the NH package (the compact layout
  collided the legend with the title at three panels).
- **Figures 3 and 4 label fix:** the AAS copies of the count heatmaps
  and variance figure still carried raw variable names on their axes
  (`radius_deg`, `dist`, `higher_order`, `water_balance`), a defect
  under the author's 2026-11-01 figure standard. They now carry the
  label-corrected renders the NH package already used (steps 24/25
  there); the data are identical. Flagged here because it goes one
  step beyond the directed figure list.

### Verification (all gates pass)
- `code/08_citation_closure.py`: **PASS**, 37 cited / 37 listed.
- `code/11_verify_numbers.py`: **PASS** — 318 literals checked; the
  only unmatched literals are two structural ones, not results:
  "1.00" (the 1.00-inch severe-hail criterion in Section 3.2) and "7"
  (the renumbered Figure 7 references). The pole-map counts (43/42/3)
  were added to the trace corpus from the rebuild run.
- Preflight (profile nick) on manuscript and cover letter: **0
  errors**, text identical on format fixes; caption keep-with-next
  re-applied after the fix pass (10 captions). Em dashes 0; black
  text only; no themeColor in content; creator metadata per the
  standing rule; the AI declaration is absent.
- Render: `manuscript_aas.pdf` regenerated from the formatted DOCX
  (19 pages); every figure page (5, 7, 8, 9, 10, 12, 13) visually
  inspected — clean after the two layout fixes above.

## Filing

### Drive — Natural Hazards folder `1cpdPXhSfWNm7WMawdxYRRGMFvVjYTIX1`
All updated in place via files update and size-verified against the
local files (bytes): manuscript_nh.docx `1gMFg57Ngwe8Q3SmwEolKwqzmAIsOnDWE`
1,350,822 (the preflight-formatted build); manuscript_nh.md
`12gRMX7H4BXrgbbwgSnzgGtIDjAPJL6Mi` 29,103; references_nh.bib
`1GrPuXlTTG01yZVYHCmK9sIqZjvsTYe7v` 12,047; cover_letter_nh.docx
`15tdRY1vxEUQM8sZGyrPj8ORuE2lS5yhL` 37,583; cover_letter_nh.md
`1SmyOBIAn5bPpEzG3jgwwUqzGRU_FvCud` 2,833;
supplementary_information_nh.docx `11exLynyxVLXRHOteRpIHxv7BIMV8-JWG`
37,746; supplementary_information_nh.md
`1pf5A5O8hNijtXYGhBhxggjq45UUIxoR-` 1,708; fig_h1_forest.png
`1Q9YjXhDjGMJIir4QyDfl_Ir-l4bC6pcE` 124,091; fig_h2_envelope.png
`1LEoz9FQEhD_MuBtLhOEvJzD3pp29I3cZ` 164,215; fig_h2_envelope.pdf
`1Kk3m7yjW9Zf8_2Z5zTm9baKzQUePnC7z` 19,471; fig_h3_series.png
`1FkRWEChwdwHh_20f6FH74H0yAjkGdRMk` 394,682; fig_map_geography.png
`1oWl1BhdlTZfXghiLp7TJujDIOVssgBTp` 245,705; fig_map_geography.pdf
`1C3bCV1WE236NZ-sLI1GjGDr6_BykJY9c` 133,635; archive_nh_code.zip
`1q1aucZZUAujRcAK55e7mZ7-ZbmvelGrI` 492,419 (rebuilt from the updated
repository staging tree, 102 entries). Created: fig_map_poles.png
`1xf-psMBgZ_BoZGwZXZZhQP5AlQr7AsGM` 273,387; fig_map_poles.pdf
`10CU13ukX1TQ4quTg0losBNAH2JOtWS2X` 953,209; this report.

### Drive — AAS folder `1xgRoFBd0b5LJsfD1qvaHMFNok8J56wui`
Updated in place and size-verified: manuscript_aas.docx
`1FAyBY-sIu-bGx7g4yAre8sg7AuYua3y4` 1,347,976 (formatted build);
manuscript_aas.pdf `1f9ZeHHENJhlP00pthdiyeeB4wSKap8Ow` 1,431,854;
manuscript_aas.md `1kyoGTFL_HmKS8emuSSBwsRkTfeJKcDtq` 29,159;
cover_letter.docx `1Fucv_qy5y4qsDNTyfWiLKDB-ep9juqJF` 37,525;
cover_letter.pdf `1T8iHTwvKZBnLUL1fUCjIZq35KGkaAaN6` 21,936;
references_aas.bib `14AeK7lclFHhpXCDycIkfCnmiSX87L_jD` 12,132;
AAS_COMPLIANCE.md `1KzEzeDe2gUvPHcwaZFHLnyRZXzZGxsUs` 28,583;
rate_ratios_summary.json `1gngEA-HFvio5vx-kU3-hUytXrlKIfAxj` 5,202;
fact_sheet.txt `10qnUhYeTgt2Jt60_kIEao2N2OzwWYXcQ` 2,079;
preflight_manuscript.log `18pk2gsnBSMsz_0sU6pKimtbCDTlos1IU` 7,453;
preflight_cover_letter.log `1_3WYomp6MHNxypxNwVUoXwVAn6K93JuD` 942.
In the `code` subfolder: 07_figures.py `1DfpKQbnJmLzsOdv4g4Et3Fa4NKCypWVo`
7,695; 09_build_docx.py `1zYAijdH87RVXE9ZtmxXYTu-6KrG21KuY` 12,680;
10_fact_sheet.py `1oK98TbvE1dC9WpZERqfvMOE9-gxw8VxC` 3,135;
11_verify_numbers.py `1W7vi5qCbGNoPrR9CP9OFHlV_yOpZPny7` 4,111;
manuscript_aas.md `1K7DLxP9SV7QmsNj1HdntnDCFWbIILfJl` 29,159;
references_aas.bib `133rON1mhFNwO-vPwqOxUN-EG3n19B1Qs` 12,132.

### START HERE index (`1VBVzxR8V9J6CL__WEiRfhv9_0ypGqPj2`)
The AAS entry now carries the rebuilt title and an accurate status
(the 2026-10-28 AAS submission, AAS-2026-0874, was desk-rejected
2026-10-31; the package is retained, not a live submission), and a
new entry 8 records the Natural Hazards package, its folder, and its
ready-for-the-author state.

### GitHub — Nsokol44/cdpe-hazards: PENDING the author's approval card
The sync is fully staged but the push did not complete: the
push-files call's session ended while awaiting the write approval,
and a read-back confirms the new files are not yet in the repository.
Staging tree: `/tmp/cdpe_repo` (pycache purged); paths file:
`/tmp/push_paths.bin` (18 paths: the two manuscripts' sources, bib,
cover letter, supplement, edited build/verify scripts, the new
06b conditioning script, the SPEIbase rebuild script, step 28 map
builder, the three no-lightning results files, the baseline pole
table, and the README rebuild note). Command to complete it:
`github push-files --owner Nsokol44 --repo cdpe-hazards --branch main
--message "Rebuild 2026-11-02: remove the lightning (GLM) arm; add
pole-geography Figure 2" --source-dir /tmp/cdpe_repo --paths-file
/tmp/push_paths.bin`. No workaround was attempted.

## Flags for the author (not changed, per "nothing else changes")
1. **AAS Table 2** still carries the "at most 189 / at most 0.88"
   cells. The NH version of the same table carries the recomputed
   exact values (189, 0.88). One-word fix on the author's go.
2. **Limitations wording (both packages):** the first limitation now
   sits two pages from a pole-location figure yet says pole-relative
   conditioning "requires the pole locations, which the saved month
   sets used here do not carry". The rebuild run did save pole
   locations for the baseline months (that is what Figure 2 plots);
   the sentence describes the hazards arm's saved month sets. Left
   verbatim; the author may want it revisited.
3. **Data availability statements (both packages)** still list
   GOES-16 GLM among the public source datasets. The brief held these
   statements unchanged, so they stand; the acknowledgments lists no
   longer thank GLM.
4. **SPEIBASE_REBUILD_REPORT.md rounding slip:** its split-era table
   prints hail ≥1 in, 1996–2023 as 1.20; the run JSON gives
   1.1949885…, which formats to 1.19 — the value both manuscripts and
   the fact sheet carry. The manuscripts are correct; the rebuild
   report's table cell is the slip.
5. **Supplement builder:** `code/23_build_nh_supplement.py` cannot
   build the current supplement source (it expects YAML frontmatter
   the author's R3 source does not carry). The filed supplement is the
   author's R3 DOCX with the single title-string edit, as in previous
   rounds.
6. **Drive cover letters:** the previous Drive copies differed from
   the local builds only in signature-block line breaks (body text
   identical, verified). The filed copies are the new local builds, as
   in previous rounds.

## Corrections addendum — 2026-11-02 (flags 1–4 closed)

A factual-consistency pass closing Flags 1–4 above, under the
author's standing rules (exact counts in tables; a known-wrong
statement is chased, not left). Nothing else was changed; the
extracted-text diffs against the pre-pass files show only the four
corrections below.

1. **AAS Table 2 (Flag 1).** The bounded cells are replaced with the
   exact recomputed values the NH table carries.
   Before: `| SPEI-1, theta = 1.0, r = 3 degrees | 214 | at most 189 | at most 0.88 |`
   After: `| SPEI-1, theta = 1.0, r = 3 degrees | 214 | 189 | 0.88 |`
2. **Limitations wording, both manuscripts (Flag 2).** The
   sentence's referent is this paper's own saved month sets, and it
   was false as written: the pole locations have been recovered.
   Before: "Pole-relative conditioning is the natural next step and
   requires the pole locations, which the saved month sets used here
   do not carry."
   After: "Pole-relative conditioning is the natural next step and
   requires the pole locations. The saved month sets used here do
   not carry them, so we recovered them by re-running the frozen
   detector, which reproduced the archived month sets exactly
   across all 27 scenarios, and Figure 2 plots the recovered
   locations for the baseline months."
   (SPEIBASE_REBUILD_REPORT.md §B: the rerun saved per-month pole
   lat/lon for every scenario and all 27 SPEI scenario month sets
   match run_armA_2026-10-05 exactly, Jaccard 1.000.)
3. **Data availability, both manuscripts (Flag 3).** The GOES-16
   GLM entry is removed from the data-source list, as the lightning
   arm is dropped. The GitHub deposit sentence and the rest of each
   statement are unchanged.
   Before (both): "…Storm Events from NOAA NCEI, and GOES-16 GLM
   from the NOAA Open Data program on AWS."
   After (both): "…Storm Events from NOAA NCEI."
4. **SPEIBASE_REBUILD_REPORT.md (Flag 4).** Split-era table, hail
   ≥ 1 in, 1996–2023 cell: 1.20 → **1.19**, the run JSON value
   (1.1949885…; `C_conditioning/rate_ratios_summary.json`). The
   manuscripts already carried 1.19 and are unchanged on this point.

### Re-verification
- Both DOCXs rebuilt from the package builders; preflight (profile
  nick) on both manuscripts: **0 errors**, "text identical to
  original: True" on each fix pass (formatted files checked
  text-identical to the raw builds independently as well); caption
  keep-with-next 10 of 10 in both formatted files.
- NH `code/22_verify_nh.py`: **ALL PASS** (number trace 316
  literals, 0 unmatched; NH–AAS token identities hold at md and
  DOCX level with only the previously itemised explained deltas).
- AAS `code/08_citation_closure.py`: **PASS** (37 cited / 37
  listed). `code/11_verify_numbers.py`: 320 literals, unmatched
  only the two previously explained structural literals ("1.00",
  "7") — the same pass state as the rebuild.
- AAS PDF regenerated from the formatted DOCX (19 pp class render
  via LibreOffice).

### Re-filing (Drive, in place, size-verified against local bytes)
- NH folder `1cpdPXhSfWNm7WMawdxYRRGMFvVjYTIX1`: manuscript_nh.docx
  `1gMFg57Ngwe8Q3SmwEolKwqzmAIsOnDWE` 1,350,870 (formatted build);
  manuscript_nh.md `12gRMX7H4BXrgbbwgSnzgGtIDjAPJL6Mi` 29,244;
  SPEIBASE_REBUILD_REPORT.md filed new as
  `13Wu4cG5p5IVy2X8uc68IVpwyydhu6Nuw` 12,644 (it had no prior copy
  in this folder); this report, re-filed in the same pass.
- AAS folder `1xgRoFBd0b5LJsfD1qvaHMFNok8J56wui`:
  manuscript_aas.docx `1FAyBY-sIu-bGx7g4yAre8sg7AuYua3y4`
  1,348,015 (formatted build); manuscript_aas.pdf
  `1f9ZeHHENJhlP00pthdiyeeB4wSKap8Ow` 1,431,729; manuscript_aas.md
  `1kyoGTFL_HmKS8emuSSBwsRkTfeJKcDtq` 29,284 and its `code`-subfolder
  copy `1K7DLxP9SV7QmsNj1HdntnDCFWbIILfJl` 29,284;
  preflight_manuscript.log `18pk2gsnBSMsz_0sU6pKimtbCDTlos1IU`
  7,453 (this pass's run).
- Flags 5–6 stand as recorded. The staged GitHub push
  (/tmp/cdpe_repo) was not touched; it remains pending the author's
  approval card.
