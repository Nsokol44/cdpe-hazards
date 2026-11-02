#!/usr/bin/env python3
"""Fix Round 2, item 4 - pole-relative strata on the LAGGED arm.

Same design as code/35_pole_relative.py (same-month), shifted one
month, exactly as the paper's lagged arm shifts the domain-wide
estimands: for each aligned CDPE regime month m (companion_v211, 52),
the REPORTS OF THE FOLLOWING MONTH m+1 are classified by m's poles
(near-dry / near-wet within 4.0 degrees of the pole, nearer pole wins
on overlap, else elsewhere). Controls mirror the same-month design:
for every non-CDPE regime month t with the same calendar month as m,
the reports of month t+1, classified by m's poles; a control instance
counts only when t+1 is inside the record. Stratum rate ratio =
(exposed reports / 52) / (control reports / control instances).
Bootstrap: resample the 52 regime months with replacement, B = 2000,
seed 20261102, percentile intervals.

Rationale (the author's 2026-11-02 verification read): the same-month
pole-relative tornado estimates (2.52 near the wet pole, 0.56 near the
dry pole) carry the same reverse-causation exposure as the same-month
headline: a wet pole is where the month's rain fell and storms make
rain, and few storms near a dry pole is close to tautological
same-month. The lagged strata are the circularity-free version: the
poles are fixed by month m's field and the storms are month m+1's.

Multiplicity: this run adds 6 stratum-hazard estimates (3 strata x 2
hazards); the pole-relative family in the paper is 12 estimates
(6 same-month from code/35 + 6 lagged here). Heat waves are excluded
for the same reason as in code/35 (gridMET land grid, not report
cells).

Inputs: results/phase3_2026-11-02/monthly_cell_counts.csv (the frozen
Step-04 counting saved by code/35), results/alignment_2026-11-02/
pole_classification.csv.
Outputs: results/fixround2_2026-11-02/pole_relative_lagged_results.csv

Deterministic. Deps: numpy, pandas.
"""
from pathlib import Path

import numpy as np
import pandas as pd

PKG = Path(__file__).resolve().parents[1]
P3 = PKG / "results" / "phase3_2026-11-02"
ALIGN = PKG / "results" / "alignment_2026-11-02"
OUT = PKG / "results" / "fixround2_2026-11-02"
OUT.mkdir(parents=True, exist_ok=True)
B = 2000
SEED = 20261102


def next_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    return f"{y + (mo == 12):04d}-{(mo % 12) + 1:02d}"


def stratum_of(clat, clon, dry, wet):
    d_dry = np.hypot(clat + 0.5 - dry[0], clon + 0.5 - dry[1])
    d_wet = np.hypot(clat + 0.5 - wet[0], clon + 0.5 - wet[1])
    near_d, near_w = d_dry <= 4.0, d_wet <= 4.0
    out = np.full(len(clat), "elsewhere", dtype=object)
    both = near_d & near_w
    out[near_d & ~near_w] = "near_dry"
    out[near_w & ~near_d] = "near_wet"
    out[both & (d_dry <= d_wet)] = "near_dry"
    out[both & (d_dry > d_wet)] = "near_wet"
    return out


def main() -> int:
    grid = pd.read_csv(P3 / "monthly_cell_counts.csv")
    by_month = {m: g for m, g in grid.groupby("month")}
    all_months = sorted(by_month)
    month_set = set(all_months)
    poles = pd.read_csv(ALIGN / "pole_classification.csv")
    pc = poles[poles["set"] == "companion_v211"].copy()
    cdpe_months = sorted(pc["month"])
    assert len(cdpe_months) == 52
    pole_map = {r.month: ((r.dry_lat, r.dry_lon), (r.wet_lat, r.wet_lon))
                for r in pc.itertuples()}
    cdpe_set = set(cdpe_months)

    per_m = {}
    for m in cdpe_months:
        dry, wet = pole_map[m]
        exposed_month = next_month(m)
        controls_t = [t for t in all_months
                      if t[5:7] == m[5:7] and t not in cdpe_set
                      and next_month(t) in month_set]
        gm = by_month[exposed_month]
        sm = stratum_of(gm["clat"].values, gm["clon"].values, dry, wet)
        ctrl_frames = []
        for t in controls_t:
            gt = by_month[next_month(t)]
            st = stratum_of(gt["clat"].values, gt["clon"].values,
                            dry, wet)
            ctrl_frames.append((gt, st))
        d = {}
        for s in ("near_dry", "near_wet", "elsewhere"):
            e_tor = float(gm.loc[sm == s, "tornado"].sum())
            e_hail = float(gm.loc[sm == s, "hail_ge1in"].sum())
            c_tor = sum(float(g.loc[st == s, "tornado"].sum())
                        for g, st in ctrl_frames)
            c_hail = sum(float(g.loc[st == s, "hail_ge1in"].sum())
                         for g, st in ctrl_frames)
            d[s] = (e_tor, e_hail, c_tor, c_hail, len(controls_t))
        per_m[m] = d

    def rr_from(month_list, stratum, haz_idx):
        e = sum(per_m[m][stratum][haz_idx] for m in month_list)
        c = sum(per_m[m][stratum][haz_idx + 2] for m in month_list)
        nc = sum(per_m[m][stratum][4] for m in month_list)
        if c == 0 or nc == 0:
            return np.nan
        return (e / len(month_list)) / (c / nc)

    rng = np.random.default_rng(SEED)
    rows = []
    for haz, haz_idx, hlabel in [("tornado_all", 0, "Tornadoes"),
                                 ("hail_ge1in", 1, "Hail >= 1 in")]:
        tot_e = sum(per_m[m][s][haz_idx] for m in cdpe_months
                    for s in ("near_dry", "near_wet", "elsewhere"))
        for s in ("near_dry", "near_wet", "elsewhere"):
            point = rr_from(cdpe_months, s, haz_idx)
            reps = []
            for _ in range(B):
                sample = list(rng.choice(cdpe_months, size=52,
                                         replace=True))
                reps.append(rr_from(sample, s, haz_idx))
            reps = np.array([r for r in reps if np.isfinite(r)])
            e = sum(per_m[m][s][haz_idx] for m in cdpe_months)
            c = sum(per_m[m][s][haz_idx + 2] for m in cdpe_months)
            nc = sum(per_m[m][s][4] for m in cdpe_months)
            rows.append({
                "hazard": haz, "hazard_label": hlabel, "stratum": s,
                "rr": point,
                "ci_lo": float(np.percentile(reps, 2.5)),
                "ci_hi": float(np.percentile(reps, 97.5)),
                "cdpe_following_reports": int(e),
                "control_reports": int(c),
                "n_control_month_instances": int(nc),
                "share_of_following_reports": float(e / tot_e),
                "bootstrap_finite": int(len(reps))})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "pole_relative_lagged_results.csv", index=False)
    print(res.to_string(index=False))
    print(f"multiplicity: {len(res)} lagged stratum-hazard estimates; "
          f"pole-relative family total = 12 (6 same-month + 6 lagged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
