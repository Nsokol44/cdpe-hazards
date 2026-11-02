#!/usr/bin/env python3
"""Step 10 - Fact sheet for the hazards arm.

Prints every number needed to fill the manuscript's results tokens, taken
only from the computed results files (DESIGN LOCK gate G3). The prose in
the manuscript is written from this sheet, and step 11 then verifies that
every number in the hazard sections appears in these source files.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"


def fmt(x, nd=2):
    return "null" if x is None else f"{x:.{nd}f}"


def main() -> int:
    s = json.loads((RES / "rate_ratios_summary.json").read_text())
    storm = pd.read_csv(RES / "hazard_series_storm.csv")
    hw = pd.read_csv(RES / "hazard_series_heatwave.csv")
    monthly = pd.read_csv(RES / "monthly_series_all.csv")
    slog = json.loads((RES / "storm_build_log.json").read_text())
    hlog = json.loads((RES / "heatwave_build_log.json").read_text())
    lines = []
    lines.append("== STORM EVENTS BUILD ==")
    lines.append(json.dumps(slog))
    lines.append(f"total tornado_all 1980-2023: {int(storm['tornado_all'].sum())}")
    lines.append(f"total tornado_ef1plus: {int(storm['tornado_ef1plus'].sum())}")
    lines.append(f"total tornado_ef2plus: {int(storm['tornado_ef2plus'].sum())}")
    lines.append(f"total hail_all: {int(storm['hail_all'].sum())}")
    lines.append(f"total hail_ge1in: {int(storm['hail_ge1in'].sum())}")
    lines.append(f"mean monthly tornado_all: {storm['tornado_all'].mean():.1f}")
    lines.append(f"mean monthly hail_ge1in: {storm['hail_ge1in'].mean():.1f}")
    lines.append("== HEAT WAVES ==")
    lines.append(json.dumps(hlog))
    lines.append(f"mean monthly heatwave_days_per_cell: "
                 f"{hw['heatwave_days_per_cell'].mean():.3f}")
    # Rebuild 2026-11-02: the GLM (lightning) arm was dropped from the
    # paper on the author's direction; the summary of record carries no
    # GLM blocks, so the GLM section and rate-ratio row are removed.
    lines.append("== RATE RATIOS ==")
    for h in ["tornado_all", "tornado_ef1plus", "tornado_ef2plus",
              "hail_ge1in", "hail_all", "heatwave_days_per_cell"]:
        d = s[h]
        b, e = d["baseline"], d["envelope"]
        lines.append(
            f"{h}: baseline RR {fmt(b['rr'])} (95% CI {fmt(b['ci_lo'])} to "
            f"{fmt(b['ci_hi'])}, n_cdpe={b['n_cdpe_months']}); envelope "
            f"n={e['n_configs_included']}, range {fmt(e['rr_min'])} to "
            f"{fmt(e['rr_max'])}, share_same_side="
            f"{fmt(e['share_same_side_as_baseline'])}, share_ci_excl_1="
            f"{fmt(e['share_ci_excludes_1'])}; G2 robust={d['gate_G2_robust']}")
    lines.append("== SPLIT ERA (baseline) ==")
    for h, eras in s["split_era_baseline"].items():
        for era, d in eras.items():
            lines.append(f"{h} {era}: RR {fmt(d['rr'])} (CI {fmt(d['ci_lo'])} "
                         f"to {fmt(d['ci_hi'])}, n={d['n_cdpe_months']})")
    text = "\n".join(lines)
    (RES / "fact_sheet.txt").write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
