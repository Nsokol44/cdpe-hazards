"""Concurrent drought-pluvial event (CDPE) detection.

IMPORTANT: ``detect_cdpe`` implements a *generic, parameterized* definition:
a month is a CDPE month when, within one domain, drought cells (SPEI <= -thr)
and pluvial cells (SPEI >= +thr) BOTH cover at least ``min_area_frac`` of the
valid domain, after discarding spatial clusters smaller than
``min_cluster_cells``. This is a stand-in so the sensitivity machinery can be
tested end to end. To analyse your published CDPE algorithm, write a function
with the same signature and pass it as ``detector=`` to
``sensitivity.run_sensitivity``. Do not report results from the generic
definition as results of your algorithm.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import ndimage

_STRUCT8 = np.ones((3, 3), dtype=int)


def _filter_clusters(mask2d, min_cells):
    if min_cells <= 1 or not mask2d.any():
        return mask2d
    lab, n = ndimage.label(mask2d, structure=_STRUCT8)
    if n == 0:
        return mask2d
    sizes = ndimage.sum(mask2d, lab, index=np.arange(1, n + 1))
    keep = np.concatenate([[False], sizes >= min_cells])
    return keep[lab]


def detect_cdpe(spei, drought_thr=1.0, pluvial_thr=1.0, min_area_frac=0.1,
                min_cluster_cells=1):
    """Return dict with per-month boolean ``cdpe`` and area fractions.

    Months where fewer than half of the valid cells have a finite index
    (e.g. the spin-up months of an accumulation window) are not evaluable
    and are reported as False.
    """
    spei = np.asarray(spei, dtype=float)
    finite = np.isfinite(spei)
    valid = finite.mean(axis=0) > 0.5            # cells with a usable record
    fin = finite & valid[None]
    n_valid_cells = max(1, int(valid.sum()))
    evaluable = fin.sum(axis=(1, 2)) >= 0.5 * n_valid_cells

    with np.errstate(invalid="ignore"):
        dmask = (spei <= -drought_thr) & fin
        pmask = (spei >= pluvial_thr) & fin

    T = spei.shape[0]
    dfrac = np.zeros(T)
    pfrac = np.zeros(T)
    for t in range(T):
        if not evaluable[t]:
            continue
        d = _filter_clusters(dmask[t], min_cluster_cells)
        p = _filter_clusters(pmask[t], min_cluster_cells)
        dfrac[t] = d.sum() / n_valid_cells
        pfrac[t] = p.sum() / n_valid_cells
    cdpe = evaluable & (dfrac >= min_area_frac) & (pfrac >= min_area_frac)
    return {"cdpe": cdpe, "drought_frac": dfrac, "pluvial_frac": pfrac,
            "evaluable": evaluable}


def event_table(cdpe, dates, drought_frac=None, pluvial_frac=None):
    """Collapse a monthly boolean series into events (runs of consecutive months)."""
    cdpe = np.asarray(cdpe, dtype=bool)
    rows = []
    t = 0
    T = len(cdpe)
    while t < T:
        if cdpe[t]:
            s = t
            while t + 1 < T and cdpe[t + 1]:
                t += 1
            e = t
            row = {"start": dates[s], "end": dates[e], "duration_months": e - s + 1}
            if drought_frac is not None:
                row["peak_drought_frac"] = float(np.max(drought_frac[s:e + 1]))
            if pluvial_frac is not None:
                row["peak_pluvial_frac"] = float(np.max(pluvial_frac[s:e + 1]))
            rows.append(row)
        t += 1
    return pd.DataFrame(rows)
