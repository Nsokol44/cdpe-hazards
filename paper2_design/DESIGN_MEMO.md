# DESIGN MEMO — CDPE physical-dynamics paper (Advances in Atmospheric Sciences special issue)

**Working title:** The physical environments of concurrent drought-pluvial regimes:
matched environmental characteristics of tornadoes, hail, heat waves, and lightning
in CDPE and non-CDPE months over the contiguous United States.

**Status:** Stage 1 (design) complete, 2026-11-01. Stage 2 (data build) is gated on
the reanalysis decision in Section 10: the specified source (ERA5) is not reachable
at production scale from this environment without the author's Copernicus CDS
credentials; a fully verified fallback (NOAA NARR) is ready. Evidence and options:
ACCESS_AUDIT.md. Nothing in Sections 1–9 depends on that choice except the sampling
cadence noted in Section 6.

**Venue:** Advances in Atmospheric Sciences, special issue "Compound Climate
Extremes: Processes, Trends, and Impacts". Verified live on the journal's Springer
collections page, 2026-11-01: submission status OPEN, deadline 15 January 2027.
Submission via Manuscript Central, manuscript type "Special issue: Compound
Extremes", subscription route (no APC on that route; the optional open-access
charge is the author's decision at submission, as recorded for the sibling).

**Relations (fencing, as in the sibling design lock).** Parent: Sokol, "A
Computational Algorithm to Identify Concurrent Drought-Precipitation Events"
(national catalogue, 52 CDPE months), under review at Physical Geography; credited
with the detector and catalogue, whose event characteristics are not restated here.
Sibling 1: the Southeastern regional study (under revision at Southeastern
Geographer); no regional claims imported. Sibling 2: the definition-sensitivity and
hazard-occurrence paper (AAS-2026-0874; retargeted to Natural Hazards), which asked
whether hazard OCCURRENCE rates differ in CDPE months and found no robust
association for any hazard. This paper asks the orthogonal physical question: given
that an event of a stated magnitude occurred, did it occur in a different
environment when the month was a CDPE month? Occurrence results from Sibling 2 are
cited as motivation only, never restated as findings here.

---

## 1. Question and contribution

Do severe-weather events that occur during concurrent drought-pluvial event (CDPE)
regime months take place in systematically different physical environments than
comparable events (same magnitude, same calendar month, same region) in non-CDPE
months? The contribution is a magnitude-matched environmental comparison for four
hazards under a compound-regime label, with the comparison repeated across the CDPE
definition envelope so that any claimed difference is shown not to be an artefact of
how the regime catalogue was built.

## 2. Regime frame (input, frozen)

- Primary frame: the family baseline configuration of the completed sensitivity
  study, Arm A (SPEI-1, detection threshold 1.5, radius 4 degrees; detector
  f = 0.5, q = 0.10; SPEIbase v2.10): **46 CDPE months, January 1980 to
  December 2023**, staged in the sibling archive at
  `cdpe-hazards-aas/data/raw/cdpe_monthsets/cdpe_monthly_series_armA.csv`
  (manifest in the sibling `data/DATA_MANIFEST.md`). This is the same frame the
  sibling occurrence paper used, so the two papers' statements are commensurable.
- Envelope (sensitivity, headline parameters only): the 23 Arm A configurations
  meeting the sibling inclusion rule (at least 10 CDPE months in 1980–2023;
  at least 3 in the 2018–2023 lightning window, 20 configurations there).
- Domain: 25–50 N, 125–66 W (the detector's CONUS bounding domain), as in the
  sibling. Statements are about the domain, not United States territory as such.

## 3. Event sets (inputs, frozen; census in results/event_frame_counts.json)

All event data are already archived locally by the sibling build; nothing is
re-fetched (sibling DATA_MANIFEST.md is the provenance record).

1. **Tornadoes** (NOAA/NCEI Storm Events yearly details files). Primary set:
   events with reported begin coordinates inside the domain and a rated scale
   (F/EF0–F5; EFU and missing ratings excluded and counted). 53,457 events,
   of which **6,168 fall in baseline CDPE months** (667 distinct days).
   Location rule deviation from the sibling, deliberate: the sibling's monthly
   counts admitted county-centroid fallback locations (112 tornadoes); point
   environments require reported coordinates, so the primary set excludes
   centroid-located events and a sensitivity run reports the all-location frame
   (54,607 events; 6,280 in CDPE months).
2. **Hail** (Storm Events). Primary set: reports with magnitude at least
   1.00 inch (the fixed severe criterion, as in the sibling) and reported
   coordinates: 219,282 reports, **25,803 in CDPE months** (728 distinct days).
   Magnitude bins for matching: 1.00–1.24, 1.25–1.74, 1.75–2.49, 2.50+ inches
   (CDPE-month counts 13,405 / 3,817 / 7,973 / 1,710). Secondary stratum:
   reports of at least 2.00 inches (2,733 in CDPE months, all locations),
   which carry less reporting-effort noise. Reports are treated as events and
   day-clustered in inference (Section 7), since one storm yields many reports.
3. **Heat waves** (gridMET daily Tmax, sibling step-05 definition replicated
   exactly and verified: binned 0.5 degree grid, 3,608 land cells, exact
   calendar-day 98th percentile over 1981–2010 in a 31-day centred window, a
   heat-wave day is a day belonging to a run of at least 3 such days; this
   build's census reproduces the sibling's total of 475,233 cell-days
   exactly). Event unit: the heat-wave **cell-day**: 475,233 cell-days in
   total, **34,682 in CDPE months**, on 579 distinct CDPE-month days
   (7,504 distinct heat-wave days overall). Each cell-day carries its
   exceedance intensity (Tmax minus the cell's calendar-day threshold,
   from gridMET).
4. **Lightning** (GOES-16 GLM LCFA, sibling sampled frame: first 20-second
   file of every hour on days of month congruent to 1 mod 3, March 2018 to
   December 2023, 70 valid months; census reproduces the sibling's sampled
   total of 849,826 flashes in the domain exactly). Event unit: the sampled
   flash (centroid and energy from the archived LCFA files). **89,403 sampled
   flashes fall in the 4 CDPE months inside the window** (2020-05, 2021-07,
   2022-04, 2023-07; 43 sampled days). Labelled exploratory throughout, as in
   the sibling, because the treated frame is four months.

## 4. Estimands

For hazard h, environmental parameter p, and CDPE configuration c, the primary
estimand is the **matched mean environmental difference**

  Δ_hp(c) = Σ_cells w_cell · ( ȳ_case,cell − ȳ_control,cell ),

the case-minus-control mean of p over coarsened-exact-matching cells (Section 5),
weighted to the case distribution, reported (i) in native units and (ii)
standardised by the pooled within-cell standard deviation. Secondary estimands:
matched median difference and interquartile shift of p, and the difference in
the share of events exceeding published operational thresholds of p where such
thresholds exist (for example 0–6 km shear of 18 m s−1 for supercell
environments), each pre-specified per hazard in the analysis codebook before
extraction begins. The estimand is associational: it compares environments of
events that occurred under two monthly regime labels at fixed reported
magnitude, season, and region. It is not a causal effect of the regime on the
environment, and the manuscript will say so.

## 5. Matching design

- Cases: events in CDPE months of configuration c. Controls: events in
  non-CDPE months of the same window.
- Coarsened exact matching on three factors, then case-distribution weighting
  (CEM weights); cells with no case or no control contribute nothing and are
  counted, as are unmatched cases (match rate reported per hazard):
  * magnitude: tornado EF class (0, 1, 2, 3, 4–5 combined); hail size bin
    (Section 3); heat-wave exceedance bin (0–1, 1–2, 2–3, 3+ degrees C) with
    the additional exact factor **same grid cell** (a cell's CDPE-month
    heat-wave days are compared with the same cell's non-CDPE-month
    heat-wave days, which holds terrain and local climatology fixed by
    construction); lightning log-energy tercile computed within
    calendar month and region.
  * calendar month (exact, 1–12): absorbs seasonality and month length.
  * region (storms and lightning): six state-group regions by event state
    FIPS — Northeast and Mid-Atlantic (ME NH VT MA RI CT NY NJ PA DE MD DC
    VA WV); Southeast (NC SC GA FL AL MS TN KY); Midwest and Great Lakes
    (OH IN IL MI WI MN IA MO); Southern Plains (TX OK KS AR LA); Northern
    Plains and Mountain West (NE SD ND MT WY CO UT ID NV); West Coast and
    Southwest (CA OR WA AZ NM). Lightning flashes take the region of the
    nearest county centroid in the Census gazetteer (tolerance 1.5 degrees;
    unassigned flashes are excluded and counted).
- Pre-specified sensitivities: (a) inverse-probability weighting on the same
  three factors in place of CEM; (b) the sibling's calendar-month-stratified
  unmatched difference (a coarse check, reported in supplement); (c) era
  split 1980–1999 vs 2000–2023 for tornado and hail (reporting
  inhomogeneity); (d) configuration envelope for headline parameters
  (Section 2); (e) tornado all-location frame (Section 3, item 1).

## 6. Environment sampling and parameters

Environments are sampled at the reanalysis grid point nearest the event
(bilinear interpolation as a sensitivity), at the analysis time nearest the
event begin time (ERA5 route: nearest hour; NARR route: nearest 3-hourly
step; the choice is fixed by the Section 10 decision and stated in the
methods). Profiles are taken on the source's pressure levels; derived
quantities use one documented code path for both sources so the parameter
definitions cannot drift with the data decision:

- Bulk shear 0–6 km and 0–1 km: magnitude of the vector difference between
  the wind interpolated to 6 km (1 km) above ground level and the 10 m wind.
- Storm-relative helicity 0–1 km and 0–3 km: Bunkers et al. (2000)
  right-moving storm motion, integrated on the native levels.
- Mixed-layer CAPE and CIN: lowest-100-hPa mass-weighted mean parcel,
  virtual-temperature correction, trapezoidal integration; LCL from the
  parcel's origin properties (Bolton 1980). (ERA5's archived CAPE and
  NARR's archived CAPE are extracted as cross-checks, never as primaries,
  so one parcel definition governs every event and era.)
- Relative vorticity at 850 hPa (primary, the author's example quantity)
  and 500 hPa: ERA5 archived field on the ERA5 route; centred differences
  of the wind grids on the NARR route.
- Lapse rates 700–500 hPa (primary) and 850–500 hPa.
- Moisture: precipitable water integrated from the profile (archived
  total-column water as cross-check), 850 hPa dewpoint, 2 m dewpoint.
- Heights: freezing-level height and wet-bulb-zero height from the profile
  (hail), 500 hPa geopotential height and its anomaly against the
  1991–2020 calendar-day climatology of the same reanalysis (heat waves).

Primary parameter sets (six per hazard, fixed before extraction):
- Tornado: SRH 0–1 km; 0–6 km bulk shear; MLCAPE; 850 hPa vorticity;
  700–500 hPa lapse rate; LCL height.
- Hail: MLCAPE; 0–6 km bulk shear; 700–500 hPa lapse rate; freezing-level
  height; precipitable water; MLCIN.
- Heat waves (sampled at 18:00 UTC on the cell-day; sensitivity: mean of
  the day's synoptic steps): 500 hPa height anomaly; 850 hPa temperature;
  700 hPa vertical velocity (subsidence); precipitable water; surface soil
  moisture (top layer); 2 m dewpoint depression.
- Lightning: MLCAPE; MLCIN; precipitable water; 700–500 hPa lapse rate;
  warm-cloud depth (freezing level minus LCL); 0–6 km bulk shear.

Build-time QA gate (reported in the build report, not the paper): the
extracted CONUS tornado-environment medians must fall inside the ranges
published by independent proximity-sounding climatologies (Brooks et al.
2003; Taszarek et al. 2020) before any matched difference is computed;
failure stops the build for diagnosis.

## 7. Inference and multiplicity

- Cluster bootstrap resampling **event days** with replacement (B = 2000,
  seed 20261101, mirroring the family's fixed-seed bootstrap practice),
  recomputing Δ within each replicate; percentile 95% intervals. Days are
  the dependence unit because reports cluster in outbreaks. Sensitivity:
  year-block bootstrap for headline parameters.
- Estimation first: every primary parameter reports Δ with its interval,
  significant or not. Benjamini–Hochberg within each hazard's six primary
  parameters disciplines any "detected difference" language.
- Language gates (family pattern, fixed in advance). G1 completeness: if
  environments are extracted for under 98% of a hazard's primary events,
  that arm is descriptive only and leaves the abstract. G2 robust claim: a
  difference may be called robust only if the baseline interval excludes
  zero AND the point estimate keeps its sign in at least 80% of envelope
  configurations AND its BH q is below 0.05 within hazard; otherwise the
  language is "no consistent difference" or "configuration-dependent", as
  the numbers dictate. G3 traceability: every number in the manuscript
  must be a value in this project's results files; NaN serialises as null.

## 8. Headline figure (author's requirement; form settled here)

**Figure 2, "Where and when the environments differ."** Four columns (one
per hazard) by two rows. Top row: CONUS maps of the matched difference of
the hazard's flagship parameter (tornado: SRH 0–1 km; hail: MLCAPE; heat
wave: 500 hPa height anomaly; lightning: MLCAPE), computed from matched
event pairs binned on a 1.5 degree grid; bins holding fewer than 10
matched pairs are masked. Bottom row: for the same parameter, a
region-by-calendar-month matrix of matched differences (six regions by
twelve months; cells with fewer than 10 matched pairs masked), which is
the figure's time dimension. One shared diverging colour scale for all
eight panels (ColorBrewer BrBG, colourblind-safe), standardised units
(pooled within-cell standard deviations) so panels are comparable, with
native-unit equivalents in the caption; a single shared legend placed
above the panels; pan
...[truncated 5336 chars]
---

## Amendment 2026-11-01 — reanalysis source: NARR substitution (Option B)

**Decision (author's, 2026-11-01).** The build proceeds on the North American
Regional Reanalysis (NARR), not ERA5. The specified source (ERA5) cannot be
produced from this environment without the author's Copernicus CDS
credentials, which do not exist on this machine; every credential-free ERA5
route was measured and found infeasible or insufficient (ACCESS_AUDIT.md,
2026-11-01: ARCO-ERA5 Zarr global-chunk reads, NCAR AWS daily-file volume
and range-read latency, NCI and UCAR subsetting services unreachable,
era5-pds lacking pressure-level profiles and CAPE, Open-Meteo archive
surface-only). NARR is delivered by the verified NOAA PSL THREDDS OPeNDAP
route (monthly pressure-level files open in ~2 s; full-grid slice ~0.6 s;
29 pressure levels, 3-hourly, 32 km Lambert grid, 1980–2023, CAPE at
monolevel).

**What changes (and only this).** (i) Environment sampling is at the
nearest NARR 3-hourly analysis step instead of the nearest ERA5 hour
(Section 6 cadence). (ii) 850 and 500 hPa relative vorticity is computed
by centred differences of the NARR wind grids instead of taken from an
archived vorticity field. (iii) The 500 hPa height climatology behind the
heat-wave anomaly is the 1991–2020 calendar-day climatology of NARR
itself. (iv) Archived cross-check fields are NARR's (monolevel CAPE and
precipitable water). Estimands, matching, parameter sets, event frames,
inference, multiplicity control, and language gates G1–G3 are unchanged.

**Manuscript disclosure.** The methods section states the substitution
and its reason in one sentence, as specified when the decision was taken.

— Recorded 2026-11-01, at the Stage 2 gate.

---

## Amendment 2026-11-01 (second, later the same day) — ERA5 restored; NARR amendment superseded

**Decision (author's, 2026-11-01, superseding the Option B amendment
above).** The author supplied his Copernicus Climate Data Store (CDS)
credentials later the same day (credentials held in `~/.cdsapirc`,
never copied into this project), and the parent session verified the
CDS route directly: a real ERA5 single-levels request completed
(accepted, running, successful) with a valid NetCDF download, and a
pressure-levels request was accepted under the same key. ERA5 is
therefore back in force exactly as originally designed in Sections
1-9: hourly sampling at the hour nearest the event, ERA5 archived
relative vorticity, the heat-wave 500 hPa height anomaly against
ERA5's own 1991-2020 calendar-day climatology, and ERA5 archived CAPE
and total-column water as cross-checks. The NARR amendment above is
superseded and NARR reverts to fallback-only status; the partial NARR
extraction archived before the reversal (9 storm month units and 43
climatology month units, with its pilot QA gate) stays in the project
as a record and is not used in the ERA5 analysis. ACCESS_AUDIT.md
remains the evidence record for both decisions. The manuscript
describes ERA5 as the source in the normal way; no substitution
sentence is needed. Estimands, matching, parameter sets, event
frames, inference, multiplicity control, and language gates G1-G3 are
unchanged, as they were under both amendments.

- Recorded 2026-11-01, at the Stage 2 restart under the restored
  ERA5 design.

---

## Amendment 2026-11-02 (third review installment + two-paper split)

**Status and scope of this amendment.** Recorded 2026-11-02. This amendment folds into this design the third review installment, as adopted by the author, and the author's decision to split one paper into two. It adds to the frozen design above and, where it conflicts with the frozen body on frame years, catalog version, regime timing, event restriction, or analysis order, this amendment governs for all future work on this paper. No other part of the frozen body is changed. This amendment authorizes no new analysis, no manuscript writing, and no dataset substitution. Execution remains gated as recorded in Section A9 below.

### A1. Venue settled, and the two papers kept distinct

The venue for this paper is settled. This paper, Paper 2, targets Advances in Atmospheric Sciences (AAS), special issue "Compound Climate Extremes", with a submission deadline of 15 January 2027. An external review suggested Monthly Weather Review, the Journal of Applied Meteorology and Climatology, and Weather and Climate Extremes as alternative venues for this material. The author considered that suggestion and has settled on AAS for Paper 2. The venue question is closed and is not reopened by this amendment.

Paper 1, the statistical paper that asks the frequency question, goes to Natural Hazards. Paper 2, this paper, is the physical and synoptic paper, and it stays out of Natural Hazards. Paper 1 stays out of AAS. The two papers are kept distinct at every stage. Paper 2 cites Paper 1. The two papers share only the regime catalog described in Section A2. Paper 2 reuses no results from Paper 1, and Paper 1 reuses no results from Paper 2. Neither paper is ever under review at two journals at the same time, and neither paper is submitted to the other paper's journal.

### A2. Shared catalog rule

Paper 2 uses the same aligned, US-anchored catalog as Paper 1. The lineage is the companion Study 1 lineage, the detector and catalog are held in common, and the catalog version of record for both split papers is SPEIbase v2.11. The anchored subset is the subset in which both poles of a CDPE month lie inside the contiguous United States (CONUS). Statements that rest on the anchored subset say so, and statements that rest on the full domain frame say so, and the two are never mixed in one comparison. Paper 2 cites Paper 1 for the catalog and for the frequency findings, states that it shares the catalog and nothing else, and reports no Paper 1 occurrence rates, ratios, or gate outcomes as findings of its own. Where the extended frame in Section A6 reaches back before 1980, it does so by running the same detector, the same lineage, and the same SPEIbase version over the longer record. It is an extension of the shared catalog in time, not a new or different catalog.

### A3. Circularity fix, adopted as the first principle of the design

The circularity problem is named first because it governs everything that follows. SPEI-1 is built from precipitation in the same month it describes, and severe storms produce warm season rain. A regime label built from same-month SPEI-1 can therefore be partly caused by the very events the analysis then conditions on. A same-month comparison would risk reading the rain left behind by the storms as if it were the background state that preceded them.

The fix is structural, and it replaces the same-month regime timing of the frozen design for all severe weather work in this paper. The Paper 2 regime is defined from the antecedent state only. In the primary definition, the regime for a test month is the regime of the previous month. In the sensitivity definitions, the regime is carried by antecedent SPEI-3 or antecedent SPEI-6, computed over months that end before the test month begins. Severe event days are then tested in the month that follows the regime month. No precipitation, no event, and no environmental field from the test month enters the definition of the label that the test month is judged against. The heat wave arm follows the same rule, with its regime taken from the antecedent month and its cell days counted in the following month. Any same-month result computed during development is a diagnostic only, is labeled as such, and carries no claim in the paper.

### A4. The 2 by 2 design on top of the lagged definition

The core design is a 2 by 2, and it sits on top of the lagged definition in Section A3. One factor is the day type, event days against non-event days. The other factor is the antecedent regime, lagged CDPE months against non-CDPE months, where non-CDPE means a month whose antecedent month carried no CDPE label under the same definition. The four cells are event days in lagged CDPE months, event days in non-CDPE months, non-event days in lagged CDPE months, and non-event days in non-CDPE months. The contrast between the two non-event cells measures the background state shift that the antecedent regime carries into the test month, in the absence of events. The contrast between the two event cells measures how event environments differ by antecedent regime. The difference between those two contrasts is the quantity that separates a background state shift from an event environment shift, and it is reported for every headline parameter, in native units and in standardized units.

Three additions govern inference in the 2 by 2. First, composites are tested by permutation. Regime labels are permuted at the month level, within the matching strata below, the full composite is recomputed for each permutation, and a field significance correction is applied across the composite field so that no single grid point, level, or parameter is called significant on an uncorrected test. Second, controls are matched on calendar month, on era, and on ENSO phase, in addition to the magnitude and region matching already in the frozen design. Era is a fixed stratification factor, not a covariate added after the fact, because reporting practice and reanalysis inputs both change over the long frame in Section A6. Third, uncertainty is estimated by block bootstrap at the level of the CDPE month. The resampling unit is the whole antecedent regime month together with its test month, so events that cluster on the same day, in the same outbreak, and in the same regime episode are resampled together and are never treated as independent draws.

For heat waves, the 2 by 2 is read through two named diagnostics rather than through event counts. The first is ridge amplitude, the strength of the mid-tropospheric ridge over the affected region in the test month. The second is soil moisture coupling, the relation between antecedent soil moisture at the dry pole and the temperature and humidity environment of heat wave cell days in the following month. Both diagnostics are computed for all four cells, so a heat wave difference can be attributed to the ridge, to the land surface state, to both, or to neither, on evidence rather than by assertion.

### A5. Mechanism, not only composites

Composites alone do not carry this paper. A composite difference shows that environments differ, and it does not show which ingredient carries the difference or where the air came from. The full design therefore requires at least one quantitative attribution step, and three are specified here, of which the first is mandatory for any headline severe weather claim.

First, index decomposition. Differences in the Significant Tornado Parameter (STP), the Supercell Composite Parameter (SCP), and the Significant Hail Parameter (SHIP) between lagged CDPE and non-CDPE event environments are decomposed into the contributions of their ingredients. The ingredients named for the decomposition are convective available potential energy (CAPE), bulk shear, storm relative helicity (SRH), and lifted condensation level (LCL) height, with convective inhibition included where an index uses it. The method is one at a time substitution. Each ingredient in the CDPE composite is replaced in turn by its non-CDPE composite value while the remaining ingredients are held at their CDPE values, the index is recomputed, and the change is recorded as that ingredient's contribution. The sum of the contributions is checked against the full index difference, any residual is reported, and the ordering is reversed as a sensitivity so that no contribution depends on the order of substitution.

Second, source region tracing. The paper traces where the air in the differing environments came from, by Lagrangian back trajectories from the event environments, or by a moisture budget over the pole regions and the event regions, with the choice between those two routes fixed and recorded before extraction begins. Two source questions are pre-specified. One asks whether air over the dry pole and the event region carries the thermodynamic signature of the Mexican Plateau and the Southwest, in the form of an elevated mixed layer with warm, dry air aloft over cooler, moist low level air. The other asks whether air arriving at wet pole event environments carries enhanced low level moisture transport along the route into the pole region. A trajectory or budget result that answers neither question is reported as a null mechanism result, not rewritten into a weaker claim.

Third, soil moisture coupling at the dry pole. Antecedent soil moisture in the dry pole region is related to the test month environment at and downwind of the pole, through evaporative fraction or a direct soil moisture and surface flux diagnostic, through CAPE and convective inhibition, through LCL height, and through heat wave ridge amplitude as defined in Section A4. The diagnostic is computed on the lagged frame only, so the land surface state precedes the environment it is said to influence.

### A6. More events, a longer frame, and a cleaner event restriction

The frame is extended to 1950 to 2023. The extension is feasible on inputs, and no input is the limiting factor. ERA5 is available from 1940, and SPEIbase is available from 1901, so a 1950 start sits well inside both records and leaves room for the antecedent SPEI-3 and SPEI-6 windows that Section A3 requires at the start of the frame. The shared catalog of Section A2 is extended over this frame with the same detector and the same version.

To limit contamination from changes in reporting over a 74 year frame, the severe weather event sets are restricted to significant severe events only. Tornadoes are restricted to EF2 or stronger, with F2 or stronger standing as the equivalent rating before the Enhanced Fujita scale. Hail is restricted to reports of at least 2.00 inches. Weaker events are excluded from the primary frame, because their counts track reporting effort, spotter coverage, and population far more strongly than the counts of significant events do. Reported coordinates are required, as in the frozen design, because point environments cannot be sampled for an event whose location is a county centroid. Inference throughout the extended design is cluster aware. The block bootstrap by CDPE month in Section A4, the day clustering already in the frozen design, and field significance corrections on every composite field all apply to the extended frame without exception, and no result on the long frame is reported with an independence assumption across events, days, or grid points.

### A7. One pre-committed headline hypothesis

The paper carries exactly one pre-committed headline hypothesis, recorded here before any pilot extraction, and stated verbatim as follows.

"dry poles over the Mexican Plateau and Southwest feed an elevated mixed layer that strengthens the cap and lapse rates, while wet poles sit where low-level moisture transport is enhanced"

That sentence is the registered hypothesis of this paper. The pilot in Section A9 and the full design above are built to test it, in that form, with the dry pole and wet pole roles, the elevated mixed layer, the cap, the lapse rates, and the low level moisture transport all read as named, testable parts of one claim. No second headline hypothesis is added, and no part of this one is quietly weakened, broadened, or replaced after the data are seen. The consequence is stated plainly. If the data do not show this, the paper has no story. In that case the outcome is the null deliverable defined by the pilot gate in Section A9, reported honestly, and not a search through other parameters, other regions, or other regime definitions for a difference that can be promoted in its place.

### A8. Framing and literature plan for an atmospheric science readership

The paper is framed for atmospheric scientists. Its subject is large scale regimes and the convective environments that occur inside them, and its language is the language of synoptic and mesoscale meteorology, not the language of an index evaluation. The frequency question, the detector performance question, and all occurrence rate material belong to Paper 1 and appear here only as cited motivation.

The literature plan engages three strands, at strand level, and records what each strand contributes to this design. The first strand is the elevated mixed layer literature. It contributes the physical account of how air heated and dried over elevated arid terrain moves out over the Plains, strengthens a capping inversion, steepens mid level lapse rates, and shapes where and when severe convection can occur, and it supplies the expectations that the trajectory work in Section A5 and the hypothesis in Section A7 are tested against. The second strand is the Great Plains low level jet literature. It contributes the account of nocturnal and synoptically driven low level moisture transport from the Gulf of Mexico into the Plains, its diurnal and seasonal structure, and its role in supplying the low level moisture and helicity of severe environments, and it frames the wet pole side of the hypothesis and the moisture transport diagnostics in Section A5. The third strand is the soil moisture and convection feedback literature. It contributes the account of how antecedent land surface wetness or dryness feeds back on boundary layer growth, LCL height, CAPE, convective inhibition, and heat wave amplification, and it frames the dry pole coupling diagnostics in Sections A4 and A5 and the decision to define the regime from the antecedent state in Section A3. No specific citation is added by this amendment. Citations are added only at the writing stage, from sources read and verified at that stage, and no citation already in the frozen memo is altered here.

### A9. Pilot before pipeline, the mandated first execution step, and the data gate

No full pipeline is built first. The mandated first execution step is a pilot, and the pilot carries an explicit go or no-go gate.

Pilot question. Do significant severe event days in lagged CDPE months occur in environments that differ, at field significance, from significant severe event days in non-CDPE months, on the lagged definition of Section A3, over 1950 to 2023.

Pilot products. Composites, on the 2 by 2 frame of Section A4, of STP, SCP, and SHIP at the event time and location, and composite fields of 500 hPa geopotential height (Z500) and CAPE, for significant severe days in lagged CDPE months against matched significant severe days in non-CDPE months. Matching is on calendar month, era, and ENSO phase. Significance is by month level permutation with a field significance correction across each composite field and across the parameter set. Nothing outside this product list is computed in the pilot.

Pilot event lists. Tornado and hail event lists back to 1950 are built from NOAA and NCEI Storm Events, restricted as in Section A6 to tornadoes rated EF2 or stronger, with F2 or stronger before the Enhanced Fujita scale, and hail of at least 2.00 inches, with reported coordinates required and exclusions counted. Antecedent CDPE month sets are built from SPEIbase v2.11 with the shared detector of Section A2, extended to cover antecedent months for the full 1950 to 2023 test frame, in three forms that correspond to Section A3, namely the previous month regime, antecedent SPEI-3, and antecedent SPEI-6. The counted number of distinct significant severe event days, event hours, and antecedent CDPE months from these lists replaces every planning estimate in the volume audit below, and the audit is recomputed and recorded before any reanalysis request is submitted.

Reduced variable list. Pressure level variables are temperature, specific humidity, zonal wind, meridional wind, and geopotential, on 13 levels, namely 1000, 925, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, and 100 hPa. Single level fields are CAPE, mean sea level pressure, 2 m temperature, 2 m dewpoint, 10 m zonal wind, and 10 m meridional wind. Z500 is taken from geopotential at 500 hPa in the pressure level set, and CAPE is taken from the single level field, with mixed layer CAPE, convective inhibition, shear, SRH, and LCL derived from the sampled profiles by the single documented code path already specified in the frozen design. No other variable is requested in the pilot.

Request grouping. Requests are grouped by event time, not by calendar period. One request covers one event day and contains only the hours sampled on that day, only the reduced variable list, only the 13 levels above, and only the CONUS area of the frozen design, namely 25 to 50 N and 125 to 66 W. No full field download of a month, a season, or a year at all hours is made for the pilot, and no request is padded with hours, levels, or variables that no sampled event needs. The first 20 day requests are treated as a measurement batch. Delivered megabytes per event hour and queue time per request are measured on that batch, the volume projection is updated from measurement rather than from the planning rates below, and the pilot pauses for a recorded check if the updated projection exceeds the disk available at that time.

Data volume audit, planning estimate. The audit rests on the project's own measured rate. In results/step02_cds_feasibility.json, a production pressure level subset test over the CONUS area delivered 6.85 megabytes per hour for 6 variables on 27 levels, on a grid of 101 latitudes by 237 longitudes, and the same file records the full frozen design at 83,481 distinct ERA5 hours for the primary frames, which at that rate gives 83,481 times 6.85 megabytes, or about 572,000 megabytes, recorded in that file as a minimum pressure volume of 572 gigabytes at perfect packing. The same file records 124 gigabytes of disk available, and a grouping warning that month level grouping multiplies delivered volume by roughly 3 to 4, which would take that full design to about 1.7 to 2.3 terabytes.

The pilot estimate is built from the design, as follows. Event days are estimated from the project's own census in results/event_frame_counts.json. That census counts, for 1980 to 2023, hail of at least 2.00 inches on 4,556 distinct days, and significant tornadoes, rated EF2 or stronger or F2 or stronger, as 1,054 of the 6,158 rated tornadoes in baseline CDPE months, a share of about 17 percent, which applied to the full tornado frame gives about 9,150 significant tornadoes over 44 years. On the stated planning assumptions of about 3 significant tornadoes per distinct significant tornado day and about 1,500 days shared between the significant tornado days and the significant hail days, the union is about 6,106 distinct significant severe days in 44 years, or about 139 days per year, which over the 74 years from 1950 to 2023 gives a planning figure of about 10,300 distinct significant severe event days. Hours sampled are taken as 3 distinct event hours per event day on average, which gives 10,300 times 3, or 30,900 event hours. The reduced pressure level set carries 5 variables times 13 levels, or 65 variable levels, against 6 times 27, or 162 variable levels, in the measured rate, so the scaled rate is 6.85 times 65 divided by 162, or about 2.75 megabytes per event hour, on the same grid of 101 by 237 points. Pressure level volume is therefore 30,900 times 2.75 megabytes, or about 85 gigabytes. The 6 single level fields add 6 variable levels at 6.85 divided by 162, or about 0.042 megabytes each per event hour, which gives 30,900 times 6 times 0.042 megabytes, or about 8 gigabytes. The pilot total at perfect packing is therefore about 93 gigabytes. That is about one sixth of the 572 gigabytes audited for the full frozen design, and it sits nominally inside the 124 gigabytes of disk recorded in the feasibility file, with no room for grouping waste, which is why the measurement batch above is a gate and not a formality. The sensitivity is recorded with the estimate. At 6 distinct event hours per day instead of 3, the total doubles to about 186 gigabytes and exceeds the recorded disk, and the pilot would then narrow to one representative event hour per event day and region, only with the author's approval recorded in advance. These are planning numbers, labeled as such, and Section A9 above requires them to be replaced by counted numbers before any download begins.

Go or no-go gate. If the pilot composites show no field significant difference between lagged CDPE and non-CDPE significant severe environments, the deliverable is a short note that reports the design, the lagged definition, and the null result, and no full paper is built, no full pipeline is commissioned, and no wider parameter, region, or definition search is run to rescue a headline. If at least one headline parameter or field is field significant in the direction the registered hypothesis requires, the full design in Sections A4 to A6 may proceed, and only then. The gate decision, the numbers it rested on, and the date are recorded in this memo as a further dated amendment before any full build starts.

Data access gate. Execution of the pilot, and of every later stage, remains gated on the author's reanalysis decision. The project's own audit, in results/step02_cds_feasibility.json, found the full ERA5 design infeasible in this environment as audited, at about 572 gigabytes at perfect packing against 124 gigabytes of disk, before grouping waste, and it set out options A to D for the author, namely reverting to the verified NARR fallback, reducing the ERA5 design with explicit approval, providing bulk storage for a managed ERA5 fetch, or pausing the paper. That call is the author's, and it is pending. This amendment makes no choice among those options, substitutes no dataset for another, changes no source named in the frozen design or its earlier amendments, and starts no download, no extraction, and no request. The pilot specification above is written to be complete enough to start on the day that decision is taken, under whichever option the author chooses, with its variable list, grouping rule, and audit method unchanged and its counted volume audit refreshed first.

Recorded 2026-11-02.
