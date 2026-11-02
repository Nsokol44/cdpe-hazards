"""Tie-fix variant of the author's CDPE detector (Phase 2, 2026-11-02).

This module does NOT modify :mod:`cdpe_sens.author_detector` (the frozen
port of Sokol Study 1). It re-implements
``classify_month_author`` with ONE change: pole selection under ties.

Why: the empirical (Gringorten) standardization in
``cdpe_sens.spei`` caps |z| at 2.146 for a 35-year calibration sample,
so ~128 land cells tie at the field minimum and ~128 at the maximum in
every month (see DISTRIBUTION_DIAGNOSIS.md). The frozen detector's
``np.argmin``/``np.argmax`` resolves those ties to the FIRST cell in
row-major order (southernmost, then westernmost), which parks the pole
on the southern coast and collapses the empirical counts under the land
mask. The log-logistic fields have a smaller version of the same issue
at their clipped plateau: the z clip at Phi^-1(1 - 1e-6) = +4.753 /
Phi^-1(1e-6) = -4.753 (and the F = 0 plateau for eval <= gamma) creates
exact-float ties at the extremes.

Tie rule implemented here (everything else is identical to
``classify_month_author`` -- same degree-space buffer, same NA gate,
same majority rule, via the frozen module's own ``buffer_mask_np`` and
``_qualifies`` helpers):

* Collect ALL finite cells whose value is exactly equal (float ==) to
  the field minimum (dry pole) or maximum (wet pole).
* If exactly one such cell exists, select it (identical to the frozen
  detector).
* If more than one exists, choose uniformly at random among the tied
  cells. First-index order is never used to break a tie -- that order
  IS the artifact being fixed.
* Randomness: ``numpy.random.default_rng`` seeded deterministically
  per (pole, month). The seed is the first 8 bytes (little-endian) of
  SHA-256 over the UTF-8 string

      cdpe-tiefix-v1|BASE_SEED=<base_seed>|scenario=<scenario_key>|month=<month_index>|pole=<dry|wet>

  where ``<scenario_key>`` is the canonical scenario key string built
  by :func:`scenario_key_string`. With the default
  ``BASE_SEED = 20261102`` reruns are bit-identical; varying
  BASE_SEED gives the seed-sensitivity ensemble.
"""
from __future__ import annotations

import hashlib

import numpy as np

from .author_detector import (AUTHOR_MAX_NA_FRAC, AUTHOR_MAJORITY_FRAC,
                              AUTHOR_RADIUS_DEG, AUTHOR_THRESHOLD,
                              _qualifies, buffer_mask_np)

BASE_SEED = 20261102


def scenario_key_string(scenario_key):
    """Canonical string form of a scenario key tuple/dict.

    A tuple key is joined with '/' using ``str`` on each element in
    order. A dict key is rendered as 'name=value' pairs sorted by name.
    The Arm B driver uses tuples in FACTORS + radius order:
    (dataset, timescale, dist, cal_period, water_balance, threshold,
    min_area_frac, min_cluster_cells, radius_deg).
    """
    if isinstance(scenario_key, dict):
        return "/".join(f"{k}={scenario_key[k]}" for k in sorted(scenario_key))
    return "/".join(str(x) for x in scenario_key)


def rng_for(base_seed, scenario_key, month_index, pole):
    """Deterministic per-(pole, month) RNG; see module docstring."""
    material = (f"cdpe-tiefix-v1|BASE_SEED={int(base_seed)}"
                f"|scenario={scenario_key_string(scenario_key)}"
                f"|month={int(month_index)}|pole={pole}")
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    seed_int = int.from_bytes(digest[:8], "little")
    return np.random.default_rng(seed_int)


def _tied_pole(field2d, lat, lon, want_min, rng):
    """Return ((lat, lon), extreme_value, n_tied) selecting uniformly
    at random among the finite cells exactly attaining the min/max."""
    finite = np.isfinite(field2d)
    vals = field2d[finite]
    extreme = vals.min() if want_min else vals.max()
    tied = np.argwhere(finite & (field2d == extreme))  # row-major order
    n_tied = int(len(tied))
    if n_tied == 1:
        iy, ix = tied[0]
    else:
        iy, ix = tied[int(rng.integers(n_tied))]
    return (float(lat[iy]), float(lon[ix])), float(extreme), n_tied


def classify_month_tiefix(field2d, lat, lon, threshold=AUTHOR_THRESHOLD,
                          radius_deg=AUTHOR_RADIUS_DEG,
                          majority_frac=AUTHOR_MAJORITY_FRAC,
                          max_na_frac=AUTHOR_MAX_NA_FRAC,
                          scenario_key="unspecified", month_index=0,
                          base_seed=BASE_SEED):
    """``classify_month_author`` with random tie-breaking at the poles.

    Return dict mirrors the frozen detector's, plus ``n_tied_dry`` /
    ``n_tied_wet`` diagnostics (number of finite cells tied at the
    field minimum / maximum that month).
    """
    field2d = np.asarray(field2d, dtype=float)
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    if not np.isfinite(field2d).any():
        return {"is_event": False, "dry_center": (float("nan"), float("nan")),
                "wet_center": (float("nan"), float("nan")),
                "dry_frac": float("nan"), "wet_frac": float("nan"),
                "dry_na_frac": float("nan"), "wet_na_frac": float("nan"),
                "spei_min": float("nan"), "spei_max": float("nan"),
                "n_tied_dry": 0, "n_tied_wet": 0}

    dry_center, spei_min, n_tied_dry = _tied_pole(
        field2d, lat, lon, True,
        rng_for(base_seed, scenario_key, month_index, "dry"))
    wet_center, spei_max, n_tied_wet = _tied_pole(
        field2d, lat, lon, False,
        rng_for(base_seed, scenario_key, month_index, "wet"))

    dry_buf = buffer_mask_np(lat, lon, *dry_center, radius_deg)
    wet_buf = buffer_mask_np(lat, lon, *wet_center, radius_deg)
    dry_ok, dry_frac, dry_na = _qualifies(field2d[dry_buf], "dry",
                                          threshold, majority_frac, max_na_frac)
    wet_ok, wet_frac, wet_na = _qualifies(field2d[wet_buf], "wet",
                                          threshold, majority_frac, max_na_frac)
    return {"is_event": bool(dry_ok and wet_ok),
            "dry_center": dry_center, "wet_center": wet_center,
            "dry_frac": dry_frac, "wet_frac": wet_frac,
            "dry_na_frac": dry_na, "wet_na_frac": wet_na,
            "spei_min": spei_min, "spei_max": spei_max,
            "n_tied_dry": n_tied_dry, "n_tied_wet": n_tied_wet}


def detect_cdpe_tiefix(spei, lat, lon, threshold=AUTHOR_THRESHOLD,
                       radius_deg=AUTHOR_RADIUS_DEG,
                       majority_frac=AUTHOR_MAJORITY_FRAC,
                       max_na_frac=AUTHOR_MAX_NA_FRAC,
                       scenario_key="unspecified", base_seed=BASE_SEED):
    """Tie-fix detector over a (T, Y, X) index field.

    Returns the same dict as ``detect_cdpe_author`` plus per-month
    ``n_tied_dry``/``n_tied_wet`` arrays. ``scenario_key`` identifies
    the scenario for the deterministic per-month seeding (see the
    module docstring); it does not affect any non-tied month.
    """
    spei = np.asarray(spei, dtype=float)
    T = spei.shape[0]
    cdpe = np.zeros(T, dtype=bool)
    evaluable = np.zeros(T, dtype=bool)
    dry_frac = np.full(T, np.nan)
    wet_frac = np.full(T, np.nan)
    dry_center = np.full((T, 2), np.nan)
    wet_center = np.full((T, 2), np.nan)
    spei_min = np.full(T, np.nan)
    spei_max = np.full(T, np.nan)
    n_tied_dry = np.zeros(T, dtype=int)
    n_tied_wet = np.zeros(T, dtype=int)
    for t in range(T):
        r = classify_month_tiefix(spei[t], lat, lon, threshold=threshold,
                                  radius_deg=radius_deg,
                                  majority_frac=majority_frac,
                                  max_na_frac=max_na_frac,
                                  scenario_key=scenario_key, month_index=t,
                                  base_seed=base_seed)
        cdpe[t] = r["is_event"]
        evaluable[t] = np.isfinite(r["spei_min"])
        dry_frac[t] = r["dry_frac"]
        wet_frac[t] = r["wet_frac"]
        dry_center[t] = r["dry_center"]
        wet_center[t] = r["wet_center"]
        spei_min[t] = r["spei_min"]
        spei_max[t] = r["spei_max"]
        n_tied_dry[t] = r["n_tied_dry"]
        n_tied_wet[t] = r["n_tied_wet"]
    return {"cdpe": cdpe, "drought_frac": dry_frac, "pluvial_frac": wet_frac,
            "evaluable": evaluable, "dry_center": dry_center,
            "wet_center": wet_center, "spei_min": spei_min,
            "spei_max": spei_max, "n_tied_dry": n_tied_dry,
            "n_tied_wet": n_tied_wet}
