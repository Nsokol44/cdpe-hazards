#!/usr/bin/env python3
"""Phase 3, Step 32 - validate inputs and build the Phase 3 design table.

Validates, before any analysis:
  * aligned catalog (companion_v211 SPEI-1 baseline = 52 months, all in
    Jan 1980-Dec 2023; US-anchored subset = 15; Arm A v2.10 = 46;
    companion-vs-ArmA intersection = 32);
  * monthly hazard series (cdpe-hazards-aas/results/monthly_series_all.csv,
    the hazards analysis of record): 528 months, Jan 1980-Dec 2023, totals
    54,607 tornadoes / 229,650 hail >= 1 in / 379,430 hail overall, and the
    heat-wave total: the series stores heatwave_days_per_cell (mean over
    3,608 land cells, heatwave_build_log.json), so total cell-days =
    sum(days_per_cell) * 3608 = 475,232.99 (asserted);
  * era split of record: 1980-1995 vs 1996-2023 (1996 boundary, from the
    frozen Step 06 split-era block).

Builds results/phase3_2026-11-02/design_monthly.csv with, for every month,
the three hazard outcomes, ONI, and the exposure indicators for the
same-month arms (aligned 52, US-anchored 15, Arm A 46) and the lagged arms
(exposure label of regime month t attached to outcome month t+1).
Also writes oni_monthly.csv + DATA_MANIFEST.md.

ONI: NOAA PSL oni.data (CPC ONI; 3-month running mean of ERSST SST
anomalies in the Nino 3.4 region, each season value centred on its middle
month), retrieved 2026-11-02 via the official file
https://psl.noaa.gov/data/correlation/oni.data (footer: ONI from CPC,
ERSST v6 vintage as of the retrieval). The 1980-2023 monthly values below
are transcribed verbatim from that retrieval; the fallback file
~/workspace/seg-revision/seg_rerun/data/NewONI.csv (ERSST v5 vintage,
provenance in ONI_PROVENANCE.md) is used only as a cross-check
(correlation and max absolute difference are reported in the manifest).

Deterministic; no randomness. Deps: numpy, pandas.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

PKG = Path(__file__).resolve().parents[1]
ALIGN = PKG / "results" / "alignment_2026-11-02"
AAS_RES = PKG.parent / "cdpe-hazards-aas" / "results"
OUT = PKG / "results" / "phase3_2026-11-02"
OUT.mkdir(parents=True, exist_ok=True)

# PSL oni.data rows 1980-2023, transcribed from the 2026-11-02 retrieval
# (year followed by Jan..Dec centred 3-month running-mean values).
ONI_ROWS = """1980 0.62 0.47 0.35 0.34 0.45 0.40 0.18 -0.06 -0.17 -0.07 0.08 -0.05
1981 -0.27 -0.42 -0.41 -0.27 -0.28 -0.27 -0.28 -0.23 -0.08 -0.16 -0.19 -0.14
1982 -0.05 0.02 0.07 0.34 0.65 0.73 0.78 0.99 1.45 1.82 2.03 2.12
1983 2.14 1.91 1.52 1.23 0.95 0.62 0.25 -0.06 -0.43 -0.76 -0.96 -0.89
1984 -0.63 -0.51 -0.38 -0.47 -0.55 -0.52 -0.39 -0.22 -0.32 -0.62 -0.95 -1.06
1985 -1.01 -0.86 -0.85 -0.80 -0.79 -0.60 -0.44 -0.33 -0.31 -0.30 -0.28 -0.36
1986 -0.40 -0.38 -0.25 -0.17 -0.09 0.02 0.24 0.46 0.64 0.86 1.06 1.21
1987 1.18 1.13 1.02 0.94 0.95 1.11 1.30 1.46 1.49 1.41 1.20 1.00
1988 0.63 0.37 -0.03 -0.45 -0.99 -1.30 -1.30 -1.14 -1.27 -1.54 -1.81 -1.85
1989 -1.64 -1.38 -1.09 -0.85 -0.61 -0.40 -0.37 -0.36 -0.33 -0.25 -0.12 -0.04
1990 0.18 0.19 0.30 0.27 0.25 0.25 0.26 0.32 0.31 0.27 0.31 0.34
1991 0.35 0.26 0.23 0.29 0.49 0.63 0.77 0.67 0.72 0.83 1.18 1.43
1992 1.54 1.50 1.40 1.30 1.08 0.72 0.35 0.08 -0.15 -0.22 -0.24 -0.05
1993 0.13 0.31 0.50 0.73 0.76 0.56 0.28 0.22 0.20 0.20 0.20 0.19
1994 0.07 0.00 0.04 0.17 0.25 0.23 0.30 0.30 0.47 0.66 0.93 0.97
1995 0.88 0.65 0.46 0.19 0.03 -0.11 -0.30 -0.55 -0.81 -0.97 -1.05 -1.01
1996 -0.88 -0.70 -0.52 -0.36 -0.25 -0.24 -0.22 -0.27 -0.30 -0.33 -0.39 -0.41
1997 -0.41 -0.26 -0.03 0.30 0.71 1.13 1.48 1.79 2.04 2.24 2.34 2.37
1998 2.22 1.91 1.40 1.03 0.40 -0.08 -0.63 -0.83 -1.02 -1.12 -1.31 -1.47
1999 -1.51 -1.25 -0.93 -0.80 -0.79 -0.84 -0.90 -0.94 -1.00 -1.13 -1.35 -1.53
2000 -1.47 -1.26 -0.98 -0.81 -0.67 -0.62 -0.48 -0.40 -0.42 -0.54 -0.76 -0.78
2001 -0.76 -0.54 -0.43 -0.29 -0.19 -0.08 -0.05 -0.13 -0.15 -0.26 -0.33 -0.32
2002 -0.15 0.07 0.11 0.15 0.30 0.45 0.57 0.63 0.78 0.99 1.19 1.08
2003 0.90 0.59 0.38 -0.01 -0.18 -0.13 0.09 0.14 0.23 0.23 0.29 0.29
2004 0.34 0.27 0.19 0.10 0.12 0.22 0.39 0.54 0.58 0.61 0.64 0.71
2005 0.62 0.55 0.40 0.37 0.27 0.09 -0.04 -0.14 -0.11 -0.27 -0.57 -0.82
2006 -0.86 -0.80 -0.63 -0.45 -0.19 -0.05 0.12 0.33 0.54 0.71 0.88 0.88
2007 0.62 0.19 -0.12 -0.32 -0.34 -0.41 -0.49 -0.77 -1.05 -1.38 -1.57 -1.72
2008 -1.76 -1.61 -1.37 -1.05 -0.85 -0.56 -0.33 -0.20 -0.25 -0.36 -0.57 -0.79
2009 -0.89 -0.84 -0.63 -0.35 0.03 0.34 0.50 0.56 0.66 0.92 1.31 1.50
2010 1.47 1.21 0.88 0.38 -0.16 -0.66 -0.98 -1.24 -1.43 -1.54 -1.57 -1.48
2011 -1.29 -1.06 -0.85 -0.68 -0.50 -0.34 -0.37 -0.50 -0.76 -0.94 -1.02 -0.92
2012 -0.71 -0.56 -0.44 -0.35 -0.18 0.03 0.28 0.39 0.37 0.28 0.13 -0.03
2013 -0.24 -0.28 -0.23 -0.20 -0.30 -0.38 -0.45 -0.34 -0.32 -0.14 -0.12 -0.11
2014 -0.24 -0.21 -0.02 0.25 0.35 0.22 0.07 0.07 0.24 0.51 0.70 0.80
2015 0.73 0.65 0.72 0.86 1.04 1.19 1.44 1.73 2.02 2.28 2.45 2.59
2016 2.50 2.21 1.69 1.11 0.57 0.09 -0.19 -0.34 -0.42 -0.51 -0.49 -0.37
2017 -0.08 0.08 0.27 0.32 0.35 0.32 0.14 -0.07 -0.23 -0.44 -0.61 -0.76
2018 -0.71 -0.67 -0.55 -0.35 -0.07 0.13 0.20 0.30 0.52 0.82 1.04 1.05
2019 0.99 0.94 0.87 0.82 0.71 0.59 0.38 0.20 0.31 0.51 0.72 0.75
2020 0.71 0.66 0.57 0.33 0.04 -0.18 -0.29 -0.43 -0.77 -1.00 -1.11 -1.06
2021 -0.99 -0.85 -0.74 -0.56 -0.40 -0.31 -0.35 -0.46 -0.64 -0.77 -0.91 -0.83
2022 -0.76 -0.68 -0.77 -0.86 -0.83 -0.73 -0.70 -0.78 -0.87 -0.89 -0.82 -0.70
2023 -0.55 -0.33 -0.11 0.19 0.46 0.73 1.00 1.25 1.50 1.74 1.90 1.99"""


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def main() -> int:
    checks = {}

    # --- aligned catalog ---
    summ = json.loads((ALIGN / "alignment_summary.json").read_text())
    comp = summ["companion_v211"]
    assert comp["n_months"] == 52 and comp["n_us_anchored_months"] == 15
    assert summ["armA_v210"]["n_months"] == 46
    assert summ["subset_test"]["intersection"] == 32
    aligned = pd.read_csv(ALIGN / "aligned_month_sets.csv")
    comp_months = sorted(aligned.loc[aligned["in_companion_v211"], "month"])
    arma_months = sorted(aligned.loc[aligned["in_armA_v210"], "month"])
    usa_months = sorted(aligned.loc[aligned["in_companion_v211"]
                                     & (aligned["companion_us_anchored"]
                                        .astype(str) == "True"), "month"])
    # pole_classification is the authoritative US-anchored source
    poles = pd.read_csv(ALIGN / "pole_classification.csv")
    pc = poles[poles["set"] == "companion_v211"]
    usa2 = sorted(pc.loc[pc["us_anchored"].astype(str) == "True", "month"])
    assert usa_months == usa2 == sorted(comp["us_anchored_months"]), \
        (usa_months, usa2)
    assert len(comp_months) == 52 and len(arma_months) == 46
    assert min(comp_months) >= "1980-01" and max(comp_months) <= "2023-12"
    assert len(set(comp_months) & set(arma_months)) == 32
    checks["aligned"] = {"n_companion": 52, "n_us_anchored": 15,
                         "n_armA": 46, "intersection_comp_armA": 32,
                         "companion_max_month": max(comp_months),
                         "all_companion_tplus1_in_window":
                             max(comp_months) < "2023-12"}

    # --- hazard series ---
    ms = pd.read_csv(AAS_RES / "monthly_series_all.csv")
    assert len(ms) == 528 and ms["month"].iloc[0] == "1980-01" \
        and ms["month"].iloc[-1] == "2023-12"
    assert int(ms["tornado_all"].sum()) == 54607
    assert int(ms["hail_ge1in"].sum()) == 229650
    assert int(ms["hail_all"].sum()) == 379430
    hwlog = json.loads((AAS_RES / "heatwave_build_log.json").read_text())
    land_cells = int(hwlog["land_cells"])
    assert land_cells == 3608
    heat_cell_days = float(ms["heatwave_days_per_cell"].sum() * land_cells)
    assert abs(heat_cell_days - 475232.994896) < 0.01, heat_cell_days
    # the series' own cdpe_baseline column is the Arm A 46 set
    base_months = sorted(ms.loc[ms["cdpe_baseline"] == 1, "month"])
    assert base_months == arma_months, "series baseline != Arm A aligned set"
    checks["series"] = {"rows": 528, "tornado_all": 54607,
                        "hail_ge1in": 229650, "hail_all": 379430,
                        "heatwave_cell_days_total": heat_cell_days,
                        "heatwave_land_cells": land_cells}

    # --- ONI ---
    recs = []
    for line in ONI_ROWS.strip().splitlines():
        parts = line.split()
        yr, vals = int(parts[0]), [float(v) for v in parts[1:]]
        assert len(vals) == 12
        for m, v in enumerate(vals, start=1):
            recs.append({"month": f"{yr:04d}-{m:02d}", "oni": v})
    oni = pd.DataFrame(recs)
    assert len(oni) == 528 and oni["oni"].abs().max() < 5
    oni.to_csv(OUT / "oni_monthly.csv", index=False)
    fb = pd.read_csv(Path.home() / "workspace" / "seg-revision"
                     / "seg_rerun" / "data" / "NewONI.csv")
    fb["month"] = pd.to_datetime(fb["date"]).dt.strftime("%Y-%m")
    merged = oni.merge(fb[["month", "oni"]], on="month",
                       suffixes=("_psl", "_v5"))
    corr = float(np.corrcoef(merged["oni_psl"], merged["oni_v5"])[0, 1])
    maxdiff = float((merged["oni_psl"] - merged["oni_v5"]).abs().max())
    import hashlib as _hl
    checks["oni"] = {"oni_monthly_sha256":
                    _hl.sha256((OUT / "oni_monthly.csv")
                               .read_bytes()).hexdigest(),
                    "corr_vs_seg_v5_fallback": corr,
                     "max_abs_diff_vs_seg_v5_fallback": maxdiff}
    manifest = f"""# Phase 3 ONI data manifest

- Covariate file: `oni_monthly.csv` (528 rows, 1980-01 to 2023-12).
- Source: NOAA Physical Sciences Laboratory `oni.data` — the CPC Oceanic
  Nino Index (ONI). Official URL: https://psl.noaa.gov/data/correlation/oni.data
  (the file's own footer cites the CPC source
  https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt).
- Retrieved: 2026-11-02 (page crawl timestamp 2026-11-02 13:02 UTC).
- Convention: the ONI is the 3-month running mean of ERSST SST anomalies
  in the Nino 3.4 region (5N-5S, 120-170W); each overlapping season value
  is assigned to its centre month, so the value stored for month t is the
  season centred on t. The PSL file already stores values in this monthly
  centred layout (one row per year, Jan..Dec); no re-centring was applied.
- Vintage: the retrieved file states "As of 09/7/2026, uses NOAA ERSST
  V6". Values for 1980-2023 were transcribed verbatim from the retrieval
  into code/32_prepare_inputs.py (ONI_ROWS) and are written out unchanged.
- SHA-256 of oni_monthly.csv as written: computed at runtime and recorded
  in validation.json (this manifest is written by the same run).
- Cross-check against the fallback file
  ~/workspace/seg-revision/seg_rerun/data/NewONI.csv (ERSST v5 vintage;
  provenance: ~/workspace/seg-revision/seg_rerun/ONI_PROVENANCE.md):
  Pearson r = {corr:.4f}, max |difference| = {maxdiff:.2f} over 1980-2023.
  Differences are the expected v5-to-v6 revision; the PSL/CPC file of
  record above is the covariate used in all Phase 3 models.
"""
    (OUT / "DATA_MANIFEST.md").write_text(manifest)

    # --- design table ---
    df = ms[["month", "year", "cal", "tornado_all", "hail_ge1in",
             "hail_all", "heatwave_days_per_cell"]].copy()
    df["heatwave_cell_days"] = (df["heatwave_days_per_cell"]
                                * land_cells).round().astype(int)
    df = df.merge(oni, on="month", how="left")
    assert df["oni"].notna().all()
    cs, us, aa = set(comp_months), set(usa_months), set(arma_months)
    df["exp_same52"] = df["month"].isin(cs).astype(int)
    df["exp_same15"] = df["month"].isin(us).astype(int)
    df["exp_armA46"] = df["month"].isin(aa).astype(int)
    # lagged arms: exposure label of regime month t attaches to outcome t+1
    nxt = {m: i for i, m in enumerate(df["month"])}
    def lag_label(months_set):
        lab = np.zeros(len(df), dtype=int)
        for t in months_set:
            i = nxt[t]
            if i + 1 < len(df):
                lab[i + 1] = 1
        return lab
    df["exp_lag52"] = lag_label(cs)
    df["exp_lag15"] = lag_label(us)
    df["era"] = np.where(df["year"] <= 1995, "1980-1995", "1996-2023")
    df.to_csv(OUT / "design_monthly.csv", index=False)

    checks["design"] = {
        "n_same52": int(df["exp_same52"].sum()),
        "n_same15": int(df["exp_same15"].sum()),
        "n_armA46": int(df["exp_armA46"].sum()),
        "n_lag52_outcome_months": int(df["exp_lag52"].sum()),
        "n_lag15_outcome_months": int(df["exp_lag15"].sum()),
        "lag_frame_months": int(len(df) - 1),
        "era_early_months": int((df["era"] == "1980-1995").sum()),
        "era_late_months": int((df["era"] == "1996-2023").sum()),
        "aligned_in_early_era": int(((df["era"] == "1980-1995")
                                     & (df["exp_same52"] == 1)).sum()),
    }
    (OUT / "validation.json").write_text(json.dumps(checks, indent=2))
    print(json.dumps(checks, indent=2))
    print("wrote design_monthly.csv, oni_monthly.csv, DATA_MANIFEST.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
