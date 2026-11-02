#!/usr/bin/env python3
"""Step 06 - Stratified rate ratios, year bootstrap, configuration envelope.

DESIGN LOCK Sections 3, 5, 6, 7. Estimand per hazard h and configuration c:
RR = sum_m w_m * mean(rate in CDPE months of calendar stratum m)
     / sum_m w_m * mean(rate in non-CDPE months of stratum m),
w_m = share of c's CDPE months falling in stratum m. Uncertainty: bootstrap
over whole calendar years (B = 2000, seed 20261026), percentile intervals.
Outputs: monthly series table, per-configuration CSV, strict-JSON summary
(NaN serialised as null).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
SEED = 20261026
B = 2000
BASELINE = "SPEI-1|thr=1.5|r=4.0"
PRIMARY = ["tornado_all", "hail_ge1in", "heatwave_days_per_cell", "glm_flash_box"]
SECONDARY = ["tornado_ef1plus", "tornado_ef2plus", "hail_all"]
LONG_YEARS = list(range(1980, 2027))  # EXTENDED run: months present run 1980-01..2026-07 (binding endpoint)
GLM_YEARS = list(range(2018, 2027))  # EXTENDED run: GLM frame months present run 2018-03..2025-03 (arm-specific endpoint)


def load_months() -> pd.DataFrame:
    df = pd.read_csv(RES / "hazard_series_storm.csv")
    hw = pd.read_csv(RES / "hazard_series_heatwave.csv")
    df = df.merge(hw[["month", "heatwave_days_per_cell"]], on="month", how="left")
    glm = {}
    for p in sorted((RES / "glm_fetch").glob("*.json")):
        d = json.loads(p.read_text())
        if d["valid"]:
            # DESIGN_LOCK Amendment 2: uniform thinned frame (days of the
            # month congruent to 1 mod 3) applied to every month, including
            # months fetched under the full daily sample
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
    cfg = pd.read_csv(ROOT / "data" / "raw" / "cdpe_monthsets"
                      / "cdpe_monthly_series_armA.csv",
                      parse_dates=["date"])
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
        # rebuild with multiplicity: gather rows per sampled year in order
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
    df = load_months()
    cfg_all = load_configs()
    configs = [c for c in cfg_all.columns if "|" in c]  # the 36 Arm A configs
    assert len(configs) == 27, configs  # nClimGrid run: 27 SPEI configs (no SPI arm); estimator, seed, gates unchanged
    rng = np.random.default_rng(SEED)
    monthly = df.copy()
    monthly["cdpe_baseline"] = monthly["month"].map(
        lambda m: int(cfg_all.loc[m, BASELINE]) if m in cfg_all.index else 0)
    monthly.to_csv(RES / "monthly_series_all.csv", index=False)

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
            rows.append(est)
            per_cfg[c] = est
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
    # split-era descriptive, baseline configuration only
    eras = {}
    for series in ["tornado_all", "tornado_ef1plus", "tornado_ef2plus",
                   "hail_all", "hail_ge1in"]:
        eras[series] = {}
        # EXTENDED run: second era ends at the extended window end
        for label, yrs in [("1980-1995", list(range(1980, 1996))),
                           ("1996-2026", list(range(1996, 2027)))]:
            e = estimate(df, cfg_all[BASELINE], series, yrs, rng)
            eras[series][label] = {k: e[k] for k in
                                   ("rr", "ci_lo", "ci_hi", "n_cdpe_months")}
    summary["split_era_baseline"] = eras
    glm_months = df[df["year"].isin(GLM_YEARS)]
    # Gate G1 is evaluated on the Amendment 1 effective window (from
    # 2018-03): Jan-Feb 2018 contain no data in the open GLM archive for
    # any user, so they are outside the window by the pre-specified rule,
    # not missing from it.
    glm_eff = glm_months[glm_months["month"] >= "2018-03"]
    summary["glm_completeness"] = {
        "months_in_window": int(len(glm_months)),
        "months_valid": int(glm_months["glm_flash_box"].notna().sum()),
        "effective_window_from": "2018-03",
        "months_in_effective_window": int(len(glm_eff)),
        "months_valid_effective": int(glm_eff["glm_flash_box"].notna().sum()),
        "gate_G1_pass": bool(glm_eff["glm_flash_box"].notna().mean() >= 0.98),
    }
    pd.DataFrame(rows).to_csv(RES / "rate_ratios_by_config.csv", index=False)
    (RES / "rate_ratios_summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False))
    print(json.dumps({k: summary[k] for k in PRIMARY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
