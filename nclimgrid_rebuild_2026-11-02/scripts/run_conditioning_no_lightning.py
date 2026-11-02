#!/usr/bin/env python3
"""Workstream C (2026-11-02) - hazards conditioning WITHOUT the lightning arm.

The estimator code (rr_from_arrays, estimate, windows, thresholds, seed
20261026, B = 2000 year bootstrap) is the frozen Step 06 of the hazards
pipeline (cdpe-hazards-aas/code/06_rate_ratios.py), copied verbatim.
Documented changes, and only these:

1. Inputs are read from their locations of record: hazard series and
   GLM fetch files from cdpe-hazards-nclimgrid/win2023/results/ (the
   tree the delta report verified reproduces the frozen storm and
   heat-wave series exactly -- re-verified value-equal against
   cdpe-hazards-aas/results/ before this run), and the 36 Arm A
   configuration month sets from cdpe_sensitivity/results/
   run_armA_2026-10-05/cdpe_monthly_series.csv (verified identical to
   the frozen cdpe_monthly_series_armA.csv input and, for the 27 SPEI
   configurations, to the Workstream B rebuild).
2. The lightning (GLM) arm is DROPPED from all outputs, per the
   author's direction: the summary JSON carries no glm_flash_box block
   and no glm_completeness gate block; the by-configuration CSV carries
   no GLM rows; the monthly series table carries no GLM column. To keep
   every retained number bit-identical to the with-lightning run of
   record, the GLM series is still estimated internally in the frozen
   series order so the shared bootstrap RNG stream is consumed exactly
   as frozen; its estimates are discarded, never written.
3. Outputs land in the rebuild run directory, not the package results
   directory. A verification file compares every retained number
   against the with-lightning run of record
   (cdpe-hazards-aas/results/rate_ratios_summary.json and
   rate_ratios_by_config.csv).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

PKG = Path(__file__).resolve().parents[1]
FIN = PKG.parent
WIN_RES = FIN / "cdpe-hazards-nclimgrid" / "win2023" / "results"
AAS_RES = FIN / "cdpe-hazards-aas" / "results"
CFG_PATH = PKG / "results" / "run_armA_2026-10-05" / "cdpe_monthly_series.csv"
OUT = PKG / "results" / "run_armA_speibase_rebuild_2026-11-02" / "C_conditioning"

SEED = 20261026
B = 2000
BASELINE = "SPEI-1|thr=1.5|r=4.0"
PRIMARY = ["tornado_all", "hail_ge1in", "heatwave_days_per_cell", "glm_flash_box"]
SECONDARY = ["tornado_ef1plus", "tornado_ef2plus", "hail_all"]
RETAINED = ["tornado_all", "hail_ge1in", "heatwave_days_per_cell",
            "tornado_ef1plus", "tornado_ef2plus", "hail_all"]
LONG_YEARS = list(range(1980, 2024))
GLM_YEARS = list(range(2018, 2024))


def load_months() -> pd.DataFrame:
    df = pd.read_csv(WIN_RES / "hazard_series_storm.csv")
    hw = pd.read_csv(WIN_RES / "hazard_series_heatwave.csv")
    df = df.merge(hw[["month", "heatwave_days_per_cell"]], on="month", how="left")
    glm = {}
    for p in sorted((WIN_RES / "glm_fetch").glob("*.json")):
        d = json.loads(p.read_text())
        if d["valid"]:
            glm[d["month"]] = sum(
                r["n_flash_box"] for r in d["records"]
                if r.get("n_flash_box") is not None
                and (int(r["day"][-2:]) - 1) % 3 == 0)
        else:
            glm[d["month"]] = np.nan
    df["glm_flash_box"] = df["month"].map(glm)
    df["year"] = df["month"].str[:4].astype(int)
    df["cal"] = df["month"].str[5:7].astype(int)
    return df


def load_configs() -> pd.DataFrame:
    cfg = pd.read_csv(CFG_PATH, parse_dates=["date"])
    cfg["month"] = cfg["date"].dt.strftime("%Y-%m")
    return cfg.set_index("month")


def rr_from_arrays(values: np.ndarray, cal: np.ndarray,
                   cdpe: np.ndarray) -> float:
    """Stratified rate ratio on one (possibly bootstrapped) month sample."""
    ok = ~np.isnan(values)
    total_cdpe = int((cdpe & ok).sum())
    if total_cdpe == 0:
        return np.nan
    num = den = wsum = 0.0
    for m in range(1, 13):
        c = ok & cdpe & (cal == m)
        k = ok & ~cdpe & (cal == m)
        if c.sum() == 0:
            continue
        if k.sum() == 0:
            continue
        w = c.sum() / total_cdpe
        num += w * values[c].mean()
        den += w * values[k].mean()
        wsum += w
    if wsum == 0 or den == 0:
        return np.nan
    return (num / wsum) / (den / wsum)


def estimate(df: pd.DataFrame, cfg: pd.Series, series: str,
             years: list[int], rng: np.random.Generator) -> dict:
    sub = df[df["year"].isin(years)]
    cdpe_map = cfg.to_dict()
    cdpe = sub["month"].map(lambda m: bool(cdpe_map.get(m, 0))).values
    values, cal, yr = sub[series].values.astype(float), sub["cal"].values, \
        sub["year"].values
    point = rr_from_arrays(values, cal, cdpe)
    year_arr = np.array(years)
    reps = np.empty(B)
    for b in range(B):
        sampled = rng.choice(year_arr, size=len(year_arr), replace=True)
        mask = np.isin(yr, sampled)
        idx = np.concatenate([np.where(yr == y)[0] for y in sampled]) \
            if mask.any() else np.array([], dtype=int)
        reps[b] = rr_from_arrays(values[idx], cal[idx], cdpe[idx])
    finite = reps[np.isfinite(reps)]
    lo = float(np.percentile(finite, 2.5)) if len(finite) >= 100 else None
    hi = float(np.percentile(finite, 97.5)) if len(finite) >= 100 else None
    return {"rr": None if not np.isfinite(point) else float(point),
            "ci_lo": lo, "ci_hi": hi,
            "n_cdpe_months": int(cdpe.sum()),
            "bootstrap_finite": int(len(finite))}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_months()
    cfg_all = load_configs()
    configs = [c for c in cfg_all.columns if "|" in c]  # the 36 Arm A configs
    assert len(configs) == 36, configs
    rng = np.random.default_rng(SEED)
    monthly = df.copy()
    monthly["cdpe_baseline"] = monthly["month"].map(
        lambda m: int(cfg_all.loc[m, BASELINE]) if m in cfg_all.index else 0)
    monthly.drop(columns=["glm_flash_box"]).to_csv(
        OUT / "monthly_series_all.csv", index=False)

    rows, summary = [], {}
    windows = {s: (GLM_YEARS if s == "glm_flash_box" else LONG_YEARS)
               for s in PRIMARY + SECONDARY}
    for series in PRIMARY + SECONDARY:
        years = windows[series]
        per_cfg = {}
        for c in configs:
            n_in_window = int(df[df["year"].isin(years)]["month"].map(
                lambda m: int(cfg_all.loc[m, c]) if m in cfg_all.index else 0
            ).sum())
            thresh = 3 if series == "glm_flash_box" else 10
            included = n_in_window >= thresh
            est = estimate(df, cfg_all[c], series, years, rng) \
                if n_in_window > 0 else {"rr": None, "ci_lo": None,
                                         "ci_hi": None,
                                         "n_cdpe_months": 0,
                                         "bootstrap_finite": 0}
            est.update({"hazard": series, "config": c,
                        "included_in_envelope": bool(included)})
            if series != "glm_flash_box":  # lightning dropped from outputs
                rows.append(est)
            per_cfg[c] = est
        if series == "glm_flash_box":
            continue  # estimated only to preserve the frozen RNG stream
        base = per_cfg[BASELINE]
        env = [e for e in per_cfg.values() if e["included_in_envelope"]
               and e["rr"] is not None]
        if env and base["rr"] is not None:
            side = np.sign(base["rr"] - 1)
            envelope = {
                "n_configs_included": len(env),
                "rr_min": min(e["rr"] for e in env),
                "rr_max": max(e["rr"] for e in env),
                "share_same_side_as_baseline": float(np.mean(
                    [np.sign(e["rr"] - 1) == side for e in env])),
                "share_ci_excludes_1": float(np.mean(
                    [e["ci_lo"] is not None
                     and (e["ci_lo"] > 1 or e["ci_hi"] < 1) for e in env])),
            }
        else:
            envelope = {"n_configs_included": len(env), "rr_min": None,
                        "rr_max": None, "share_same_side_as_baseline": None,
                        "share_ci_excludes_1": None}
        robust = bool(base["ci_lo"] is not None
                      and (base["ci_lo"] > 1 or base["ci_hi"] < 1)
                      and envelope["share_same_side_as_baseline"] is not None
                      and envelope["share_same_side_as_baseline"] >= 0.80)
        summary[series] = {"window_years": [years[0], years[-1]],
                           "baseline_config": BASELINE,
                           "baseline": {k: base[k] for k in
                                        ("rr", "ci_lo", "ci_hi",
                                         "n_cdpe_months")},
                           "envelope": envelope,
                           "gate_G2_robust": robust,
                           "tier": "primary" if series in PRIMARY
                                   else "secondary"}
    eras = {}
    for series in ["tornado_all", "tornado_ef1plus", "tornado_ef2plus",
                   "hail_all", "hail_ge1in"]:
        eras[series] = {}
        for label, yrs in [("1980-1995", list(range(1980, 1996))),
                           ("1996-2023", list(range(1996, 2024)))]:
            e = estimate(df, cfg_all[BASELINE], series, yrs, rng)
            eras[series][label] = {k: e[k] for k in
                                   ("rr", "ci_lo", "ci_hi", "n_cdpe_months")}
    summary["split_era_baseline"] = eras
    pd.DataFrame(rows).to_csv(OUT / "rate_ratios_by_config.csv", index=False)
    (OUT / "rate_ratios_summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False))

    write_verification(summary)
    print(json.dumps({s: summary[s]["baseline"] for s in RETAINED}, indent=1))
    return 0


def write_verification(summary=None) -> dict:
    """Compare the written no-lightning outputs against the with-lightning
    run of record, retained hazards only (the reference by-config CSV
    also carries the dropped GLM rows; they are excluded here)."""
    if summary is None:
        summary = json.loads((OUT / "rate_ratios_summary.json").read_text())
    ref = json.loads((AAS_RES / "rate_ratios_summary.json").read_text())
    ref_cfg = pd.read_csv(AAS_RES / "rate_ratios_by_config.csv")
    my_cfg = pd.read_csv(OUT / "rate_ratios_by_config.csv")
    checks = {}
    max_dev = 0.0
    for s in RETAINED:
        a, b = summary[s], ref[s]
        same = (a["baseline"] == b["baseline"]
                and a["envelope"] == b["envelope"]
                and a["gate_G2_robust"] == b["gate_G2_robust"]
                and a["window_years"] == b["window_years"])
        checks[s] = {"summary_block_identical": bool(same)}
        for k in ("rr", "ci_lo", "ci_hi"):
            va, vb = a["baseline"][k], b["baseline"][k]
            if va is not None and vb is not None:
                max_dev = max(max_dev, abs(va - vb))
        sub_a = my_cfg[my_cfg["hazard"] == s].sort_values("config")
        sub_b = ref_cfg[ref_cfg["hazard"] == s].sort_values("config")
        merged = sub_a.merge(sub_b, on=["hazard", "config"],
                             suffixes=("_new", "_ref"))
        checks[s]["n_config_rows"] = int(len(merged))
        checks[s]["config_rows_identical"] = bool(
            len(merged) == 36
            and merged["included_in_envelope_new"].equals(
                merged["included_in_envelope_ref"])
            and np.allclose(merged["rr_new"].fillna(-999),
                            merged["rr_ref"].fillna(-999), atol=0, rtol=0)
            and np.allclose(merged["ci_lo_new"].fillna(-999),
                            merged["ci_lo_ref"].fillna(-999), atol=0, rtol=0)
            and np.allclose(merged["ci_hi_new"].fillna(-999),
                            merged["ci_hi_ref"].fillna(-999), atol=0, rtol=0))
    checks["split_era_identical"] = bool(
        summary["split_era_baseline"] == ref["split_era_baseline"])
    checks["max_abs_baseline_deviation"] = float(max_dev)
    checks["all_retained_identical"] = bool(
        all(v.get("summary_block_identical") and v.get("config_rows_identical")
            for k, v in checks.items() if isinstance(v, dict))
        and checks["split_era_identical"])
    (OUT / "verification_conditioning.json").write_text(
        json.dumps(checks, indent=1))
    print("verification:", json.dumps(checks, indent=1))
    return checks


if __name__ == "__main__":
    import sys
    if "--verify-only" in sys.argv:
        write_verification()
        raise SystemExit(0)
    raise SystemExit(main())
