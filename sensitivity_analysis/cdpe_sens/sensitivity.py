"""Full-factorial sensitivity analysis for CDPE detection.

Factors
-------
Index construction : dataset, timescale, dist, cal_period, water_balance
Event definition   : threshold, min_area_frac, min_cluster_cells

The SPEI field is computed once per index-construction combination and reused
across all event-definition combinations, so the expensive step is not repeated.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .events import detect_cdpe, event_table
from .spei import compute_spei, thornthwaite_pet

FACTORS = ["dataset", "timescale", "dist", "cal_period", "water_balance",
           "threshold", "min_area_frac", "min_cluster_cells"]

DEFAULT_LEVELS = {
    "timescale": [1, 3, 6, 9, 12],
    "dist": ["loglogistic", "empirical"],
    "cal_period": ["full"],
    "water_balance": ["spei", "spi"],
    "threshold": [0.5, 0.8, 1.0, 1.28, 1.5],
    "min_area_frac": [0.05, 0.10, 0.20],
    "min_cluster_cells": [1, 10],
}


@dataclass
class SensitivityResult:
    table: pd.DataFrame
    series: dict                       # key tuple (FACTORS order) -> bool array (T,)
    dates: pd.DatetimeIndex
    levels: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)


def _cal_tuple(label):
    if label in (None, "full"):
        return None
    a, b = str(label).split("-")
    return int(a), int(b)


def check_aligned(datasets):
    """All datasets must share the same monthly time axis and grid shape."""
    items = list(datasets.values())
    d0 = items[0]
    for d in items[1:]:
        if not d.dates.equals(d0.dates):
            raise ValueError(f"{d.name}: time axis differs from {d0.name}; "
                             "restrict to the common period first")
        if d.precip.shape != d0.precip.shape:
            raise ValueError(f"{d.name}: grid shape differs from {d0.name}; "
                             "regrid to a common grid first")


def run_sensitivity(datasets, levels=None, detector=detect_cdpe, verbose=False):
    """Run every factor combination.

    datasets : dict name -> MonthlyDataset (aligned in time and space)
    levels   : dict factor -> list of levels (see DEFAULT_LEVELS)
    detector : callable(spei, drought_thr, pluvial_thr, min_area_frac,
               min_cluster_cells) -> dict with boolean 'cdpe' and optional
               'drought_frac'/'pluvial_frac'
    """
    lv = {**DEFAULT_LEVELS, **(levels or {})}
    check_aligned(datasets)
    dates = next(iter(datasets.values())).dates
    n_years = len(dates) / 12.0
    rows, series, diag = [], {}, {}

    for dname, ds in datasets.items():
        pet = thornthwaite_pet(ds.tmean, ds.lat, ds.dates)
        for ts, dist, cal, wb in itertools.product(
                lv["timescale"], lv["dist"], lv["cal_period"], lv["water_balance"]):
            use_pet = pet if wb == "spei" else None
            spei, dg = compute_spei(ds.precip, use_pet, ds.dates, ts,
                                    cal_period=_cal_tuple(cal), dist=dist,
                                    return_diagnostics=True)
            diag[(dname, ts, dist, cal, wb)] = dg
            for thr, area, clus in itertools.product(
                    lv["threshold"], lv["min_area_frac"], lv["min_cluster_cells"]):
                out = detector(spei, thr, thr, area, clus)
                cd = np.asarray(out["cdpe"], dtype=bool)
                ev = event_table(cd, dates, out.get("drought_frac"), out.get("pluvial_frac"))
                key = (dname, ts, dist, cal, wb, thr, area, clus)
                series[key] = cd
                rows.append({
                    "dataset": dname, "timescale": ts, "dist": dist, "cal_period": cal,
                    "water_balance": wb, "threshold": thr, "min_area_frac": area,
                    "min_cluster_cells": clus,
                    "n_cdpe_months": int(cd.sum()),
                    "n_events": int(len(ev)),
                    "mean_duration": float(ev["duration_months"].mean()) if len(ev) else 0.0,
                    "months_per_year": float(cd.sum() / n_years),
                    "loglogistic_fallback_fraction": dg["loglogistic_fallback_fraction"],
                })
            if verbose:
                print(f"done {dname} ts={ts} dist={dist} cal={cal} wb={wb}")
    lv_out = {"dataset": list(datasets.keys()), **lv}
    return SensitivityResult(pd.DataFrame(rows), series, dates, lv_out, diag)


# --------------------------------------------------------------------------
# Variance decomposition (balanced full factorial)
# --------------------------------------------------------------------------
def _closed_share(df, y, subset):
    if not subset:
        return 0.0
    gm = df.groupby(list(subset))[y].transform("mean")
    tot = df[y].var(ddof=0)
    return float(gm.var(ddof=0) / tot) if tot > 0 else 0.0


def variance_decomposition(table, metric="n_cdpe_months", factors=None):
    """Main-effect and two-way-interaction shares of Var(metric).

    Requires a balanced full factorial. 'higher_order' is the remainder.
    Factors with a single level are dropped (they carry no variance).
    """
    factors = factors or FACTORS
    factors = [f for f in factors if table[f].nunique() > 1]
    expected = int(np.prod([table[f].nunique() for f in factors]))
    if len(table) != expected:
        raise ValueError("table is not a balanced full factorial over the varying factors")
    rows = []
    mains = {}
    for f in factors:
        mains[f] = _closed_share(table, metric, [f])
        rows.append({"term": f, "order": 1, "share": mains[f]})
    inter_total = 0.0
    for a, b in itertools.combinations(factors, 2):
        v = _closed_share(table, metric, [a, b]) - mains[a] - mains[b]
        v = max(v, 0.0)
        inter_total += v
        rows.append({"term": f"{a} x {b}", "order": 2, "share": v})
    higher = max(0.0, 1.0 - sum(mains.values()) - inter_total)
    rows.append({"term": "higher_order", "order": 3, "share": higher})
    out = pd.DataFrame(rows).sort_values("share", ascending=False).reset_index(drop=True)
    return out


# --------------------------------------------------------------------------
# Agreement metrics
# --------------------------------------------------------------------------
def jaccard(a, b):
    a = np.asarray(a, dtype=bool)
    b = np.asarray(b, dtype=bool)
    union = (a | b).sum()
    return float((a & b).sum() / union) if union else float("nan")


def annual_counts(cdpe, dates):
    s = pd.Series(np.asarray(cdpe, dtype=int), index=dates)
    return s.groupby(s.index.year).sum()


def interannual_correlation(cdpe_a, cdpe_b, dates):
    a = annual_counts(cdpe_a, dates)
    b = annual_counts(cdpe_b, dates)
    if a.nunique() < 2 or b.nunique() < 2:
        return float("nan")
    return float(spearmanr(a.values, b.values).correlation)


def oat_agreement(result, baseline):
    """One-at-a-time agreement with a baseline scenario.

    baseline : dict factor -> level for all FACTORS (levels must exist in result).
    Returns one row per (factor, alternative level).
    """
    base_key = tuple(baseline[f] for f in FACTORS)
    base = result.series[base_key]
    rows = []
    for i, f in enumerate(FACTORS):
        for lev in result.levels[f]:
            if lev == baseline[f]:
                continue
            key = list(base_key)
            key[i] = lev
            alt = result.series[tuple(key)]
            rows.append({
                "factor": f, "level": lev,
                "baseline_months": int(base.sum()), "alt_months": int(alt.sum()),
                "jaccard": jaccard(base, alt),
                "interannual_spearman": interannual_correlation(base, alt, result.dates),
            })
    return pd.DataFrame(rows)


def dataset_agreement(result, baseline):
    """Pairwise agreement between datasets under otherwise identical settings."""
    names = result.levels["dataset"]
    rows = []
    for a, b in itertools.combinations(names, 2):
        ka = tuple(a if f == "dataset" else baseline[f] for f in FACTORS)
        kb = tuple(b if f == "dataset" else baseline[f] for f in FACTORS)
        sa, sb = result.series[ka], result.series[kb]
        rows.append({"dataset_a": a, "dataset_b": b,
                     "months_a": int(sa.sum()), "months_b": int(sb.sum()),
                     "jaccard": jaccard(sa, sb),
                     "interannual_spearman": interannual_correlation(sa, sb, result.dates)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Sampling uncertainty
# --------------------------------------------------------------------------
def bootstrap_rate_ci(cdpe, dates, B=2000, seed=0, alpha=0.05):
    """Year-block bootstrap CI for CDPE months per year.

    Resamples whole calendar years with replacement and recomputes the mean
    annual count. This quantifies sampling uncertainty of the *detected*
    series only; it does not refit the SPEI distribution on each resample,
    so it is a lower bound on total sampling uncertainty.
    """
    counts = annual_counts(cdpe, dates).values.astype(float)
    rng = np.random.default_rng(seed)
    n = len(counts)
    idx = rng.integers(0, n, size=(B, n))
    boot = counts[idx].mean(axis=1)
    return {"mean": float(counts.mean()),
            "lo": float(np.quantile(boot, alpha / 2)),
            "hi": float(np.quantile(boot, 1 - alpha / 2)),
            "n_years": int(n)}
