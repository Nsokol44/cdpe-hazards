# Phase 2 Report — Arm B detector tie-breaking fix, masked rerun, and variance decomposition (raw + log1p)

Date: 2026-11-02. Driver: `scripts/run_armB_tiefix.py` (one command; deterministic). Tie-fix detector: `cdpe_sens/detector_tiefix.py` (new module; the frozen `cdpe_sens/author_detector.py` was NOT modified). No manuscript file was edited. Outputs in this directory; provenance in `run_manifest.json`.

## Step 1 — Reproduce before changing (gate)

All masked Arm B fields were recomputed through the package pipeline exactly as the archived masked run (`scripts/run_arm_b_masked.py`) constructed them — datasets via `run_two_arms._arm_b_datasets` (1980–2014), Thornthwaite PET, `compute_spei`, SPEIbase land mask applied to the field (4,443 of 6,069 cells land) — and run through the ORIGINAL detector. **Result: 720/720 scenarios reproduce the archived `results/run_armB_masked_2026-10-05/scenarios.csv` `n_cdpe_months` EXACTLY** (per-scenario comparison in `reproduction_check.csv`). The script aborts before any tie-fix output if this gate fails. Computed masked fields are cached one npz per field configuration under `cache/` (80 configurations) and per-field results checkpointed under `checkpoints/`, so reruns resume.

Archived zero counts were verified first from the archived file itself: **272 of 720 scenarios are zero** (empirical 241, log-logistic 31) — matching the tasking figures.

## Step 2 — The tie rule as implemented

Identical to `classify_month_author` in every rule (same degree-space buffer, NA gate ≤ 0.10, majority ≥ 0.5, via the frozen module's own `buffer_mask_np`/`_qualifies`) except pole selection: all finite cells exactly equal (float ==) to the field minimum (dry) or maximum (wet) are collected; a unique extremum is selected as before; with k > 1 tied cells, one is chosen **uniformly at random** among them. First-index order is never used to break a tie. This single rule covers both tie sources: the empirical Gringorten cap (|z| ≤ 2.146, ~128 tied land cells per pole per month at the baseline) and the log-logistic clip plateau at z = ±4.753 (including F = 0 cells). Randomness: `numpy.random.default_rng` seeded per (pole, month) with the first 8 bytes (little-endian) of SHA-256 over `cdpe-tiefix-v1|BASE_SEED=<seed>|scenario=<key>|month=<t>|pole=<dry|wet>`, where `<key>` is (dataset, timescale, dist, cal_period, water_balance, threshold, min_area_frac, min_cluster_cells, radius_deg) joined by '/'. Default BASE_SEED = 20261102. **Bit-identical rerun assertion on the masked baseline scenario (NARR ts6 log-logistic, θ=1.0, r=4.0): PASSED** (the baseline scenario was detected twice and the CDPE series compared element-wise).

## Step 3 — Rerun: headline counts

Zero-CDPE scenarios: **272 (old) → 58 (new)** of 720. By distribution (of 360 scenarios each):

| dist | zeros old | zeros new |
|---|---|---|
| empirical | 241 | 26 |
| loglogistic | 31 | 32 |

Masked baseline cells (θ = 1.0, r = 4.0°, full calibration, SPEI water balance), old vs new `n_cdpe_months`:

| dataset | timescale | dist | old | new | delta |
|---|---|---|---|---|---|
| ERA5 | 1 | empirical | 18 | 112 | 94 |
| ERA5 | 1 | loglogistic | 79 | 88 | 9 |
| ERA5 | 3 | empirical | 13 | 116 | 103 |
| ERA5 | 3 | loglogistic | 66 | 71 | 5 |
| ERA5 | 6 | empirical | 27 | 109 | 82 |
| ERA5 | 6 | loglogistic | 69 | 74 | 5 |
| ERA5 | 9 | empirical | 15 | 96 | 81 |
| ERA5 | 9 | loglogistic | 47 | 55 | 8 |
| ERA5 | 12 | empirical | 8 | 85 | 77 |
| ERA5 | 12 | loglogistic | 34 | 42 | 8 |
| NARR | 1 | empirical | 9 | 80 | 71 |
| NARR | 1 | loglogistic | 55 | 62 | 7 |
| NARR | 3 | empirical | 3 | 79 | 76 |
| NARR | 3 | loglogistic | 55 | 55 | 0 |
| NARR | 6 | empirical | 6 | 68 | 62 |
| NARR | 6 | loglogistic | 44 | 50 | 6 |
| NARR | 9 | empirical | 4 | 61 | 57 |
| NARR | 9 | loglogistic | 40 | 44 | 4 |
| NARR | 12 | empirical | 2 | 55 | 53 |
| NARR | 12 | loglogistic | 25 | 26 | 1 |

Seed sensitivity, NARR ts6 empirical baseline (θ=1.0, r=4.0, full cal, SPEI), BASE_SEED varied 20261102–20261106 (same derivation, seed value changed):

| BASE_SEED | n_cdpe_months |
|---|---|
| 20261102 | 68 |
| 20261103 | 72 |
| 20261104 | 81 |
| 20261105 | 78 |
| 20261106 | 84 |

Range 68–84, mean 76.6 (old first-occurrence count: 6; the diagnosis's 57–80 range was on its own setup — the audit counterfactual field with masked detection — and is reported here only as context, not as a target). The BASE_SEED=20261102 value equals the scenarios_tiefix count for this scenario by construction (asserted in the driver).

## Step 4 — Variance decomposition (both arms, raw + log1p)

Method: the package's own `variance_decomposition` (`cdpe_sens/sensitivity.py`), first verified against the archives: Arm A max |share diff| = 5.9e-17 over 7 terms; Arm B_masked max |share diff| = 9.04e-17 over 29 terms — both archived `variance_decomposition.csv` files reproduce. Scales: raw `n_cdpe_months`, and log1p counts, log(1 + n) — the standard zero-safe log (chosen because 272/720 old masked scenarios are exactly zero; stated here and in the manifest). `higher_order` is its own category, as in the archived method: it is the remainder after main effects and all two-way interactions (labelled exactly `higher_order`). Full long-form table: `decomposition_tiefix.csv` (arm, version, scale, factor, share).

**Distribution factor share, Arm B masked (the headline correction):**

| scale | dist share OLD | dist share NEW | dist × threshold OLD | dist × threshold NEW |
|---|---|---|---|---|
| raw | 0.188 | 0.005 | 0.167 | 0.012 |
| log1p | 0.345 | 0.000 | 0.052 | 0.005 |

Arm B top terms, raw OLD: threshold 0.319; dist 0.188; dist x threshold 0.167; higher_order 0.072; radius_deg 0.066.
Arm B top terms, raw NEW: threshold 0.641; radius_deg 0.126; threshold x radius_deg 0.097; higher_order 0.028; dataset 0.023.
Arm B top terms, log1p OLD: threshold 0.445; dist 0.345; higher_order 0.052; dist x threshold 0.052; radius_deg 0.046.
Arm B top terms, log1p NEW: threshold 0.786; radius_deg 0.120; higher_order 0.035; dataset 0.018; timescale 0.008.

Arm A (36 scenarios, archived; the tie fix does not apply — SPEIbase/CRU fields are continuous and tie-free, so Arm A has no `dist` factor; its index factor is `index`): index share raw 0.031, log1p 0.035; threshold share raw 0.759, log1p 0.854; higher_order raw 0.001, log1p 0.006.
Arm B higher_order: raw OLD 0.072 → NEW 0.028; log1p OLD 0.052 → NEW 0.035.

## Scenarios changed by more than 50%

Of the 720 scenarios, **141** with old count > 0 changed by more than 50% in relative terms (|delta| / old > 0.5), and **215** moved from 0 to a positive count (relative change undefined, listed in `scenarios_tiefix.csv`). The full >50% list is in `changed_gt50pct.csv` and reproduced below.

| dataset | ts | dist | cal | wb | thr | r | old | new | delta | rel |
|---|---|---|---|---|---|---|---|---|---|---|
| ERA5 | 1 | empirical | full | spei | 1.0 | 3.0 | 40 | 183 | 143 | +3.58 |
| ERA5 | 1 | empirical | full | spi | 1.0 | 3.0 | 31 | 190 | 159 | +5.13 |
| ERA5 | 1 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 28 | 170 | 142 | +5.07 |
| ERA5 | 1 | empirical | 1981-2010 | spi | 1.0 | 3.0 | 24 | 178 | 154 | +6.42 |
| ERA5 | 1 | empirical | full | spei | 1.0 | 4.0 | 18 | 112 | 94 | +5.22 |
| ERA5 | 1 | empirical | full | spi | 1.0 | 4.0 | 11 | 121 | 110 | +10.00 |
| ERA5 | 1 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 13 | 130 | 117 | +9.00 |
| ERA5 | 1 | empirical | 1981-2010 | spi | 1.0 | 4.0 | 9 | 109 | 100 | +11.11 |
| ERA5 | 1 | empirical | full | spei | 1.0 | 5.0 | 10 | 93 | 83 | +8.30 |
| ERA5 | 1 | empirical | full | spi | 1.0 | 5.0 | 1 | 62 | 61 | +61.00 |
| ERA5 | 1 | empirical | 1981-2010 | spei | 1.0 | 5.0 | 8 | 62 | 54 | +6.75 |
| ERA5 | 3 | empirical | full | spei | 1.0 | 3.0 | 34 | 180 | 146 | +4.29 |
| ERA5 | 3 | empirical | full | spei | 1.5 | 3.0 | 1 | 34 | 33 | +33.00 |
| ERA5 | 3 | empirical | full | spi | 1.0 | 3.0 | 38 | 210 | 172 | +4.53 |
| ERA5 | 3 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 22 | 158 | 136 | +6.18 |
| ERA5 | 3 | empirical | 1981-2010 | spi | 1.0 | 3.0 | 32 | 211 | 179 | +5.59 |
| ERA5 | 3 | empirical | full | spei | 1.0 | 4.0 | 13 | 116 | 103 | +7.92 |
| ERA5 | 3 | empirical | full | spei | 1.5 | 4.0 | 1 | 15 | 14 | +14.00 |
| ERA5 | 3 | empirical | full | spi | 1.0 | 4.0 | 11 | 126 | 115 | +10.45 |
| ERA5 | 3 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 8 | 95 | 87 | +10.88 |
| ERA5 | 3 | empirical | 1981-2010 | spi | 1.0 | 4.0 | 11 | 108 | 97 | +8.82 |
| ERA5 | 3 | empirical | full | spei | 1.0 | 5.0 | 4 | 71 | 67 | +16.75 |
| ERA5 | 3 | empirical | full | spei | 1.5 | 5.0 | 1 | 6 | 5 | +5.00 |
| ERA5 | 3 | empirical | full | spi | 1.0 | 5.0 | 7 | 74 | 67 | +9.57 |
| ERA5 | 3 | empirical | 1981-2010 | spei | 1.0 | 5.0 | 3 | 68 | 65 | +21.67 |
| ERA5 | 3 | empirical | 1981-2010 | spi | 1.0 | 5.0 | 5 | 70 | 65 | +13.00 |
| ERA5 | 6 | empirical | full | spei | 1.0 | 3.0 | 41 | 167 | 126 | +3.07 |
| ERA5 | 6 | empirical | full | spi | 1.0 | 3.0 | 39 | 178 | 139 | +3.56 |
| ERA5 | 6 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 38 | 161 | 123 | +3.24 |
| ERA5 | 6 | empirical | 1981-2010 | spi | 1.0 | 3.0 | 34 | 182 | 148 | +4.35 |
| ERA5 | 6 | empirical | full | spei | 1.0 | 4.0 | 27 | 109 | 82 | +3.04 |
| ERA5 | 6 | empirical | full | spi | 1.0 | 4.0 | 14 | 115 | 101 | +7.21 |
| ERA5 | 6 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 19 | 108 | 89 | +4.68 |
| ERA5 | 6 | empirical | 1981-2010 | spi | 1.0 | 4.0 | 12 | 119 | 107 | +8.92 |
| ERA5 | 6 | empirical | full | spei | 1.0 | 5.0 | 12 | 61 | 49 | +4.08 |
| ERA5 | 6 | empirical | full | spi | 1.0 | 5.0 | 4 | 58 | 54 | +13.50 |
| ERA5 | 6 | empirical | 1981-2010 | spei | 1.0 | 5.0 | 8 | 75 | 67 | +8.38 |
| ERA5 | 6 | empirical | 1981-2010 | spi | 1.0 | 5.0 | 4 | 69 | 65 | +16.25 |
| ERA5 | 9 | empirical | full | spei | 1.0 | 3.0 | 30 | 148 | 118 | +3.93 |
| ERA5 | 9 | empirical | full | spei | 1.5 | 3.0 | 1 | 30 | 29 | +29.00 |
| ERA5 | 9 | empirical | full | spi | 1.0 | 3.0 | 37 | 162 | 125 | +3.38 |
| ERA5 | 9 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 31 | 136 | 105 | +3.39 |
| ERA5 | 9 | empirical | 1981-2010 | spei | 1.5 | 3.0 | 1 | 46 | 45 | +45.00 |
| ERA5 | 9 | empirical | 1981-2010 | spi | 1.0 | 3.0 | 32 | 191 | 159 | +4.97 |
| ERA5 | 9 | empirical | 1981-2010 | spi | 1.5 | 3.0 | 1 | 52 | 51 | +51.00 |
| ERA5 | 9 | empirical | full | spei | 1.0 | 4.0 | 15 | 96 | 81 | +5.40 |
| ERA5 | 9 | empirical | full | spei | 1.5 | 4.0 | 1 | 10 | 9 | +9.00 |
| ERA5 | 9 | empirical | full | spi | 1.0 | 4.0 | 11 | 102 | 91 | +8.27 |
| ERA5 | 9 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 14 | 102 | 88 | +6.29 |
| ERA5 | 9 | empirical | 1981-2010 | spi | 1.0 | 4.0 | 10 | 114 | 104 | +10.40 |
| ERA5 | 9 | empirical | full | spei | 1.0 | 5.0 | 5 | 40 | 35 | +7.00 |
| ERA5 | 9 | empirical | full | spei | 1.5 | 5.0 | 1 | 5 | 4 | +4.00 |
| ERA5 | 9 | empirical | full | spi | 1.0 | 5.0 | 1 | 52 | 51 | +51.00 |
| ERA5 | 9 | empirical | 1981-2010 | spei | 1.0 | 5.0 | 5 | 54 | 49 | +9.80 |
| ERA5 | 9 | empirical | 1981-2010 | spi | 1.0 | 5.0 | 3 | 71 | 68 | +22.67 |
| ERA5 | 12 | empirical | full | spei | 1.0 | 3.0 | 20 | 135 | 115 | +5.75 |
| ERA5 | 12 | empirical | full | spi | 1.0 | 3.0 | 24 | 168 | 144 | +6.00 |
| ERA5 | 12 | empirical | full | spi | 1.5 | 3.0 | 1 | 29 | 28 | +28.00 |
| ERA5 | 12 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 26 | 160 | 134 | +5.15 |
| ERA5 | 12 | empirical | 1981-2010 | spei | 1.5 | 3.0 | 1 | 44 | 43 | +43.00 |
| ERA5 | 12 | empirical | 1981-2010 | spi | 1.0 | 3.0 | 30 | 200 | 170 | +5.67 |
| ERA5 | 12 | empirical | full | spei | 1.0 | 4.0 | 8 | 85 | 77 | +9.62 |
| ERA5 | 12 | empirical | full | spi | 1.0 | 4.0 | 8 | 96 | 88 | +11.00 |
| ERA5 | 12 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 5 | 108 | 103 | +20.60 |
| ERA5 | 12 | empirical | 1981-2010 | spi | 1.0 | 4.0 | 5 | 117 | 112 | +22.40 |
| ERA5 | 12 | empirical | full | spei | 1.0 | 5.0 | 3 | 37 | 34 | +11.33 |
| ERA5 | 12 | empirical | full | spi | 1.0 | 5.0 | 2 | 39 | 37 | +18.50 |
| ERA5 | 12 | empirical | 1981-2010 | spei | 1.0 | 5.0 | 2 | 65 | 63 | +31.50 |
| ERA5 | 12 | empirical | 1981-2010 | spi | 1.0 | 5.0 | 3 | 67 | 64 | +21.33 |
| NARR | 1 | empirical | full | spei | 1.0 | 3.0 | 20 | 143 | 123 | +6.15 |
| NARR | 1 | empirical | full | spi | 1.0 | 3.0 | 11 | 138 | 127 | +11.55 |
| NARR | 1 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 12 | 125 | 113 | +9.42 |
| NARR | 1 | empirical | 1981-2010 | spi | 1.0 | 3.0 | 6 | 145 | 139 | +23.17 |
| NARR | 1 | empirical | full | spei | 1.0 | 4.0 | 9 | 80 | 71 | +7.89 |
| NARR | 1 | empirical | full | spi | 1.0 | 4.0 | 7 | 97 | 90 | +12.86 |
| NARR | 1 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 5 | 83 | 78 | +15.60 |
| NARR | 1 | empirical | 1981-2010 | spi | 1.0 | 4.0 | 4 | 79 | 75 | +18.75 |
| NARR | 1 | empirical | full | spei | 1.0 | 5.0 | 2 | 37 | 35 | +17.50 |
| NARR | 1 | empirical | full | spi | 1.0 | 5.0 | 1 | 49 | 48 | +48.00 |
| NARR | 1 | empirical | 1981-2010 | spei | 1.0 | 5.0 | 1 | 52 | 51 | +51.00 |
| NARR | 1 | empirical | 1981-2010 | spi | 1.0 | 5.0 | 3 | 46 | 43 | +14.33 |
| NARR | 3 | empirical | full | spei | 1.0 | 3.0 | 16 | 131 | 115 | +7.19 |
| NARR | 3 | empirical | full | spi | 1.0 | 3.0 | 9 | 139 | 130 | +14.44 |
| NARR | 3 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 9 | 132 | 123 | +13.67 |
| NARR | 3 | empirical | 1981-2010 | spi | 1.0 | 3.0 | 4 | 129 | 125 | +31.25 |
| NARR | 3 | empirical | full | spei | 1.0 | 4.0 | 3 | 79 | 76 | +25.33 |
| NARR | 3 | empirical | full | spi | 1.0 | 4.0 | 2 | 80 | 78 | +39.00 |
| NARR | 3 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 1 | 78 | 77 | +77.00 |
| NARR | 3 | empirical | 1981-2010 | spi | 1.0 | 4.0 | 1 | 77 | 76 | +76.00 |
| NARR | 3 | empirical | full | spei | 1.0 | 5.0 | 1 | 57 | 56 | +56.00 |
| NARR | 3 | empirical | full | spi | 1.0 | 5.0 | 2 | 36 | 34 | +17.00 |
| NARR | 3 | empirical | 1981-2010 | spei | 1.0 | 5.0 | 1 | 41 | 40 | +40.00 |
| NARR | 3 | empirical | 1981-2010 | spi | 1.0 | 5.0 | 1 | 43 | 42 | +42.00 |
| NARR | 6 | empirical | full | spei | 1.0 | 3.0 | 19 | 135 | 116 | +6.11 |
| NARR | 6 | empirical | full | spi | 1.0 | 3.0 | 7 | 131 | 124 | +17.71 |
| NARR | 6 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 11 | 123 | 112 | +10.18 |
| NARR | 6 | empirical | 1981-2010 | spi | 1.0 | 3.0 | 7 | 134 | 127 | +18.14 |
| NARR | 6 | empirical | full | spei | 1.0 | 4.0 | 6 | 68 | 62 | +10.33 |
| NARR | 6 | empirical | full | spi | 1.0 | 4.0 | 1 | 64 | 63 | +63.00 |
| NARR | 6 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 6 | 73 | 67 | +11.17 |
| NARR | 6 | empirical | 1981-2010 | spi | 1.0 | 4.0 | 1 | 75 | 74 | +74.00 |
| NARR | 6 | empirical | full | spei | 1.0 | 5.0 | 4 | 43 | 39 | +9.75 |
| NARR | 6 | empirical | full | spi | 1.0 | 5.0 | 1 | 28 | 27 | +27.00 |
| NARR | 6 | empirical | 1981-2010 | spei | 1.0 | 5.0 | 3 | 45 | 42 | +14.00 |
| NARR | 9 | empirical | full | spei | 1.0 | 3.0 | 7 | 98 | 91 | +13.00 |
| NARR | 9 | empirical | full | spi | 1.0 | 3.0 | 4 | 112 | 108 | +27.00 |
| NARR | 9 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 4 | 121 | 117 | +29.25 |
| NARR | 9 | empirical | full | spei | 1.0 | 4.0 | 4 | 61 | 57 | +14.25 |
| NARR | 9 | empirical | full | spi | 1.0 | 4.0 | 2 | 62 | 60 | +30.00 |
| NARR | 9 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 2 | 68 | 66 | +33.00 |
| NARR | 9 | empirical | full | spei | 1.0 | 5.0 | 1 | 29 | 28 | +28.00 |
| NARR | 9 | empirical | 1981-2010 | spei | 1.0 | 5.0 | 1 | 29 | 28 | +28.00 |
| NARR | 12 | empirical | full | spei | 1.0 | 3.0 | 6 | 88 | 82 | +13.67 |
| NARR | 12 | empirical | full | spi | 1.0 | 3.0 | 5 | 93 | 88 | +17.60 |
| NARR | 12 | empirical | 1981-2010 | spei | 1.0 | 3.0 | 5 | 107 | 102 | +20.40 |
| NARR | 12 | empirical | 1981-2010 | spi | 1.0 | 3.0 | 7 | 114 | 107 | +15.29 |
| NARR | 12 | empirical | full | spei | 1.0 | 4.0 | 2 | 55 | 53 | +26.50 |
| NARR | 12 | empirical | full | spi | 1.0 | 4.0 | 1 | 62 | 61 | +61.00 |
| NARR | 12 | empirical | 1981-2010 | spei | 1.0 | 4.0 | 2 | 56 | 54 | +27.00 |
| ERA5 | 1 | loglogistic | 1981-2010 | spei | 2.0 | 3.0 | 2 | 5 | 3 | +1.50 |
| ERA5 | 3 | loglogistic | full | spei | 2.0 | 5.0 | 1 | 2 | 1 | +1.00 |
| ERA5 | 12 | loglogistic | 1981-2010 | spi | 2.0 | 3.0 | 3 | 5 | 2 | +0.67 |
| ERA5 | 12 | loglogistic | 1981-2010 | spei | 1.5 | 4.0 | 7 | 11 | 4 | +0.57 |
| ERA5 | 12 | loglogistic | 1981-2010 | spi | 1.5 | 4.0 | 9 | 15 | 6 | +0.67 |
| ERA5 | 12 | loglogistic | full | spi | 1.0 | 5.0 | 28 | 43 | 15 | +0.54 |
| ERA5 | 12 | loglogistic | 1981-2010 | spei | 1.5 | 5.0 | 3 | 5 | 2 | +0.67 |
| ERA5 | 12 | loglogistic | 1981-2010 | spi | 1.0 | 5.0 | 33 | 52 | 19 | +0.58 |
| NARR | 1 | loglogistic | 1981-2010 | spei | 2.0 | 3.0 | 1 | 2 | 1 | +1.00 |
| NARR | 1 | loglogistic | 1981-2010 | spei | 2.0 | 4.0 | 1 | 2 | 1 | +1.00 |
| NARR | 3 | loglogistic | 1981-2010 | spei | 2.0 | 3.0 | 3 | 5 | 2 | +0.67 |
| NARR | 6 | loglogistic | 1981-2010 | spei | 2.0 | 3.0 | 3 | 6 | 3 | +1.00 |
| NARR | 6 | loglogistic | 1981-2010 | spei | 1.5 | 4.0 | 6 | 11 | 5 | +0.83 |
| NARR | 6 | loglogistic | 1981-2010 | spei | 2.0 | 4.0 | 1 | 2 | 1 | +1.00 |
| NARR | 6 | loglogistic | 1981-2010 | spei | 2.0 | 5.0 | 1 | 2 | 1 | +1.00 |
| NARR | 9 | loglogistic | 1981-2010 | spei | 1.5 | 3.0 | 12 | 22 | 10 | +0.83 |
| NARR | 12 | loglogistic | full | spei | 2.0 | 3.0 | 1 | 2 | 1 | +1.00 |
| NARR | 12 | loglogistic | 1981-2010 | spei | 1.5 | 3.0 | 5 | 14 | 9 | +1.80 |
| NARR | 12 | loglogistic | 1981-2010 | spei | 1.0 | 4.0 | 18 | 30 | 12 | +0.67 |
| NARR | 12 | loglogistic | 1981-2010 | spei | 1.5 | 4.0 | 3 | 5 | 2 | +0.67 |
| NARR | 12 | loglogistic | 1981-2010 | spei | 1.5 | 5.0 | 3 | 5 | 2 | +0.67 |
| NARR | 12 | loglogistic | 1981-2010 | spi | 2.0 | 5.0 | 1 | 0 | -1 | -1.00 |

## Files

- `scenarios_tiefix.csv` — 720 masked scenarios, archived schema/order + `old_n_cdpe_months` and `delta`.
- `decomposition_tiefix.csv` — long-form decomposition (arm, version, scale, factor, share).
- `reproduction_check.csv` — Step 1 per-scenario gate.
- `seed_sensitivity.csv`, `tie_diagnostics.csv` (mean tied cells per pole per scenario), `changed_gt50pct.csv`.
- `run_manifest.json` — versions, seeds, config hash, input/output file hashes.
- `cache/` (masked field npz per configuration), `checkpoints/` (per-field results; delete or pass `--force` to recompute).
