# Supplement — the nClimGrid masked control: how much of the SPEI difference is coverage geometry?

When the CDPE detector (threshold 1.5, radius 4.0°, frozen gates) is run on nClimGrid-derived SPEI instead of SPEIbase, the baseline month counts collapse — for SPEI-1, from 46 months to 3 over January 1980–December 2023. This supplement reports the masked control that decomposes that collapse. The control re-runs the detector on the *unchanged* SPEIbase v2.10 fields with one modification: every cell that is invalid in the aggregated nClimGrid product is set to missing, so the SPEIbase values are seen through the nClimGrid coverage mask and nothing else changes.

**Baseline CDPE month counts (threshold 1.5, r = 4.0°):**

| Index | SPEIbase (full grid) | SPEIbase under the CONUS mask | nClimGrid |
|---|---|---|---|
| SPEI-1 | 46 | **10** | 3 |
| SPEI-3 | 48 | **15** | 8 |
| SPEI-6 | 51 | **14** | 8 |

For SPEI-1, the mask alone accounts for 46 → 10 of the 46 → 3 collapse; the remaining 10 → 3 is a difference in the products' values on the months the coverage gate lets through. The gate arithmetic is the dominant term: laying the CONUS mask over unchanged SPEIbase values raises the number of months failing the coverage gate (either pole) from 296 to 436 of 528 months, because any pole within 4° of a coast, the northern border, or the Great Lakes then has more than 10% missing buffer cells. The mask leaves 3,575 valid cells of the 5,900-cell domain, against 4,399 for the SPEIbase grid.

The value difference is real but secondary. Among valid cell-months at SPEI-1, the dry tail (values ≤ −1.5) holds 3.9% of cell-months in the nClimGrid gamma product against 5.7% in SPEIbase, while the wet tails (≥ +1.5) are nearly identical (8.1% against 7.9%). A thinner dry tail converts fewer gate-passing months even where coverage is equal.

**Reading.** Where both products have data they are recognisably the same phenomenon, but the frozen coverage gate is silently a rule about geographic coverage: on a CONUS-only grid it disqualifies most months before their values are ever tested. Product comparisons of CDPE counts that do not hold coverage fixed confound the gate with the climate signal.

---

*Verification (Phase 3, 2026-11-02): every number above was re-checked against the archived run outputs and matched — baseline counts 46/48/51 (full), 10/15/14 (masked) and 3/8/8 (nClimGrid) from `gate_diagnostics_summary.json` in `cdpe_sensitivity/results/run_armA_speibase_rebuild_2026-11-02/{B_speibase_full,A_speibase_masked}/` and `run_armA_nclimgrid_2026-11-01/`; SPEI-1 gate failures 296 (full) and 436 (masked) from the same two files; valid cells 3,575 and 4,399 as the archived finite shares (0.605932 and 0.745593 of the 5,900-cell grid) in the nClimGrid run's diagnostics; dry-tail shares 3.93% vs 5.70% and wet-tail shares 8.11% vs 7.92% (SPEI-1) from `run_armA_nclimgrid_2026-11-01/gate_diagnostics_summary.json` (`tail_mass_le_-1.5_pct` / `tail_mass_ge_+1.5_pct`). No number in this supplement could not be verified.*
